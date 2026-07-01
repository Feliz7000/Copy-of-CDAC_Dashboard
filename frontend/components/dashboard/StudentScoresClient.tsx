'use client';

import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AnimatedAreaChart } from '@/components/ui/charts/AreaChart';
import { Loader2 } from 'lucide-react';
import { getStudentSummary, getStudentScoresByDate } from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export default function StudentScoresClient() {
  const { data: session } = useSession();
  const [loading, setLoading] = useState(true);
  const [monthlyChart, setMonthlyChart] = useState<{ name: string; score: number }[]>([]);
  const [scoreRows, setScoreRows] = useState<any[]>([]);

  useEffect(() => {
    const prn = session?.user?.prn;
    if (!prn) {
      setLoading(false);
      return;
    }

    Promise.all([
      getStudentSummary(prn).catch(() => null),
      getStudentScoresByDate(prn).catch(() => []),
    ])
      .then(([summary, byDate]) => {
        const activity = summary?.monthly_activity ?? [];
        const byMonth = new Map<string, number>();
        for (const row of activity) {
          const label = row.month_label || row.exam_month;
          if (!label) continue;
          byMonth.set(label, (byMonth.get(label) ?? 0) + parseFloat(row.marks_in_month ?? 0));
        }
        setMonthlyChart(
          Array.from(byMonth.entries()).map(([name, score]) => ({ name, score: Math.round(score) }))
        );
        setScoreRows(Array.isArray(byDate) ? byDate : []);
      })
      .finally(() => setLoading(false));
  }, [session?.user?.prn]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[40vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">Detailed Scores</h2>
        <p className="text-muted-foreground">Live test history and monthly activity from your records.</p>
      </div>

      {monthlyChart.length > 0 && (
        <Card className="bg-card/50 backdrop-blur-sm border-white/10">
          <CardHeader>
            <CardTitle>Monthly Activity</CardTitle>
            <CardDescription>Total marks recorded per month across all tests.</CardDescription>
          </CardHeader>
          <CardContent>
            <AnimatedAreaChart data={monthlyChart} color="hsl(var(--primary))" />
          </CardContent>
        </Card>
      )}

      <Card className="bg-card/50 backdrop-blur-sm border-white/10">
        <CardHeader>
          <CardTitle>Test History</CardTitle>
          <CardDescription>Individual sub-test scores from the database.</CardDescription>
        </CardHeader>
        <CardContent>
          {scoreRows.length === 0 ? (
            <p className="text-sm text-muted-foreground">No scored tests found yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Test</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="text-right">Score</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {scoreRows.map((row: any) => (
                  <TableRow key={row.score_id}>
                    <TableCell>{row.sub_test_name}</TableCell>
                    <TableCell>{row.category_code}</TableCell>
                    <TableCell>{row.exam_date}</TableCell>
                    <TableCell className="text-right">
                      {row.is_absent ? 'Absent' : `${row.score} / ${row.max_marks}`}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
