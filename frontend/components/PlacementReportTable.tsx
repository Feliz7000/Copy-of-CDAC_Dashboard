'use client';

import { PlacementRow, ReportSchema, CATEGORY_META } from '@/types/reports';
import React from 'react';
import { cn } from '@/lib/utils';

// ── Types ──────────────────────────────────────────────────────────────────

interface Props {
  data: PlacementRow[];
  schema?: ReportSchema;
  sortMode?: 'Ranking' | 'Diff' | '';
  sortModule?: number | null;
}

// ── Category columns displayed in order ───────────────────────────────────
const CATEGORIES = ['cc', 'ia', 'ap', 'sx', 'ps', 'gr', 'ta', 'na', 'in', 'as', 'pq', 'gac', 'prj'] as const;
type CategoryKey = (typeof CATEGORIES)[number];

// ── Helpers ────────────────────────────────────────────────────────────────

function fmt(n: number | null | undefined, decimals = 1) {
  if (n === null || n === undefined) return '—';
  return n.toFixed(decimals);
}

function CutoffBadge({ met }: { met: boolean | null }) {
  if (met === null)
    return <span className="text-xs text-muted-foreground/60 italic">N/A</span>;
  if (met)
    return (
      <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-400">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
        Pass
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 text-xs font-semibold text-red-400">
      <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
      Fail
    </span>
  );
}

function PlacementBadge({ status }: { status: PlacementRow['placement_status'] }) {
  const cfg: Record<string, string> = {
    'Placement ready': 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
    'Can Improve': 'bg-yellow-500/15 text-yellow-600 dark:text-yellow-400 border-yellow-500/30',
    'Not Placement ready': 'bg-slate-500/15 text-slate-600 dark:text-slate-400 border-slate-500/30',
  };
  const tone = cfg[status as string] || 'bg-slate-500/15 text-slate-600 border-slate-500/30';
  return (
    <span className={cn('inline-block rounded-full border px-2.5 py-0.5 text-xs font-bold', tone)}>
      {status || 'Unknown'}
    </span>
  );
}

