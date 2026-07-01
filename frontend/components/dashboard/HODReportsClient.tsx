'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Loader2 } from 'lucide-react';
import { getGrandTotals } from '@/lib/api';
import { grandTotalPct } from '@/lib/dashboard-utils';

export default function HODReportsClient() {
  const [loading, setLoading] = useState(true);
  const [students, setStudents] = useState<any[]>([]);

  useEffect(() => {
    getGrandTotals()
      .then((rows) => setStudents(Array.isArray(rows) ? rows : []))
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

  const withPct = students.map((s) => ({
    ...s,
    pct: grandTotalPct(s.grand_total),
  }));

  const topPerformers = [...withPct].sort((a, b) => b.pct - a.pct).slice(0, 10);
  const atRisk = withPct.filter((s) => s.pct < 45).sort((a, b) => a.pct - b.pct);

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">Analytics Reports</h2>
        <p className="text-muted-foreground">
          Top performers and at-risk students from live grand-total data.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="bg-card/50 backdrop-blur-sm border-emerald-500/20">
          <CardHeader>
            <CardTitle className="text-emerald-500">Top Performers</CardTitle>
            <CardDescription>Highest scoring students in your courses.</CardDescription>
          </CardHeader>
          <CardContent>
            {topPerformers.length === 0 ? (
              <p className="text-sm text-muted-foreground">No data available.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>PRN</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Course</TableHead>
                    <TableHead className="text-right">Score %</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topPerformers.map((student) => (
                    <TableRow key={student.prn}>
                      <TableCell className="font-medium">{student.prn}</TableCell>
                      <TableCell>{student.full_name}</TableCell>
                      <TableCell>{student.course_code}</TableCell>
                      <TableCell className="text-right font-bold text-emerald-500">{student.pct}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <Card className="bg-card/50 backdrop-blur-sm border-destructive/20">
          <CardHeader>
            <CardTitle className="text-destructive">At Risk Students</CardTitle>
            <CardDescription>Students scoring below 45% who may need intervention.</CardDescription>
          </CardHeader>
          <CardContent>
            {atRisk.length === 0 ? (
              <p className="text-sm text-muted-foreground">No at-risk students in scope.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>PRN</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Course</TableHead>
                    <TableHead className="text-right">Score %</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {atRisk.map((student) => (
                    <TableRow key={student.prn}>
                      <TableCell className="font-medium">{student.prn}</TableCell>
                      <TableCell>{student.full_name}</TableCell>
                      <TableCell>{student.course_code}</TableCell>
                      <TableCell className="text-right font-bold text-destructive">{student.pct}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
