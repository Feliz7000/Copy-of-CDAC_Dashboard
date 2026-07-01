'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AnimatedBarChart } from '@/components/ui/charts/BarChart';
import { AnimatedAreaChart } from '@/components/ui/charts/AreaChart';
import { AlertCircle, GraduationCap, Loader2, Target, TrendingUp, Users } from 'lucide-react';
import { getRoleDashboard } from '@/lib/api';

interface RoleDashboardClientProps {
  title: string;
  subtitle: string;
}

export default function RoleDashboardClient({ title, subtitle }: RoleDashboardClientProps) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    getRoleDashboard()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[40vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const stats = data?.stats ?? {};
  const categoryChart = data?.category_chart ?? [];
  const courseChart = data?.course_chart ?? [];
  const batchTrend = data?.batch_trend ?? [];

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">{title}</h2>
        <p className="text-muted-foreground">{subtitle}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-card/50 backdrop-blur-sm border-white/10">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Students</CardTitle>
            <Users className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_students ?? 0}</div>
            <p className="text-xs text-muted-foreground mt-1">With recorded scores</p>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur-sm border-white/10">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Average Score</CardTitle>
            <Target className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.average_pct ?? 0}%</div>
            <p className="text-xs text-muted-foreground mt-1">Mean grand total (of 1500)</p>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur-sm border-white/10">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Top Performers</CardTitle>
            <TrendingUp className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.top_performers ?? 0}</div>
            <p className="text-xs text-muted-foreground mt-1">Students at ≥ 85%</p>
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur-sm border-white/10">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">At Risk</CardTitle>
            <AlertCircle className="h-4 w-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">{stats.at_risk ?? 0}</div>
            <p className="text-xs text-muted-foreground mt-1">Students below 40%</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {categoryChart.length > 0 && (
          <Card className="bg-card/50 backdrop-blur-sm border-white/10">
            <CardHeader>
              <CardTitle>Average by Category</CardTitle>
              <CardDescription>Mean scaled score per assessment category.</CardDescription>
            </CardHeader>
            <CardContent>
              <AnimatedBarChart data={categoryChart} color="hsl(var(--primary))" />
            </CardContent>
          </Card>
        )}

        {courseChart.length > 1 && (
          <Card className="bg-card/50 backdrop-blur-sm border-white/10">
            <CardHeader>
              <CardTitle>Course Comparison</CardTitle>
              <CardDescription>Average grand total % by course.</CardDescription>
            </CardHeader>
            <CardContent>
              <AnimatedBarChart data={courseChart} color="hsl(var(--secondary))" />
            </CardContent>
          </Card>
        )}
      </div>

      {batchTrend.length > 1 && (
        <Card className="bg-card/50 backdrop-blur-sm border-white/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <GraduationCap className="h-5 w-5" />
              Batch Trend
            </CardTitle>
            <CardDescription>Average performance by enrollment batch.</CardDescription>
          </CardHeader>
          <CardContent>
            <AnimatedAreaChart data={batchTrend} color="hsl(var(--primary))" />
          </CardContent>
        </Card>
      )}

      {stats.total_students === 0 && (
        <Card className="border-dashed">
          <CardContent className="pt-6 text-sm text-muted-foreground text-center">
            No student score data available yet for your scope.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