function PctCell({
  pct,
  cutoff,
  entered,
}: {
  pct: number;
  cutoff: boolean | null;
  entered: number;
}) {
  const bg =
    cutoff === true
      ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
      : cutoff === false
      ? 'bg-red-500/10 text-red-600 dark:text-red-400'
      : 'text-slate-600 dark:text-slate-400';
  const text = entered === 0 ? '—' : `${fmt(pct)}%`;
  return (
    <td className={cn('px-2 py-1.5 text-center text-sm font-mono font-bold whitespace-nowrap', bg)}>
      {text}
    </td>
  );
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

function GradeChip({ grade }: { grade?: string | null }) {
  if (!grade) return <span className="text-muted-foreground/60">—</span>;
  const tone =
    grade === 'A+' || grade === 'A'
      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/25'
      : grade === 'B' || grade === 'C'
      ? 'bg-amber-500/15 text-amber-300 border-amber-500/25'
      : grade === 'D'
      ? 'bg-slate-500/15 text-slate-300 border-slate-500/25'
      : 'bg-slate-500/20 text-slate-200 border-slate-500/30';

  return (
    <span className={cn('inline-flex min-w-8 justify-center rounded-full border px-2 py-0.5 text-xs font-bold', tone)}>
      {grade}
    </span>
  );
}

// ── Component ──────────────────────────────────────────────────────────────

export function PlacementReportTable({ 
  data, 
  schema, 
  sortMode = '', 
  sortModule = null 
}: Props) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        No data. Select a batch above to load the report.
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto rounded-2xl border border-white/10 bg-card/50 backdrop-blur-sm">
      <table className="w-full text-sm border-collapse">
        {/* ── Header ───────────────────────────────────────────────── */}
        <thead>
          {/* Row 1 – Category group labels */}
          <tr className="border-b border-white/10 bg-card/80">
            <th
              rowSpan={2}
              className="sticky left-0 z-20 bg-card/90 backdrop-blur-sm px-4 py-3 text-left font-bold text-sm text-foreground whitespace-nowrap border-r border-white/10"
            >
              PRN
            </th>
            <th
              rowSpan={2}
              className="sticky left-[90px] z-20 bg-card/90 backdrop-blur-sm px-4 py-3 text-left font-bold text-sm text-foreground whitespace-nowrap border-r border-white/10 min-w-[160px]"
            >
              Student Name
            </th>
            {CATEGORIES.map((cat) => (
              <th
                key={cat}
                colSpan={(schema?.[cat.toUpperCase()]?.length || 0) + 3}
                className="px-3 py-2 text-center text-xs font-bold uppercase tracking-wider text-muted-foreground border-l border-white/5"
              >
                {CATEGORY_META[cat].label}
                <div className="text-[11px] font-medium text-muted-foreground/70 normal-case tracking-normal mt-0.5">
                  {CATEGORY_META[cat].cutoffLabel}
                </div>
              </th>
            ))}
            <th colSpan={3} className="px-3 py-2 text-center text-xs font-bold uppercase tracking-wide text-muted-foreground border-l border-white/5">
              Grand Total
            </th>
            <th colSpan={3} className="px-3 py-2 text-center text-xs font-bold uppercase tracking-wide text-muted-foreground border-l border-white/5">
              Rankings
            </th>
            <th rowSpan={2} className="px-3 py-3 text-center text-sm font-bold text-foreground whitespace-nowrap border-l border-white/10">
              Pass/Fail
            </th>
            <th rowSpan={2} className="px-3 py-3 text-center text-sm font-bold text-foreground whitespace-nowrap border-l border-white/10">
              Status
            </th>
          </tr>
          {/* Row 2 – Sub-column labels */}
          <tr className="border-b border-white/10 bg-card/60 text-[10px] text-muted-foreground/70">
            {CATEGORIES.map((cat) => (
              <React.Fragment key={`${cat}-sc`}>
                {(schema?.[cat.toUpperCase()] || []).map((col) => (
                  <th
                    key={`${cat}-${col.slot}`}
                    className="px-2 py-1 text-center font-normal border-l border-white/5 truncate max-w-[80px]"
                    title={col.name}
                  >
                    {col.name}
                  </th>
                ))}
                <th className="px-2 py-1 text-center border-l border-white/10 text-emerald-400/50">Total</th>
                <th className="px-2 py-1 text-center text-emerald-400/50">Max</th>
                <th className="px-2 py-1 text-center text-emerald-400/50">%</th>
              </React.Fragment>
            ))}
            <th className="px-2 py-1 text-center border-l border-white/5">Scored</th>
            <th className="px-2 py-1 text-center">Max</th>
            <th className="px-2 py-1 text-center">%</th>
            <th className="px-2 py-1 text-center border-l border-white/5 text-cyan-400/70">M4</th>
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
                'border-b border-white/5 transition-colors hover:bg-white/5',
                i % 2 === 0 ? 'bg-transparent' : 'bg-white/[0.02]'
              )}
            >
              {/* Sticky PRN */}
              <td className="sticky left-0 z-10 bg-card/90 backdrop-blur-sm px-4 py-2 font-mono text-sm text-muted-foreground font-medium whitespace-nowrap border-r border-white/10">
                {row.prn}
              </td>
              {/* Sticky Name */}
              <td className="sticky left-[90px] z-10 bg-card/90 backdrop-blur-sm px-4 py-2 font-bold text-sm text-foreground whitespace-nowrap border-r border-white/10 max-w-[200px] truncate">
                {row.student_full_name}
              </td>

              {/* Category cells */}
              {CATEGORIES.map((cat) => {
                const catUpper = cat.toUpperCase();
                const catSchema = schema?.[catUpper] || [];

                const scored = row[`${cat}_scored` as keyof PlacementRow] as number;
                const max = row[`${cat}_max` as keyof PlacementRow] as number;
                const pct = row[`${cat}_pct` as keyof PlacementRow] as number;
                const cutoff = row[`${cat}_cutoff_met` as keyof PlacementRow] as boolean | null;
                const entered = row[`${cat}_subtests_entered` as keyof PlacementRow] as number;
                return (
                  <React.Fragment key={`${cat}-s`}>
                    {/* Dynamic individual test cells */}
                    {catSchema.map((col) => {
                      const keyName = `${cat}_${col.slot}`;
                      const val = row[keyName];
                      return (
                        <td
                          key={keyName}
                          className="px-2 py-1.5 text-center text-sm font-mono border-l border-white/5 text-foreground/80 dark:text-slate-300"
                        >
                          {fmt(val)}
                        </td>
                      );
                    })}

                    {/* Totals */}
                    <>
                      <td className="px-2 py-1.5 text-center text-sm font-mono border-l border-white/10 text-emerald-600 dark:text-emerald-400 font-bold">
                        {entered === 0 ? '—' : fmt(scored)}
                      </td>
                      <td className="px-2 py-1.5 text-center text-sm font-mono text-emerald-600/70 dark:text-emerald-400/70">
                        {max || '—'}
                      </td>
                      <PctCell pct={pct} cutoff={cutoff} entered={entered} />
                    </>
                  </React.Fragment>
                );
              })}

              {/* Grand total */}
              <td className="px-2 py-1.5 text-center text-sm font-mono font-bold border-l border-white/5 text-foreground dark:text-slate-100">
                {fmt(row.grand_total_scored)}
              </td>
              <td className="px-2 py-1.5 text-center text-sm font-mono text-muted-foreground">
                {row.grand_total_max}
              </td>
              <td className={cn(
                'px-2 py-1.5 text-center text-sm font-mono font-black',
                row.grand_total_pct >= 80 ? 'text-emerald-600 dark:text-emerald-400' : row.grand_total_pct >= 65 ? 'text-yellow-600 dark:text-yellow-400' : 'text-slate-600 dark:text-slate-400'
              )}>
                {fmt(row.grand_total_pct)}%
              </td>

              {/* Rankings M4, M6, M8 */}
              <td className="px-2 py-1.5 text-center font-bold border-l border-white/10 text-cyan-600 dark:text-cyan-400">
                {(row as any).rank_after_m4 ?? '—'}
              </td>
              <td className="px-2 py-1.5 text-center font-bold text-cyan-600 dark:text-cyan-400">
                {(row as any).rank_after_m6 ?? '—'}
              </td>
              <td className="px-2 py-1.5 text-center font-bold text-cyan-600 dark:text-cyan-400">
                {(row as any).rank_after_m8 ?? '—'}
              </td>

              {/* Pass/Fail */}
              <td className="px-3 py-1.5 text-center border-l border-white/10">
                <span className={cn(
                  'text-sm font-black uppercase tracking-tighter',
                  row.pass_fail === 'Pass' ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'
                )}>
                  {row.pass_fail}
                </span>
              </td>

              {/* Placement status */}
              <td className="px-3 py-1.5 text-center border-l border-white/10">
                <PlacementBadge status={row.placement_status} />
              </td>
            </tr>
          ))}
        </tbody>

        {/* ── Summary Footer ─────────────────────────────────────── */}
        <tfoot>
          <tr className="border-t border-white/10 bg-card/80 text-xs font-semibold text-muted-foreground">
            <td colSpan={2} className="sticky left-0 bg-card/90 px-4 py-2 border-r border-white/10">
              Summary ({data.length} students)
            </td>
            {CATEGORIES.map((cat) => {
              const catSchemaLength = schema?.[cat.toUpperCase()]?.length || 0;
              return (
                <React.Fragment key={`f-${cat}-s`}>
                  {Array.from({ length: catSchemaLength }).map((_, idx) => (
                    <td key={`f-${cat}-dyn-${idx}`} className="px-2 py-2 text-center border-l border-white/5 text-muted-foreground/40">—</td>
                  ))}
                  <td className="px-2 py-2 text-center border-l border-white/10 text-muted-foreground/40">—</td>
                  <td className="px-2 py-2 text-center text-muted-foreground/40">—</td>
                  <td className="px-2 py-2 text-center text-muted-foreground/40">—</td>
                </React.Fragment>
              );
            })}
            <td colSpan={3} className="px-2 py-2 text-center border-l border-white/5">
              Placement ready: {data.filter(r => r.placement_status === 'Placement ready').length} &nbsp;|&nbsp;
              Can Improve: {data.filter(r => r.placement_status === 'Can Improve').length} &nbsp;|&nbsp;
              Not Placement Ready: {data.filter(r => r.placement_status === 'Not Placement ready').length}
            </td>
            <td colSpan={5} className="border-l border-white/10" />
          </tr>
        </tfoot>
      </table>
    </div>
  );
}
