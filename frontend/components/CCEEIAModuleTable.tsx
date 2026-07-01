'use client';

import { Fragment } from 'react';
import { ModuleRow, PlacementRow } from '@/types/reports';
import { cn } from '@/lib/utils';

interface Props {
  data: ModuleRow[];
  placementData?: PlacementRow[];
  sortMode?: 'Ranking' | 'Diff' | '';
  sortModule?: number | null;
  /** When set, Overall totals only include modules up to this number (e.g. 4, 6, 8). */
  totalsUpToModule?: number | null;
}

function computeTotalsUpToModule(row: ModuleRow, upToModule: number | null) {
  const modules =
    upToModule != null
      ? row.modules.filter((m) => m.module_no <= upToModule)
      : row.modules;

  const enteredCc = modules
    .map((m) => m.ccee_score)
    .filter((s): s is number => s !== null && s !== undefined);
  const enteredIa = modules
    .map((m) => m.ia_score)
    .filter((s): s is number => s !== null && s !== undefined);

  const ccee_total = enteredCc.reduce((sum, s) => sum + s, 0);
  const ia_total = enteredIa.reduce((sum, s) => sum + s, 0);
  const grand_total = ccee_total + ia_total;
  const grand_max = modules.reduce((sum, m) => sum + (m.module_max ?? 0), 0);
  const percentage = grand_max > 0 ? Math.round((grand_total / grand_max) * 10000) / 100 : 0;
  const cc_fail = enteredCc.some((s) => s < 16);
  const ia_fail = enteredIa.some((s) => s < 24);
  const pass_fail = cc_fail || ia_fail ? ('Fail' as const) : ('Pass' as const);

  return { ccee_total, ia_total, grand_total, grand_max, percentage, pass_fail };
}

function fmt(n: number | null | undefined) {
  if (n === null || n === undefined) return '—';
  return n.toFixed(1);
}

function gradeFromPct(pct: number | null | undefined) {
  if (pct === null || pct === undefined) return null;
  if (pct >= 85) return 'A+';
  if (pct >= 70) return 'A';
  if (pct >= 60) return 'B';
  if (pct >= 50) return 'C';
  if (pct >= 40) return 'D';
  return 'F';
}

function GradeCell({ grade }: { grade?: string | null }) {
  if (!grade) {
    return <td className="px-2 py-1.5 text-center text-xs text-muted-foreground/40">—</td>;
  }

  const tone =
    grade === 'A+' || grade === 'A'
      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25'
      : grade === 'B' || grade === 'C'
      ? 'bg-amber-500/15 text-amber-300 border-amber-500/25'
      : grade === 'D'
      ? 'bg-slate-500/15 text-slate-300 border-slate-500/25'
      : 'bg-slate-500/20 text-slate-200 border-slate-500/30';

  return (
    <td className="px-2 py-1.5 text-center text-xs font-bold">
      <span className={cn('inline-flex min-w-10 justify-center rounded-full border px-2 py-0.5', tone)}>
        {grade}
      </span>
    </td>
  );
}

function ScoreCell({
  score,
  threshold,
  max,
}: {
  score: number | null;
  threshold: number; // score below this → red
  max?: number | null;
}) {
  if (score === null)
    return <td className="px-2 py-1.5 text-center text-xs text-muted-foreground/40">—</td>;

  const fail = score < threshold;
  return (
    <td
      className={cn(
        'px-2 py-1.5 text-center text-sm font-mono',
        fail ? 'bg-red-500/20 text-red-600 dark:text-red-400 font-bold' : 'text-foreground dark:text-slate-100 font-medium'
      )}
    >
      {fmt(score)}
      {max != null && (
        <span className="text-slate-400/60 font-normal">/{max}</span>
      )}
    </td>
  );
}

