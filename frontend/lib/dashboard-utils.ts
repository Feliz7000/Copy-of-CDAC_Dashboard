const GRAND_TOTAL_MAX = 1500;

export function grandTotalPct(grandTotal: number | string, max = GRAND_TOTAL_MAX): number {
  const value = typeof grandTotal === 'string' ? parseFloat(grandTotal) : grandTotal;
  if (!Number.isFinite(value) || max <= 0) return 0;
  return Math.round((value / max) * 100);
}

export function performanceStatus(pct: number): string {
  if (pct >= 85) return 'Excellent';
  if (pct >= 60) return 'Good';
  if (pct >= 45) return 'Average';
  return 'At Risk';
}

export function performanceStatusClass(status: string): string {
  if (status === 'Excellent') return 'bg-emerald-400/10 text-emerald-400 ring-emerald-400/20';
  if (status === 'At Risk') return 'bg-red-400/10 text-red-400 ring-red-400/20';
  return 'bg-blue-400/10 text-blue-400 ring-blue-400/20';
}

export function formatBatchLabel(batchMonth: string, enrollYear: number | string): string {
  const yearSuffix = String(enrollYear).slice(-2);
  return batchMonth === '02' ? `Feb ${yearSuffix}` : `Aug ${yearSuffix}`;
}

export function roleDashboardPath(role: string): string {
  switch (role) {
    case 'admin':
      return '/admin/dashboard';
    case 'hod':
      return '/hod/dashboard';
    case 'faculty':
      return '/faculty/dashboard';
    case 'student':
      return '/student/dashboard';
    default:
      return '/login';
  }
}
