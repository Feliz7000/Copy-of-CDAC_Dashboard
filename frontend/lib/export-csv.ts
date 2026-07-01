import { ModuleRow, PlacementRow, ReportSchema } from '@/types/reports';

const PLACEMENT_CATEGORIES = [
  'cc',
  'ia',
  'ap',
  'sx',
  'ps',
  'gr',
  'ta',
  'na',
  'in',
  'as',
  'pq',
  'gac',
  'prj',
] as const;

function escapeCsv(value: unknown): string {
  if (value === null || value === undefined) return '';
  const text = String(value);
  if (/[",\n\r]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function toCsvLine(values: unknown[]): string {
  return values.map(escapeCsv).join(',');
}

export function downloadTextFile(filename: string, content: string, mimeType = 'text/csv;charset=utf-8;') {
  const blob = new Blob([content], { type: mimeType });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

export function buildPlacementReportCsv(rows: PlacementRow[], schema: ReportSchema = {}): string {
  const headers: string[] = [
    'prn',
    'student_full_name',
    'batch_name',
    'course_code',
    'centre_code',
  ];

  for (const cat of PLACEMENT_CATEGORIES) {
    const catUpper = cat.toUpperCase();
    for (const col of schema[catUpper] ?? []) {
      headers.push(`${cat}_${col.slot}`);
    }
    headers.push(`${cat}_scored`, `${cat}_max`, `${cat}_pct`);
  }

  headers.push(
    'grand_total_scored',
    'grand_total_max',
    'grand_total_pct',
    'rank_after_m4',
    'rank_after_m6',
    'rank_after_m8',
    'pass_fail',
    'placement_status',
  );

  const lines = [toCsvLine(headers)];

  for (const row of rows) {
    const values: unknown[] = [
      row.prn,
      row.student_full_name,
      row.batch_name,
      row.course_code,
      row.centre_code,
    ];

    for (const cat of PLACEMENT_CATEGORIES) {
      const catUpper = cat.toUpperCase();
      for (const col of schema[catUpper] ?? []) {
        values.push(row[`${cat}_${col.slot}`]);
      }
      values.push(row[`${cat}_scored`], row[`${cat}_max`], row[`${cat}_pct`]);
    }

    values.push(
      row.grand_total_scored,
      row.grand_total_max,
      row.grand_total_pct,
      row.rank_after_m4 ?? '',
      row.rank_after_m6 ?? '',
      row.rank_after_m8 ?? '',
      row.pass_fail,
      row.placement_status,
    );

    lines.push(toCsvLine(values));
  }

  return lines.join('\n');
}

export function buildModuleReportCsv(rows: ModuleRow[]): string {
  const moduleNumbers = Array.from(
    new Set(rows.flatMap((row) => row.modules.map((module) => module.module_no))),
  ).sort((a, b) => a - b);

  const headers = ['prn', 'student_name'];
  for (const moduleNo of moduleNumbers) {
    headers.push(`m${moduleNo}_ccee`, `m${moduleNo}_ia`, `m${moduleNo}_total`);
  }
  headers.push(
    'total_ccee',
    'total_ia',
    'grand_total',
    'grand_max',
    'percentage',
    'rank_after_m4',
    'rank_after_m6',
    'rank_after_m8',
    'pass_fail',
  );

  const lines = [toCsvLine(headers)];

  for (const row of rows) {
    const values: unknown[] = [row.prn, row.student_name];

    for (const moduleNo of moduleNumbers) {
      const module = row.modules.find((item) => item.module_no === moduleNo);
      values.push(
        module?.ccee_score ?? '',
        module?.ia_score ?? '',
        module?.module_total ?? '',
      );
    }

    values.push(
      row.totals.ccee_total,
      row.totals.ia_total,
      row.totals.grand_total,
      row.totals.grand_max,
      row.totals.percentage,
      row.rank_after_m4 ?? '',
      row.rank_after_m6 ?? '',
      row.rank_after_m8 ?? '',
      row.totals.pass_fail,
    );

    lines.push(toCsvLine(values));
  }

  return lines.join('\n');
}