export function CCEEIAModuleTable({ 
  data, 
  placementData = [],
  sortMode = '',
  sortModule = null,
  totalsUpToModule = null,
}: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        No data. Select a batch above to load the report.
      </div>
    );
  }

  // Determine the module set from all rows so partial batches still render.
  const moduleNos = Array.from(
    new Set(data.flatMap((row) => row.modules.map((module) => module.module_no)))
  ).sort((a, b) => a - b);

  return (
    <div className="w-full overflow-x-auto rounded-2xl border border-white/10 bg-card/50 backdrop-blur-sm">
      <table className="w-full text-sm border-collapse">
        {/* ── Header ───────────────────────────────────────────────── */}
        <thead>
          {/* Row 1 – Module group labels */}
          <tr className="border-b border-white/10 bg-card/80">
            <th
              rowSpan={2}
              className="sticky left-0 z-20 bg-card/90 backdrop-blur-sm px-4 py-3 text-left font-semibold text-xs text-muted-foreground whitespace-nowrap border-r border-white/10"
            >
              PRN
            </th>
            <th
              rowSpan={2}
              className="sticky left-[90px] z-20 bg-card/90 backdrop-blur-sm px-4 py-3 text-left font-semibold text-xs text-muted-foreground whitespace-nowrap border-r border-white/10 min-w-[160px]"
            >
              Student Name
            </th>

            {moduleNos.map((seq) => {
              const sample = data.find((row) => row.modules.some((m) => m.module_no === seq))?.modules.find((m) => m.module_no === seq);
              const maxLabel =
                sample?.module_max != null ? `(max ${sample.module_max})` : '';
              return (
                <th
                  key={seq}
                  colSpan={3}
                  className="px-3 py-2 text-center text-xs font-bold text-muted-foreground border-l border-white/5"
                >
                  Module {seq}
                  <div className="text-[10px] font-normal text-muted-foreground/40 mt-0.5">
                    {maxLabel}
                  </div>
                </th>
              );
            })}

            <th rowSpan={2} className="px-3 py-3 text-center text-sm font-bold text-foreground whitespace-nowrap border-l border-white/10">
              GAC Grade
            </th>
            <th rowSpan={2} className="px-3 py-3 text-center text-sm font-bold text-foreground whitespace-nowrap border-l border-white/10">
              Project Grade
            </th>
            <th rowSpan={2} className="px-3 py-3 text-center text-sm font-bold text-foreground whitespace-nowrap border-l border-white/10">
              Final Grade
            </th>

            {/* Overall */}
            <th colSpan={6} className="px-3 py-2 text-center text-xs font-bold uppercase tracking-wide text-muted-foreground border-l border-white/10">
              Overall
            </th>

            {/* Rankings */}
            <th colSpan={3} className="px-3 py-2 text-center text-xs font-bold uppercase tracking-wide text-muted-foreground border-l border-white/10">
              Rankings
            </th>
          </tr>

          {/* Row 2 – Sub-column labels */}
          <tr className="border-b border-white/10 bg-card/60 text-[11px] text-muted-foreground/90 font-bold uppercase">
            {moduleNos.map((seq) => (
              <Fragment key={`head-sub-${seq}`}>
                <th className="px-2 py-1 text-center border-l border-white/5 text-blue-400">CCEE</th>
                <th className="px-2 py-1 text-center text-violet-400">IA</th>
                <th className="px-2 py-1 text-center text-slate-300">Total</th>
              </Fragment>
            ))}
            <th className="px-2 py-1 text-center border-l border-white/10 text-blue-400">CCEE</th>
            <th className="px-2 py-1 text-center text-violet-400">IA</th>
            <th className="px-2 py-1 text-center text-slate-100">Total</th>
            <th className="px-2 py-1 text-center text-slate-400">Max</th>
            <th className="px-2 py-1 text-center text-emerald-400">%</th>
            <th className="px-2 py-1 text-center text-foreground">P/F</th>
            <th className="px-2 py-1 text-center border-l border-white/10 text-cyan-400/70">M4</th>
            <th className="px-2 py-1 text-center text-cyan-400/70">M6</th>
            <th className="px-2 py-1 text-center text-cyan-400/70">M8</th>
          </tr>
        </thead>

        {/* ── Body ─────────────────────────────────────────────────── */}
        <tbody>
          {(
            sortMode === 'Ranking' && sortModule
              ? [...data].sort((a, b) => {
                  const key = `rank_after_m${sortModule}`;
                  const av = (a as any)[key] ?? Number.MAX_SAFE_INTEGER;
                  const bv = (b as any)[key] ?? Number.MAX_SAFE_INTEGER;
                  return av - bv;
                })
              : data
          ).map((row, i) => (
            <tr
              key={row.prn}
              className={cn(
                'border-b border-white/5 hover:bg-white/5 transition-colors',
                i % 2 === 0 ? '' : 'bg-white/[0.02]'
              )}
            >
              {/* Sticky PRN */}
              <td className="sticky left-0 z-10 bg-card/90 backdrop-blur-sm px-4 py-2 font-mono text-sm text-muted-foreground whitespace-nowrap border-r border-white/10">
                {row.prn}
              </td>
              {/* Sticky Name */}
              <td className="sticky left-[90px] z-10 bg-card/90 backdrop-blur-sm px-4 py-2 font-bold text-sm text-foreground whitespace-nowrap border-r border-white/10 max-w-[200px] truncate">
                {row.student_name}
              </td>

              {/* Per-module scores */}
              {moduleNos.map((seq) => {
                const mod = row.modules.find((m) => m.module_no === seq);
                return (
                  <Fragment key={`${row.prn}-${seq}-group`}>
                    <ScoreCell
                      score={mod?.ccee_score ?? null}
                      threshold={16}
                    />
                    <ScoreCell
                      score={mod?.ia_score ?? null}
                      threshold={24}
                    />
                    <td
                      className="px-2 py-1.5 text-center text-sm font-mono text-foreground/80 dark:text-slate-200 font-medium"
                    >
                      {mod?.module_total != null ? fmt(mod.module_total) : '—'}
                    </td>
                  </Fragment>
                );
              })}

              {(() => {
                const placementRow = placementData.find((item) => item.prn === row.prn);
                const totals = computeTotalsUpToModule(row, totalsUpToModule);
                const finalGrade = gradeFromPct(totals.percentage);
                return (
                  <>
                    <GradeCell grade={gradeFromPct(placementRow?.gac_pct)} />
                    <GradeCell grade={gradeFromPct(placementRow?.prj_pct)} />
                    <GradeCell grade={finalGrade} />
                    <td className="px-2 py-1.5 text-center text-sm font-mono text-blue-600 dark:text-blue-400 font-bold border-l border-white/10">
                      {fmt(totals.ccee_total)}
                    </td>
                    <td className="px-2 py-1.5 text-center text-sm font-mono text-violet-600 dark:text-violet-400 font-bold">
                      {fmt(totals.ia_total)}
                    </td>
                    <td className="px-2 py-1.5 text-center text-sm font-mono font-black text-foreground dark:text-slate-100">
                      {fmt(totals.grand_total)}
                    </td>
                    <td className="px-2 py-1.5 text-center text-sm font-mono text-muted-foreground">
                      {totals.grand_max}
                    </td>
                    <td
                      className={cn(
                        'px-2 py-1.5 text-center text-sm font-mono font-black',
                        totals.percentage >= 65
                          ? 'text-emerald-600 dark:text-emerald-400'
                          : totals.percentage >= 50
                          ? 'text-yellow-600 dark:text-yellow-400'
                          : 'text-red-600 dark:text-red-400'
                      )}
                    >
                      {fmt(totals.percentage)}%
                    </td>
                    <td className="px-2 py-1.5 text-center">
                      <span
                        className={cn(
                          'text-sm font-black uppercase tracking-tighter',
                          totals.pass_fail === 'Pass'
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : 'text-red-600 dark:text-red-400'
                        )}
                      >
                        {totals.pass_fail}
                      </span>
                    </td>
                  </>
                );
              })()}
              {/* Rankings M4, M6, M8 */}
              <td className="px-2 py-1.5 text-center font-bold border-l border-white/10 text-cyan-600 dark:text-cyan-400">
                {row.rank_after_m4 ?? '—'}
              </td>
              <td className="px-2 py-1.5 text-center font-bold text-cyan-600 dark:text-cyan-400">
                {row.rank_after_m6 ?? '—'}
              </td>
              <td className="px-2 py-1.5 text-center font-bold text-cyan-600 dark:text-cyan-400">
                {row.rank_after_m8 ?? '—'}
              </td>
            </tr>
          ))}
        </tbody>

        {/* ── Footer ───────────────────────────────────────────────── */}
        <tfoot>
          <tr className="border-t border-white/10 bg-card/80 text-xs text-muted-foreground">
            <td colSpan={2} className="sticky left-0 bg-card/90 px-4 py-2 border-r border-white/10 font-semibold">
              {data.length} students &nbsp;|&nbsp; Pass:{' '}
              {data.filter((r) => r.totals.pass_fail === 'Pass').length} &nbsp; Fail:{' '}
              {data.filter((r) => r.totals.pass_fail === 'Fail').length}
            </td>
            <td
              colSpan={moduleNos.length * 3 + 12}
              className="px-4 py-2 text-muted-foreground/40 text-[10px]"
            >
              Red cells = score below threshold (CCEE &lt; 16 or IA &lt; 24)
              {totalsUpToModule != null && (
                <span className="ml-2 text-cyan-400/80">
                  · Overall totals through Module {totalsUpToModule}
                </span>
              )}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
