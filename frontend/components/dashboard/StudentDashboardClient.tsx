'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AnimatedBarChart } from '@/components/ui/charts/BarChart';
import { Award, BookOpen, Calendar, Loader2 } from 'lucide-react';
import { getStudentSummary } from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export default function StudentDashboardClient() {
  const { data: session } = useSession();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<any>(null);

  useEffect(() => {
    const prn = session?.user?.prn;
    if (!prn) {
      setLoading(false);
      return;
    }

    getStudentSummary(prn)
      .then(setSummary)
      .catch(() => setError('No performance data found yet. Scores will appear after marks are entered.'))
      .finally(() => setLoading(false));
  }, [session?.user?.prn]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[40vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const student = summary?.student;
  const categoryScores = summary?.category_scores ?? [];
  const upcomingExams = summary?.upcoming_exams ?? [];

  const categoryChart = categoryScores.map((c: any) => ({
    name: c.category_name || c.category_code,
    total: Math.round(parseFloat(c.scaled_score ?? c.scaled_total ?? 0)),
  }));

  const nextExam = upcomingExams[0];

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">Welcome back, {session?.user?.name}</h2>
        <p className="text-muted-foreground">Your performance overview from live assessment data.</p>
      </div>

      {error && !student && (
        <Card className="border-amber-500/30 bg-amber-500/5">
          <CardContent className="pt-6 text-sm text-muted-foreground">{error}</CardContent>
        </Card>
      )}

      {student && (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <Card className="bg-card/50 backdrop-blur-sm border-white/10 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Grand Total Score</CardTitle>
                <Award className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  {Math.round(parseFloat(student.grand_total))} / 1500
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {((parseFloat(student.grand_total) / 1500) * 100).toFixed(1)}% of maximum
                </p>
              </CardContent>
            </Card>

            <Card className="bg-card/50 backdrop-blur-sm border-white/10 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Current Grade</CardTitle>
                <BookOpen className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-primary">{student.grade || '—'}</div>
                <p className="text-xs text-muted-foreground mt-1">{student.description || 'From aggregated scores'}</p>
              </CardContent>
            </Card>

            <Card className="bg-card/50 backdrop-blur-sm border-white/10 shadow-sm">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Upcoming Exams</CardTitle>
                <Calendar className="h-4 w-4 text-primary" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{upcomingExams.length}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {nextExam
                    ? `Next: ${nextExam.sub_test_name} (${nextExam.scheduled_date})`
                    : 'No confirmed exams scheduled'}
                </p>
              </CardContent>
            </Card>
          </div>

          {categoryChart.length > 0 && (
            <Card className="bg-card/50 backdrop-blur-sm border-white/10">
              <CardHeader>
                <CardTitle>Category Performance</CardTitle>
                <CardDescription>Scaled scores across your assessment categories.</CardDescription>
              </CardHeader>
              <CardContent className="pl-2">
                <AnimatedBarChart data={categoryChart} color="hsl(var(--primary))" />
              </CardContent>
            </Card>
          )}

          {categoryScores.length > 0 && (
            <Card className="bg-card/50 backdrop-blur-sm border-white/10">
              <CardHeader>
                <CardTitle>Score Breakdown</CardTitle>
                <CardDescription>Raw and scaled totals per category.</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Category</TableHead>
                      <TableHead className="text-right">Raw</TableHead>
                      <TableHead className="text-right">Scaled</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {categoryScores.map((row: any) => (
                      <TableRow key={row.category_code}>
                        <TableCell>{row.category_name}</TableCell>
                        <TableCell className="text-right">{Number(row.raw_score).toFixed(1)}</TableCell>
                        <TableCell className="text-right font-medium">
                          {Number(row.scaled_score).toFixed(1)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
