// ─── Placement Report Types ────────────────────────────────────────────────

export interface CategorySummary {
  scored: number;
  max: number;
  pct: number;
  cutoff_met: boolean | null; // null = category not yet countable (min threshold not met)
  subtests_entered: number;
}

export interface PlacementRow {
  prn: string;
  student_full_name: string;
  batch_name: string;
  course_code: string;
  centre_code: string;
  // Per-category
  cc_scored: number;
  cc_max: number;
  cc_pct: number;
  cc_cutoff_met: boolean | null;
  cc_subtests_entered: number;
  ia_scored: number;
  ia_max: number;
  ia_pct: number;
  ia_cutoff_met: boolean | null;
  ia_subtests_entered: number;
  ap_scored: number;
  ap_max: number;
  ap_pct: number;
  ap_cutoff_met: boolean | null;
  ap_subtests_entered: number;
  sx_scored: number;
  sx_max: number;
  sx_pct: number;
  sx_cutoff_met: boolean | null;
  sx_subtests_entered: number;
  ps_scored: number;
  ps_max: number;
  ps_pct: number;
  ps_cutoff_met: boolean | null;
  ps_subtests_entered: number;
  gr_scored: number;
  gr_max: number;
  gr_pct: number;
  gr_cutoff_met: boolean | null;
  gr_subtests_entered: number;
  ta_scored: number;
  ta_max: number;
  ta_pct: number;
  ta_cutoff_met: boolean | null;
  ta_subtests_entered: number;
  na_scored: number;
  na_max: number;
  na_pct: number;
  na_cutoff_met: boolean | null;
  na_subtests_entered: number;
  in_scored: number;
  in_max: number;
  in_pct: number;
  in_cutoff_met: boolean | null;
  in_subtests_entered: number;
  as_scored: number;
  as_max: number;
  as_pct: number;
  as_cutoff_met: boolean | null;
  as_subtests_entered: number;
  pq_scored: number;
  pq_max: number;
  pq_pct: number;
  pq_cutoff_met: boolean | null;
  pq_subtests_entered: number;
  gac_scored: number;
  gac_max: number;
  gac_pct: number;
  gac_cutoff_met: boolean | null;
  gac_subtests_entered: number;
  gac_grade: string | null;
  prj_scored: number;
  prj_max: number;
  prj_pct: number;
  prj_cutoff_met: boolean | null;
  prj_subtests_entered: number;
  prj_grade: string | null;
  // Totals
  grand_total_scored: number;
  grand_total_max: number;
  grand_total_pct: number;
  pass_fail: 'Pass' | 'Fail';
  placement_status: 'Placement ready' | 'Can Improve' | 'Not Placement ready' | 'Unknown';
  // Dynamic individual subtest keys (e.g., 'cc_test_01': 16.0)
  [key: string]: any;
}

export interface SchemaColumn {
  slot: string;
  name: string;
  max: number;
  seq: number;
}

export type ReportSchema = Record<string, SchemaColumn[]>;

export interface PlacementReportResponse {
  schema: ReportSchema;
  results: PlacementRow[];
}

// ─── CCEE + IA Module Report Types ────────────────────────────────────────

export interface ModuleData {
  module_no: number;
  ccee_score: number | null;
  ccee_max: number | null;
  ia_score: number | null;
  ia_max: number | null;
  module_total: number | null;
  module_max: number | null;
}

export interface ModuleTotals {
  ccee_total: number;
  ia_total: number;
  grand_total: number;
  grand_max: number;
  percentage: number;
  pass_fail: 'Pass' | 'Fail';
}

export interface ModuleRow {
  prn: string;
  student_name: string;
  modules: ModuleData[];
  totals: ModuleTotals;
  rank_after_m4?: number | null;
  rank_after_m6?: number | null;
  rank_after_m8?: number | null;
}

// ─── Category metadata (for table headers) ────────────────────────────────

export const CATEGORY_META: Record<
  string,
  { label: string; cutoffLabel: string; color: string }
> = {
  cc: { label: 'CCEE',         cutoffLabel: '≥65% & each ≥16', color: 'blue'    },
  ia: { label: 'IA/Module',    cutoffLabel: '≥65% & each ≥24', color: 'violet'  },
  ap: { label: 'Aptitude',     cutoffLabel: 'each ≥80%',        color: 'amber'   },
  sx: { label: 'Speak X',      cutoffLabel: 'each ≥50%',        color: 'cyan'    },
  ps: { label: 'Personality',  cutoffLabel: '≥50%',             color: 'pink'    },
  gr: { label: 'Grooming',     cutoffLabel: '≥50%',             color: 'rose'    },
  ta: { label: 'Tech Act.',    cutoffLabel: '≥40% & each ≥4',   color: 'teal'    },
  na: { label: 'Non-Tech Act.',cutoffLabel: '≥40% & each ≥4',   color: 'indigo'  },
  in: { label: 'Interview',    cutoffLabel: 'each ≥80% (all 5)',color: 'orange'  },
  as: { label: 'Assignments',  cutoffLabel: 'each ≥80% (≥25)',  color: 'lime'    },
  pq: { label: 'Practice Quiz',cutoffLabel: 'each ≥80% (all 30)',color: 'fuchsia'},
  gac: { label: 'GAC Grade',   cutoffLabel: '≥40% / A+ to F',   color: 'emerald'  },
  prj: { label: 'Project Grade',cutoffLabel: '≥40% / A+ to F',   color: 'slate'    },
};
