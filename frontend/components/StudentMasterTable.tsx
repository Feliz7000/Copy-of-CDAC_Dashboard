'use client';

import { Edit2, Trash2, Loader2, User, BookOpen, Calendar, MapPin, GraduationCap } from 'lucide-react';

interface StudentMasterTableProps {
  students: any[];
  isLoading: boolean;
  onEdit: (student: any) => void;
  onDelete: (prn: string) => void;
}

export const StudentMasterTable = ({
  students,
  isLoading,
  onEdit,
  onDelete
}: StudentMasterTableProps) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  if (!students || students.length === 0) {
    return (
      <div className="text-center py-20 bg-muted/20 rounded-2xl border border-dashed border-white/10">
        <User size={48} className="mx-auto text-muted-foreground opacity-20 mb-4" />
        <p className="text-muted-foreground font-medium">No student records found.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b border-white/5">
          <tr>
            <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase tracking-wider">Student Details</th>
            <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase tracking-wider">Academic info</th>
            <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase tracking-wider">Status</th>
            <th className="px-6 py-4 text-right font-bold text-muted-foreground uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {students.map((student) => (
            <tr
              key={student.prn}
              className="hover:bg-primary/5 transition-colors group"
            >
              <td className="px-6 py-4">
                <div className="flex flex-col">
                  <span className="font-bold text-foreground text-base">{student.student_full_name}</span>
                  <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-0.5 rounded w-fit mt-1">
                    {student.prn}
                  </span>
                </div>
              </td>
              <td className="px-6 py-4">
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <MapPin size={14} className="text-primary" />
                    <span>{student.centre_name} ({student.centre_code})</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <BookOpen size={14} className="text-primary" />
                    <span>{student.course_name}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <GraduationCap size={14} className="text-primary" />
                    <span>Batch: {student.batch_name}</span>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4">
                <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${
                  student.is_active
                    ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/20'
                    : 'bg-red-500/10 text-red-500 border border-red-500/20'
                }`}>
                  {student.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td className="px-6 py-4">
                <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => onEdit(student)}
                    className="p-2 text-primary hover:bg-primary/10 rounded-lg transition shadow-sm"
                    title="Edit Student"
                  >
                    <Edit2 size={18} />
                  </button>
                  <button
                    onClick={() => onDelete(student.prn)}
                    className="p-2 text-red-500 hover:bg-red-500/10 rounded-lg transition shadow-sm"
                    title="Delete Student"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
