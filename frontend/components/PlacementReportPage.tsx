'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PlacementReportTable } from '@/components/PlacementReportTable';
import { CCEEIAModuleTable } from '@/components/CCEEIAModuleTable';
import {
  getLookups,
  getPlacementReport,
  getCCEEIAModuleReport,
} from '@/lib/api';
import {
  buildModuleReportCsv,
  buildPlacementReportCsv,
  downloadTextFile,
} from '@/lib/export-csv';
import { PlacementRow, ModuleRow, ReportSchema, PlacementReportResponse } from '@/types/reports';
import { Download, Loader2, RefreshCw, BarChart3, Layers } from 'lucide-react';
import { cn } from '@/lib/utils';

// ── Stat card ──────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className={cn('rounded-2xl border p-4 bg-card/50 backdrop-blur-sm', color)}>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs text-muted-foreground mt-1">{label}</div>
    </div>
  );
}

// ── Main shared page ───────────────────────────────────────────────────────

export default function PlacementReportPage() {
  const [batches, setBatches] = useState<{ batch_name: string }[]>([]);
  const [courses, setCourses] = useState<{ course_code: string; course_name: string }[]>([]);

  const [batchName, setBatchName] = useState('');
  const [courseCode, setCourseCode] = useState('');

  const [placementData, setPlacementData] = useState<PlacementRow[]>([]);
  const [placementSchema, setPlacementSchema] = useState<ReportSchema>({});
  const [moduleData, setModuleData] = useState<ModuleRow[]>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('placement');
  const [lastFetched, setLastFetched] = useState<Date | null>(null);
  const [rankingMode, setRankingMode] = useState<'Ranking' | 'Diff' | ''>('');
  const [rankingModule, setRankingModule] = useState<'4' | '6' | '8'>('4');
  const [criteriaFilter, setCriteriaFilter] = useState<string>('all');

  const filteredPlacementData = useMemo(() => {
    return placementData.filter((row) => {
      if (criteriaFilter === 'all') return true;
      if (criteriaFilter === 'Placement ready') return row.placement_status === 'Placement ready';
      if (criteriaFilter === 'Can Improve') return row.placement_status === 'Can Improve';
      if (criteriaFilter === 'Not Placement ready') return row.placement_status === 'Not Placement ready';
      if (criteriaFilter === 'fail') return row.pass_fail === 'Fail';
      return row[`${criteriaFilter}_cutoff_met` as keyof PlacementRow] === false;
    });
  }, [placementData, criteriaFilter]);

  // Load lookups on mount
  useEffect(() => {
    getLookups()
      .then((data) => {
        const bs = data.batches ?? [];
        setBatches(bs);
        setCourses(data.courses ?? []);
        // Pre-select the most recent batch (parse Mon/yy)
        if (bs.length > 0) {
          const monthMap: Record<string, number> = {
            Jan: 1,
            Feb: 2,
            Mar: 3,
            Apr: 4,
            May: 5,
            Jun: 6,
            Jul: 7,
            Aug: 8,
            Sep: 9,
            Oct: 10,
            Nov: 11,
            Dec: 12,
          };
          const parse = (s: string) => {
            const parts = s.split('/');
            if (parts.length !== 2) return { y: 0, m: 0 };
            const mon = parts[0].trim();
            const yy = parseInt(parts[1], 10);
            const year = yy < 100 ? 2000 + yy : yy;
            return { y: year, m: monthMap[mon] ?? 0 };
          };
          const sorted = [...bs].sort((a, b) => {
            const pa = parse(a.batch_name);
            const pb = parse(b.batch_name);
            if (pa.y !== pb.y) return pb.y - pa.y;
            return pb.m - pa.m;
          });
          setBatchName(sorted[0].batch_name);
        }
      })
      .catch(() => setError('Failed to load batch/course options.'));
  }, []);

  const fetchData = useCallback(async () => {
    if (!batchName) return;
    setIsLoading(true);
    setError(null);
    try {
      const [p, m] = await Promise.all([
        getPlacementReport(batchName, courseCode || undefined) as Promise<PlacementReportResponse>,
        getCCEEIAModuleReport(batchName, courseCode || undefined),
      ]);
      const sortedPlacement = (p.results || []).sort((a, b) => 
        String(a.prn || '').localeCompare(String(b.prn || ''), undefined, { numeric: true })
      );
      const sortedModules = m.sort((a: any, b: any) => 
        String(a.prn || '').localeCompare(String(b.prn || ''), undefined, { numeric: true })
      );
      
      setPlacementData(sortedPlacement);
      setPlacementSchema(p.schema || {});
      setModuleData(sortedModules);
      setLastFetched(new Date());
    } catch (e: any) {
      setError(e?.response?.data?.error ?? 'Failed to fetch report data.');
    } finally {
      setIsLoading(false);
    }
  }, [batchName, courseCode]);

  // Auto-fetch when batch changes
  useEffect(() => {
    if (batchName) fetchData();
  }, [batchName, courseCode, fetchData]);

  // ── Stats derived from data ──────────────────────────────────────────────
  const eligible = placementData.filter((r) => r.placement_status === 'Placement ready').length;
  const hold = placementData.filter((r) => r.placement_status === 'Can Improve').length;
  const notEligible = placementData.filter((r) => r.placement_status === 'Not Placement ready').length;
  const passed = moduleData.filter((r) => r.totals.pass_fail === 'Pass').length;
  const total = placementData.length;

  const exportRowCount = activeTab === 'placement' ? filteredPlacementData.length : moduleData.length;

  const handleDownload = () => {
    if (!batchName || exportRowCount === 0) return;
    try {
      const safeBatch = batchName.replace(/\//g, '');
      if (activeTab === 'placement') {
        const csv = buildPlacementReportCsv(filteredPlacementData, placementSchema);
        downloadTextFile(`placement_${safeBatch}.csv`, csv);
      } else {
        const csv = buildModuleReportCsv(moduleData);
        downloadTextFile(`ccee_ia_modules_${safeBatch}.csv`, csv);
      }
    } catch {
      setError('Failed to export CSV.');
    }
  };

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="flex flex-col gap-6 w-full p-6">
      {/* ── Page Header ────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <BarChart3 className="h-6 w-6 text-emerald-400" />
            Placement Report
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Student eligibility across all assessment categories
            {lastFetched && (
              <span className="ml-2 text-muted-foreground/50 text-xs">
                · last updated {lastFetched.toLocaleTimeString()}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2 mt-3 sm:mt-0">
          <button
            onClick={fetchData}
            disabled={!batchName || isLoading}
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 bg-card/50 text-sm hover:bg-white/5 disabled:opacity-40 transition"
          >
            <RefreshCw size={15} className={isLoading ? 'animate-spin' : ''} />
            Refresh
          </button>
          <button
            onClick={handleDownload}
            disabled={!batchName || isLoading || exportRowCount === 0}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-emerald-600 text-white text-sm font-semibold hover:bg-emerald-500 disabled:opacity-40 transition"
          >
            <Download size={15} />
            Export CSV
          </button>
        </div>
      </div>

      {/* ── Filters ────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-3 p-4 rounded-2xl border border-white/10 bg-card/30 backdrop-blur-sm">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground font-medium">Batch</label>
          <select
            value={batchName}
            onChange={(e) => setBatchName(e.target.value)}
            className="bg-background border border-white/10 rounded-lg px-3 py-1.5 text-sm min-w-[140px] focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="">Select Batch…</option>
            {batches.map((b) => (
              <option key={b.batch_name} value={b.batch_name}>
                {b.batch_name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground font-medium">Course</label>
          <select
            value={courseCode}
            onChange={(e) => setCourseCode(e.target.value)}
            className="bg-background border border-white/10 rounded-lg px-3 py-1.5 text-sm min-w-[160px] focus:outline-none focus:ring-1 focus:ring-emerald-500"
          >
            <option value="">All Courses</option>
            {courses.map((c) => (
              <option key={c.course_code} value={c.course_code}>
                {c.course_name}
              </option>
            ))}
          </select>
        </div>

        {activeTab === 'placement' && (
          <div className="flex flex-col gap-1">
            <label className="text-xs text-muted-foreground font-medium">Placement Status</label>
            <select
              value={criteriaFilter}
              onChange={(e) => setCriteriaFilter(e.target.value)}
              className="bg-background border border-white/10 rounded-lg px-3 py-1.5 text-sm min-w-[200px] focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              <option value="all">All Students</option>
              <option value="Placement ready">Placement Ready</option>
              <option value="Can Improve">Can Improve</option>
              <option value="Not Placement ready">Not Placement Ready</option>
              <option value="fail">Failed Overall Assessment</option>
              <option value="cc">Failed CCEE</option>
              <option value="ia">Failed IA/Module</option>
              <option value="ap">Failed Aptitude</option>
              <option value="sx">Failed Speak X</option>
              <option value="ps">Failed Personality</option>
              <option value="gr">Failed Grooming</option>
              <option value="ta">Failed Tech Act.</option>
              <option value="na">Failed Non-Tech Act.</option>
              <option value="in">Failed Interview</option>
              <option value="as">Failed Assignments</option>
              <option value="pq">Failed Practice Quiz</option>
              <option value="gac">Failed GAC Grade</option>
              <option value="prj">Failed Project Grade</option>
            </select>
          </div>
        )}
      </div>

      {/* ── Error ──────────────────────────────────────────────────────── */}
      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* ── Summary Stats ──────────────────────────────────────────────── */}
      {total > 0 && !isLoading && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard label="Total Students" value={total} color="border-white/10" />
          <StatCard label="Placement ready" value={eligible} color="border-emerald-500/20 text-emerald-400" />
          <StatCard label="Can Improve" value={hold} color="border-yellow-500/20 text-yellow-400" />
          <StatCard label="Not Placement Ready" value={notEligible} color="border-slate-500/20 text-slate-300" />
        </div>
      )}

      {/* ── Tabs ───────────────────────────────────────────────────────── */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-card/30 border border-white/10 rounded-xl p-1 gap-1">
          <TabsTrigger
            value="placement"
            className="flex items-center gap-2 data-[state=active]:bg-emerald-500/20 data-[state=active]:text-emerald-400 rounded-lg text-sm font-medium"
          >
            <BarChart3 size={14} />
            All Subtests & Placement
          </TabsTrigger>
          <TabsTrigger
            value="modules"
            className="flex items-center gap-2 data-[state=active]:bg-violet-500/20 data-[state=active]:text-violet-400 rounded-lg text-sm font-medium"
          >
            <Layers size={14} />
            CCEE + IA Modules
          </TabsTrigger>
        </TabsList>

        <TabsContent value="placement" className="mt-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-24 text-muted-foreground gap-3">
              <Loader2 className="animate-spin" size={24} />
              <span>Loading placement report…</span>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <label className="text-sm text-muted-foreground">Mode</label>
                <select
                  value={rankingMode}
                  onChange={(e) => setRankingMode(e.target.value as any)}
                  className="bg-background border border-white/10 rounded-lg px-3 py-1.5 text-sm min-w-[140px]"
                >
                  <option value="">PRN (Ascending)</option>
                  <option value="Ranking">Ranking</option>
                  <option value="Diff">Diff in Ranking</option>
                </select>

                {rankingMode === 'Ranking' && (
                  <>
                    <label className="text-sm text-muted-foreground">After Module</label>
                    <select
                      value={rankingModule}
                      onChange={(e) => setRankingModule(e.target.value as any)}
                      className="bg-background border border-white/10 rounded-lg px-3 py-1.5 text-sm min-w-[120px]"
                    >
                      <option value="4">Module 4</option>
                      <option value="6">Module 6</option>
                      <option value="8">Module 8</option>
                    </select>
                  </>
                )}
              </div>

              <PlacementReportTable
                data={filteredPlacementData}
                schema={placementSchema}
                sortMode={rankingMode}
                sortModule={parseInt(rankingModule, 10)}
              />
            </div>
          )}
        </TabsContent>

        <TabsContent value="modules" className="mt-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-24 text-muted-foreground gap-3">
              <Loader2 className="animate-spin" size={24} />
              <span>Loading module report…</span>
            </div>
          ) : (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <label className="text-sm text-muted-foreground">Mode</label>
                <select
                  value={rankingMode}
                  onChange={(e) => setRankingMode(e.target.value as any)}
                  className="bg-background border border-white/10 rounded-lg px-3 py-1.5 text-sm min-w-[140px]"
                >
                  <option value="">PRN (Ascending)</option>
                  <option value="Ranking">Ranking</option>
                  <option value="Diff">Diff in Ranking</option>
                </select>

                {rankingMode === 'Ranking' && (
                  <>
                    <label className="text-sm text-muted-foreground">After Module</label>
                    <select
                      value={rankingModule}
                      onChange={(e) => setRankingModule(e.target.value as any)}
                      className="bg-background border border-white/10 rounded-lg px-3 py-1.5 text-sm min-w-[120px]"
                    >
                      <option value="4">Module 4</option>
                      <option value="6">Module 6</option>
                      <option value="8">Module 8</option>
                    </select>
                  </>
                )}
              </div>

              <CCEEIAModuleTable
                data={moduleData}
                placementData={placementData}
                sortMode={rankingMode}
                sortModule={parseInt(rankingModule, 10)}
                totalsUpToModule={rankingMode === 'Ranking' ? parseInt(rankingModule, 10) : null}
              />
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
