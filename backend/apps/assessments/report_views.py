"""
Placement Report API Views
Reads from v_placement_report and v_ccee_ia_modules PostgreSQL views.
"""
import csv
import io
import re
import logging
from pathlib import Path
from decimal import Decimal
import requests

logger = logging.getLogger(__name__)

from django.conf import settings
from django.db import connection, DatabaseError
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework.views import APIView

from config.permissions import IsStaffOnly
from apps.assessments.models import (
    SystemConfig, TestMapping, ScoreAS, ScorePQ
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(val):
    """Convert Decimal / None to float / None for JSON serialisation."""
    if val is None:
        return None
    return float(val)


def _grade_from_pct(pct: float | None):
    if pct is None:
        return None
    if pct >= 85:
        return 'A+'
    if pct >= 70:
        return 'A'
    if pct >= 60:
        return 'B'
    if pct >= 50:
        return 'C'
    if pct >= 40:
        return 'D'
    return 'F'


def _normalize_placement_status(raw_status: str | None) -> str:
    """Map SQL/rule labels to UI placement status labels."""
    if not raw_status:
        return 'Unknown'
    key = str(raw_status).strip().lower()
    mapping = {
        'eligible': 'Placement ready',
        'placement ready': 'Placement ready',
        'hold': 'Can Improve',
        'can improve': 'Can Improve',
        'not eligible': 'Not Placement ready',
        'not placement ready': 'Not Placement ready',
    }
    return mapping.get(key, raw_status if raw_status in (
        'Placement ready', 'Can Improve', 'Not Placement ready'
    ) else 'Unknown')


def _apply_rule_based_placement_status(row: dict) -> None:
    row['placement_status'] = _normalize_placement_status(
        row.get('sql_placement_status') or row.get('placement_status')
    )
    row['placement_status_source'] = 'rules'


def _cursor_to_dicts(cursor):
    """Convert cursor fetchall() result into list of dicts."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _build_sql_filter(base_sql: str, params: list, batch_name, course_code, centre_code):
    sql = base_sql + " WHERE batch_name = %s"
    params.append(batch_name)
    if course_code:
        sql += " AND course_code = %s"
        params.append(course_code)
    if centre_code:
        sql += " AND centre_code = %s"
        params.append(centre_code)
    sql += " ORDER BY prn"
    return sql


def _safe_filename_segment(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", value or "") or "batch"


def _placement_report_fieldnames(schema):
    base_headers = ['prn', 'student_full_name', 'centre_code', 'course_code', 'batch_name']

    cat_order = ['CC', 'IA', 'AP', 'SX', 'PS', 'GR', 'TA', 'NA', 'IN', 'AS', 'PQ', 'GAC', 'PRJ']
    dynamic_headers = []
    for cat in cat_order:
        cat_lower = cat.lower()
        if cat in schema:
            for slot in schema[cat]:
                dynamic_headers.append(f"{cat_lower}_{slot['slot']}")
        dynamic_headers.extend([f'{cat_lower}_scored', f'{cat_lower}_max', f'{cat_lower}_pct'])

    end_headers = [
        'grand_total_scored', 'grand_total_max', 'grand_total_pct',
        'rank_after_m4', 'rank_after_m6', 'rank_after_m8',
        'pass_fail', 'placement_status',
    ]

    return base_headers + dynamic_headers + end_headers


def _buffered_csv_response(fieldnames, rows, filename):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    response = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _write_csv_snapshot(filename: str, fieldnames: list[str], rows: list[dict]) -> Path:
    raw_dir = Path(settings.BASE_DIR) / 'data' / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / filename

    with open(out_path, 'w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    return out_path


# ---------------------------------------------------------------------------
# Placement Report
# ---------------------------------------------------------------------------

class PlacementReportView(APIView):
    """
    GET /api/assessments/reports/placement/

    Query params:
        batch_name   (optional – defaults to active batch)
        course_code  (optional filter)
        centre_code  (optional filter)
        format       json (default) | csv
    """
    permission_classes = [IsStaffOnly]
    def get(self, request):
        # 1. Resolve batch
        batch_name = request.query_params.get('batch_name')
        if not batch_name:
            try:
                batch_name = SystemConfig.get_active_batch()
            except Exception:
                return Response({'error': 'No active batch configured. Pass batch_name param.'}, status=400)

        course_code = request.query_params.get('course_code') or None
        centre_code = request.query_params.get('centre_code') or None
        fmt = request.query_params.get('format', 'json')

        # 2. Query the view
        params = []
        sql = _build_sql_filter(
            "SELECT * FROM v_placement_report",
            params, batch_name, course_code, centre_code
        )

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                raw_data = _cursor_to_dicts(cursor)
        except Exception as e:
            return Response({'error': f'Database error: {e}'}, status=500)

        # 3. Post-process Decimals + compute AS/PQ cutoffs in Python
        data = self._post_process(raw_data, batch_name, course_code)

        # 4. Format response
        if fmt == 'csv':
            exported_name = f"placement_{_safe_filename_segment(batch_name)}.csv"
            try:
                self._save_csv_snapshot(exported_name, data['schema'], data['results'])
            except Exception as exc:
                logger.warning('Placement CSV snapshot skipped: %s', exc)
            return self._csv_response(data['schema'], data['results'], exported_name)

        return Response(data)

    def _save_csv_snapshot(self, filename, schema, data):
        fieldnames = _placement_report_fieldnames(schema)
        _write_csv_snapshot(filename, fieldnames, data)

    # ------------------------------------------------------------------
    def _post_process(self, data, batch_name, course_code):
        """Convert Decimals → float, recompute AS/PQ cutoffs, inject raw subtest scores."""
        if not data:
            return {'schema': {}, 'results': []}

        prns = [row['prn'] for row in data]

        # Fetch ALL active mappings for this batch to build the schema
        all_mappings = TestMapping.objects.filter(batch_name=batch_name, is_active=True).order_by('sequence')
        schema = {}
        for tm in all_mappings:
            if tm.category_code_id not in schema:
                schema[tm.category_code_id] = []
            schema[tm.category_code_id].append({
                'slot': tm.column_slot,
                'name': tm.logical_name,
                'max': float(tm.max_marks),
                'seq': tm.sequence
            })

        # Pre-fetch all Score models for these PRNs
        from apps.assessments.models import CATEGORY_SCORE_MODEL_MAP
        score_records = {}
        for cat_code, ModelClass in CATEGORY_SCORE_MODEL_MAP.items():
            try:
                records = ModelClass.objects.filter(prn_id__in=prns)
                score_records[cat_code] = {r.prn_id: r for r in records}
            except DatabaseError:
                score_records[cat_code] = {}

        # Category configuration for dynamic recomputation
        category_order = ['CC', 'IA', 'AP', 'SX', 'PS', 'GR', 'TA', 'NA', 'IN', 'AS', 'PQ', 'GAC', 'PRJ']
        scaled_max_by_category = {
            'CC': 320.0,
            'IA': 480.0,
            'AP': 200.0,
            'SX': 100.0,
            'PS': 100.0,
            'GR': 100.0,
            'TA': 100.0,
            'NA': 100.0,
            'IN': 50.0,
            'AS': 300.0,
            'PQ': 300.0,
            'GAC': 100.0,
            'PRJ': 100.0,
        }

        def evaluate_cutoff(cat_code: str, entered_values: list[tuple[float, float]], entered_count: int, pct: float):
            if entered_count == 0:
                return None

            per_test_rules = {
                'CC': 0.40,
                'IA': 0.40,
                'AP': 0.80,
                'SX': 0.50,
                'TA': 0.40,
                'NA': 0.40,
                'IN': 0.80,
                'AS': 0.80,
                'PQ': 0.80,
            }
            min_pct_rules = {
                'CC': 65,
                'IA': 65,
                'AP': 80,
                'SX': 50,
                'PS': 50,
                'GR': 50,
                'TA': 40,
                'NA': 40,
                'GAC': 40,
                'PRJ': 40,
            }
            count_requirements = {
                'AS': 25,
                'PQ': 30,
            }

            if cat_code in count_requirements and entered_count < count_requirements[cat_code]:
                return None

            min_ratio = per_test_rules.get(cat_code)
            if min_ratio is not None:
                if any(score < (slot_max * min_ratio) for score, slot_max in entered_values):
                    return False

            min_pct = min_pct_rules.get(cat_code)
            if min_pct is None:
                return True
            return pct >= min_pct

        result = []
        for row in data:
            prn = row['prn']
            row['sql_placement_status'] = row.get('placement_status')

            # Float conversion
            for key, val in row.items():
                if isinstance(val, Decimal):
                    row[key] = float(val)

            # ── Inject all individual raw scores ───────────────────────
            for cat_code, records_dict in score_records.items():
                cat_rec = records_dict.get(prn)
                cat_schema = schema.get(cat_code, [])
                for slot_info in cat_schema:
                    slot = slot_info['slot']
                    key_name = f"{cat_code.lower()}_{slot}"
                    if cat_rec and hasattr(cat_rec, slot):
                        val = getattr(cat_rec, slot)
                        row[key_name] = float(val) if val is not None else None
                    else:
                        row[key_name] = None

            # ── Recompute category totals from entered marks only ─────
            grand_scored = 0.0
            grand_max = 0.0
            for cat_code in category_order:
                cat_lower = cat_code.lower()
                cat_schema = schema.get(cat_code, [])

                if cat_code == 'GAC':
                    manual_part = 0.0
                    if cat_schema:
                        first_slot = cat_schema[0]['slot']
                        first_value = row.get(f'{cat_lower}_{first_slot}')
                        if first_value is not None:
                            manual_part = float(first_value)

                    # GAC components:
                    # test_02 from SX aggregate, test_03 from AP aggregate,
                    # test_04 from IN test_03, test_05 from IN test_04.
                    sx_component = None
                    ap_component = None
                    in_t03_component = None
                    in_t04_component = None

                    if (row.get('sx_subtests_entered') or 0) > 0:
                        sx_pct = float(row.get('sx_pct') or 0.0)
                        sx_raw = (sx_pct / 100.0) * 100.0
                        sx_component = round((sx_raw / 320.0) * 60.0, 2)

                    if (row.get('ap_subtests_entered') or 0) > 0:
                        ap_pct = float(row.get('ap_pct') or 0.0)
                        ap_raw = (ap_pct / 100.0) * 200.0
                        ap_component = round((ap_raw / 320.0) * 60.0, 2)

                    in_t03 = row.get('in_test_03')
                    if in_t03 is not None:
                        in_t03_component = round((float(in_t03) / 320.0) * 60.0, 2)

                    in_t04 = row.get('in_test_04')
                    if in_t04 is not None:
                        in_t04_component = round((float(in_t04) / 320.0) * 60.0, 2)

                    derived_components: list[float | None] = [
                        sx_component,
                        ap_component,
                        in_t03_component,
                        in_t04_component,
                    ]

                    derived_scaled = round(sum(v for v in derived_components if v is not None), 2)
                    cat_scored = round(min(manual_part, 40.0) + derived_scaled, 2)
                    cat_max = 100.0
                    cat_pct = round((cat_scored / cat_max) * 100, 2) if cat_max else 0.0
                    cat_entered = 1 if (manual_part or derived_scaled) else 0

                    row[f'{cat_lower}_subtests_entered'] = cat_entered
                    row[f'{cat_lower}_scored'] = cat_scored
                    row[f'{cat_lower}_max'] = cat_max
                    row[f'{cat_lower}_pct'] = cat_pct
                    row[f'{cat_lower}_cutoff_met'] = (cat_pct >= 40) if cat_entered else None
                    row[f'{cat_lower}_grade'] = _grade_from_pct(cat_pct)
                    row[f'{cat_lower}_manual_scored'] = round(min(manual_part, 40.0), 2)
                    row[f'{cat_lower}_derived_scaled'] = derived_scaled

                    if cat_schema:
                        gmap = {slot_info['slot']: value for slot_info, value in zip(cat_schema, [round(min(manual_part, 40.0), 2), *derived_components])}
                        for slot_info in cat_schema:
                            row[f'{cat_lower}_{slot_info["slot"]}'] = gmap.get(slot_info['slot'])

                    grand_scored += cat_scored
                    grand_max += cat_max
                    continue

                entered_values: list[tuple[float, float]] = []
                raw_scored = 0.0
                raw_max = 0.0

                for slot_info in cat_schema:
                    slot = slot_info['slot']
                    value = row.get(f'{cat_lower}_{slot}')
                    if value is None:
                        continue

                    score = float(value)
                    slot_max = float(slot_info['max'])
                    entered_values.append((score, slot_max))
                    raw_scored += score
                    raw_max += slot_max

                entered_count = len(entered_values)
                total_count = len(cat_schema)
                full_scaled_max = scaled_max_by_category.get(
                    cat_code,
                    sum(float(slot['max']) for slot in cat_schema),
                )
                count_factor = (entered_count / total_count) if total_count else 0.0
                cat_max = round(full_scaled_max * count_factor, 2)
                cat_scored = round((raw_scored / raw_max) * cat_max, 2) if raw_max else 0.0
                cat_pct = round((cat_scored / cat_max) * 100, 2) if cat_max else 0.0

                row[f'{cat_lower}_subtests_entered'] = entered_count
                row[f'{cat_lower}_scored'] = cat_scored
                row[f'{cat_lower}_max'] = cat_max
                row[f'{cat_lower}_pct'] = cat_pct
                row[f'{cat_lower}_cutoff_met'] = evaluate_cutoff(cat_code, entered_values, entered_count, cat_pct)
                row[f'{cat_lower}_grade'] = _grade_from_pct(cat_pct)

                grand_scored += cat_scored
                grand_max += cat_max

            row['grand_total_scored'] = round(grand_scored, 2)
            row['grand_total_max'] = round(grand_max, 2)
            row['grand_total_pct'] = round((grand_scored / grand_max) * 100, 2) if grand_max else 0.0

            result.append(row)

        # Default: rule-based placement status (SQL view + Python cutoffs)
        for row in result:
            _apply_rule_based_placement_status(row)

        # Override with ML predictions when the service is available
        try:
            if result:
                ml_payload = {'rows': result}
                ml_urls = [
                    'http://ml_service:8001/ml/predict-placement/',
                    'http://127.0.0.1:8001/ml/predict-placement/',
                    'http://localhost:8001/ml/predict-placement/',
                ]

                response_data = None
                last_error = None
                for url in ml_urls:
                    try:
                        response = requests.post(url, json=ml_payload, timeout=60)
                        response.raise_for_status()
                        response_data = response.json()
                        break
                    except Exception as exc:
                        last_error = exc

                if response_data is not None:
                    predicted_labels = response_data.get('predictions', [])
                    for i, label in enumerate(predicted_labels):
                        if i < len(result):
                            result[i]['predicted_placement_status'] = label
                            result[i]['placement_status'] = label
                            result[i]['placement_status_source'] = 'model'
                else:
                    logger.warning("ML service unavailable, using rule-based placement status: %s", last_error)
        except Exception as e:
            logger.error("Failed to get placement status from ML, using rules: %s", e)

        # --- Compute rankings after modules 4, 6, 8 -----------------
        module_points = [4, 6, 8]

        def _partial_scaled_for_modules(row, cat_code, upto_module):
            cat_schema = schema.get(cat_code, [])
            if not cat_schema:
                return 0.0

            # slots that belong to modules <= upto_module
            slots = [s for s in cat_schema if s.get('seq') and s['seq'] <= upto_module]
            if not slots:
                return 0.0

            partial_raw_scored = 0.0
            partial_raw_max = 0.0
            for s in slots:
                key = f"{cat_code.lower()}_{s['slot']}"
                val = row.get(key)
                if val is None:
                    continue
                partial_raw_scored += float(val)
                partial_raw_max += float(s['max'])

            total_count = len(cat_schema)
            partial_count = len(slots)
            full_scaled_max = scaled_max_by_category.get(cat_code, sum(float(s['max']) for s in cat_schema))
            partial_max = (full_scaled_max * (partial_count / total_count)) if total_count else 0.0

            if partial_raw_max:
                return (partial_raw_scored / partial_raw_max) * partial_max
            return 0.0

        for m in module_points:
            # collect scores
            scores = []
            for row in result:
                prn = row['prn']
                cc_part = _partial_scaled_for_modules(row, 'CC', m)
                ia_part = _partial_scaled_for_modules(row, 'IA', m)
                other_parts = 0.0
                for cat in category_order:
                    if cat in ('CC', 'IA'):
                        continue
                    other_parts += float(row.get(f"{cat.lower()}_scored") or 0.0)

                total_at_m = cc_part + ia_part + other_parts
                scores.append((prn, total_at_m))

            # sort desc and assign ranks (1 = highest)
            scores.sort(key=lambda x: x[1], reverse=True)
            ranks = {}
            prev_score = None
            prev_rank = 0
            for idx, (prn, score) in enumerate(scores, start=1):
                if prev_score is None or score != prev_score:
                    rank = idx
                    prev_score = score
                    prev_rank = rank
                else:
                    rank = prev_rank
                ranks[prn] = rank

            # attach ranks to rows
            key_name = f'rank_after_m{m}'
            for row in result:
                row[key_name] = ranks.get(row['prn'])

        return {'schema': schema, 'results': result}

    # ------------------------------------------------------------------
    def _csv_response(self, schema, data, filename='placement_report.csv'):
        fieldnames = _placement_report_fieldnames(schema)
        return _buffered_csv_response(fieldnames, data, filename)


# ---------------------------------------------------------------------------
# CCEE + IA Module Report
# ---------------------------------------------------------------------------

class CCEEIAModuleReportView(APIView):
    """
    GET /api/assessments/reports/ccee-ia-modules/

    Query params:
        batch_name   (optional – defaults to active batch)
        course_code  (optional filter)
        format       json (default) | csv
    """
    permission_classes = [IsStaffOnly]

    def get(self, request):
        batch_name = request.query_params.get('batch_name')
        if not batch_name:
            try:
                batch_name = SystemConfig.get_active_batch()
            except Exception:
                return Response({'error': 'No active batch configured.'}, status=400)

        course_code = request.query_params.get('course_code') or None
        fmt = request.query_params.get('format', 'json')

        # 1. Get test_mapping for CC and IA — slot → {sequence, logical_name, max}
        cc_mapping = {
            tm.column_slot: {
                'sequence': tm.sequence,
                'logical_name': tm.logical_name,
                'max': float(tm.max_marks),
            }
            for tm in TestMapping.objects.filter(
                batch_name=batch_name, category_code='CC', is_active=True
            )
        }
        ia_mapping = {
            tm.column_slot: {
                'sequence': tm.sequence,
                'logical_name': tm.logical_name,
                'max': float(tm.max_marks),
            }
            for tm in TestMapping.objects.filter(
                batch_name=batch_name, category_code='IA', is_active=True
            )
        }

        all_sequences = sorted(set(
            v['sequence']
            for v in list(cc_mapping.values()) + list(ia_mapping.values())
        ))

        # sequence → column_slot
        cc_seq_to_slot = {v['sequence']: slot for slot, v in cc_mapping.items()}
        ia_seq_to_slot = {v['sequence']: slot for slot, v in ia_mapping.items()}

        # 2. Query the view
        params = []
        sql = "SELECT * FROM v_ccee_ia_modules WHERE batch_name = %s"
        params.append(batch_name)
        if course_code:
            sql += " AND course_code = %s"
            params.append(course_code)
        sql += " ORDER BY prn"

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = _cursor_to_dicts(cursor)
        except Exception as e:
            return Response({'error': f'Database error: {e}'}, status=500)

        # 3. Assemble module structure
        result = []
        for row in rows:
            modules = []
            for seq in all_sequences:
                cc_slot = cc_seq_to_slot.get(seq)
                ia_slot = ia_seq_to_slot.get(seq)

                # Column names in the view are cc_t01, ia_t01, etc.
                # TestMapping column_slot is 'test_01'. We replace 'test_' with 't'.
                cc_col = f"cc_{cc_slot.replace('test_', 't')}" if cc_slot else None
                ia_col = f"ia_{ia_slot.replace('test_', 't')}" if ia_slot else None

                cc_score_raw = row.get(cc_col) if cc_col else None
                ia_score_raw = row.get(ia_col) if ia_col else None

                cc_score = _safe_float(cc_score_raw)
                ia_score = _safe_float(ia_score_raw)

                cc_max = cc_mapping[cc_slot]['max'] if cc_slot else None
                ia_max = ia_mapping[ia_slot]['max'] if ia_slot else None

                module_total = _safe_float(row.get(f'module_{seq:02d}_total'))
                if module_total is None and (cc_score is not None or ia_score is not None):
                    module_total = (cc_score or 0.0) + (ia_score or 0.0)

                module_max = _safe_float(row.get(f'module_{seq:02d}_max'))
                if module_max is None and (cc_max is not None or ia_max is not None):
                    module_max = (cc_max or 0.0) + (ia_max or 0.0)

                modules.append({
                    'module_no': seq,
                    'ccee_score': cc_score,
                    'ccee_max': cc_max,
                    'ia_score': ia_score,
                    'ia_max': ia_max,
                    'module_total': module_total,
                    'module_max': module_max,
                })

            # Totals
            entered_cc = [m['ccee_score'] for m in modules if m['ccee_score'] is not None]
            entered_ia = [m['ia_score'] for m in modules if m['ia_score'] is not None]
            cc_total = sum(entered_cc)
            ia_total = sum(entered_ia)
            grand = cc_total + ia_total
            grand_max = sum(m['module_max'] for m in modules if m['module_max'] is not None)

            pass_fail = row.get('pass_fail')
            if not pass_fail:
                cc_fail = any(s < 16 for s in entered_cc)
                ia_fail = any(s < 24 for s in entered_ia)
                pass_fail = 'Fail' if (cc_fail or ia_fail) else 'Pass'

            result.append({
                'prn': row['prn'],
                'student_name': row['student_full_name'],
                'modules': modules,
                'totals': {
                    'ccee_total': cc_total,
                    'ia_total': ia_total,
                    'grand_total': grand,
                    'grand_max': grand_max,
                    'percentage': round(grand / grand_max * 100, 2) if grand_max else 0.0,
                    'pass_fail': pass_fail,
                },
                'rank_after_m4': row.get('rank_after_m4'),
                'rank_after_m6': row.get('rank_after_m6'),
                'rank_after_m8': row.get('rank_after_m8'),
                'view_pass_fail': row.get('pass_fail'),
            })

        if fmt == 'csv':
            exported_name = f"ccee_ia_modules_{_safe_filename_segment(batch_name)}.csv"
            try:
                self._save_csv_snapshot(exported_name, result, all_sequences)
            except Exception as exc:
                logger.warning('CCEE/IA CSV snapshot skipped: %s', exc)
            return self._csv_response(result, all_sequences, exported_name)

        return Response(result)

    def _save_csv_snapshot(self, filename, data, sequences):
        headers = ['PRN', 'Student Name']
        for seq in sequences:
            headers += [f'M{seq} CCEE', f'M{seq} IA', f'M{seq} Total']
        headers += [
            'Total CCEE', 'Total IA', 'Grand Total', 'Grand Max',
            'Percentage', 'Rank M4', 'Rank M6', 'Rank M8', 'Pass/Fail'
        ]

        rows = []
        for row in data:
            flat = [row['prn'], row['student_name']]
            for seq in sequences:
                mod = next((m for m in row['modules'] if m['module_no'] == seq), {})
                flat += [
                    mod.get('ccee_score', ''),
                    mod.get('ia_score', ''),
                    mod.get('module_total', ''),
                ]
            t = row['totals']
            flat += [
                t['ccee_total'], t['ia_total'],
                t['grand_total'], t['grand_max'],
                t['percentage'],
                row.get('rank_after_m4') or '',
                row.get('rank_after_m6') or '',
                row.get('rank_after_m8') or '',
                t['pass_fail'],
            ]
            rows.append(dict(zip(headers, flat)))

        _write_csv_snapshot(filename, headers, rows)

    def _csv_response(self, data, sequences, filename='ccee_ia_modules.csv'):
        """Flatten module structure into CSV rows."""
        headers = ['PRN', 'Student Name']
        for seq in sequences:
            headers += [f'M{seq} CCEE', f'M{seq} IA', f'M{seq} Total']
        headers += [
            'Total CCEE', 'Total IA', 'Grand Total', 'Grand Max',
            'Percentage', 'Rank M4', 'Rank M6', 'Rank M8', 'Pass/Fail'
        ]

        rows = []
        for row in data:
            flat = [row['prn'], row['student_name']]
            for seq in sequences:
                mod = next((m for m in row['modules'] if m['module_no'] == seq), {})
                flat += [
                    mod.get('ccee_score', ''),
                    mod.get('ia_score', ''),
                    mod.get('module_total', ''),
                ]
            t = row['totals']
            flat += [
                t['ccee_total'], t['ia_total'],
                t['grand_total'], t['grand_max'],
                t['percentage'],
                row.get('rank_after_m4') or '',
                row.get('rank_after_m6') or '',
                row.get('rank_after_m8') or '',
                t['pass_fail'],
            ]
            rows.append(flat)

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        writer.writerows(rows)
        response = HttpResponse(buf.getvalue(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
