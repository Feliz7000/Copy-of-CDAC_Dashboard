'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Loader2 } from 'lucide-react';
import { getGrandTotals } from '@/lib/api';
import {
  formatBatchLabel,
  grandTotalPct,
  performanceStatus,
  performanceStatusClass,
} from '@/lib/dashboard-utils';

export default function FacultyStudentsClient() {
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

  return (
    <div className="flex flex-col gap-6 w-full max-w-7xl mx-auto">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-bold tracking-tight">My Students</h2>
        <p className="text-muted-foreground">Students with recorded scores in the system.</p>
      </div>

      <Card className="bg-card/50 backdrop-blur-sm border-white/10">
        <CardHeader>
          <CardTitle>Student Roster</CardTitle>
          <CardDescription>{students.length} students with performance data.</CardDescription>
        </CardHeader>
        <CardContent>
          {students.length === 0 ? (
            <p className="text-sm text-muted-foreground">No student records found.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>PRN</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Course</TableHead>
                  <TableHead>Batch</TableHead>
                  <TableHead className="text-right">Score %</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {students.map((student) => {
                  const pct = grandTotalPct(student.grand_total);
                  const status = performanceStatus(pct);
                  const batchLabel = formatBatchLabel(student.batch_month, student.enroll_year);
                  return (
                    <TableRow key={student.prn}>
                      <TableCell className="font-medium">{student.prn}</TableCell>
                      <TableCell>{student.full_name}</TableCell>
                      <TableCell>{student.course_code}</TableCell>
                      <TableCell>{batchLabel}</TableCell>
                      <TableCell className="text-right">{pct}%</TableCell>
                      <TableCell>
                        <span
                          className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${performanceStatusClass(status)}`}
                        >
                          {status}
                        </span>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
