'use client';

import { Edit2, Trash2, Loader2 } from 'lucide-react';

interface BatchesTableProps {
  batches: any[];
  isLoading: boolean;
  onEdit: (batch: any) => void;
  onDelete: (batchName: string) => void;
}

export const BatchesTable = ({ batches, isLoading, onEdit, onDelete }: BatchesTableProps) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  if (!batches || batches.length === 0) {
    return (
      <div className="text-center py-20 bg-muted/20 rounded-2xl border border-dashed border-white/10">
        <p className="text-muted-foreground font-medium">No batches defined.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b border-white/5">
          <tr>
            <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase tracking-wider">Batch</th>
            <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase tracking-wider">Month / Year</th>
            <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase tracking-wider">Active</th>
            <th className="px-6 py-4 text-right font-bold text-muted-foreground uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {batches.map((b) => (
            <tr key={b.batch_name} className="hover:bg-primary/5 transition-colors group">
              <td className="px-6 py-4">
                <div className="flex flex-col">
                  <span className="font-bold text-foreground text-base">{b.batch_name}</span>
                </div>
              </td>
              <td className="px-6 py-4">
                <span className="text-sm font-medium">{b.batch_month} / {b.batch_year}</span>
              </td>
              <td className="px-6 py-4">
                <span className={`px-2 py-1 rounded-lg text-xs font-semibold ${b.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  {b.is_active ? 'Active' : 'Inactive'}
                </span>
              </td>
              <td className="px-6 py-4">
                <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => onEdit(b)} className="p-2 text-primary hover:bg-primary/10 rounded-lg transition" title="Edit Batch">
                    <Edit2 size={18} />
                  </button>
                  <button onClick={() => onDelete(b.batch_name)} className="p-2 text-red-500 hover:bg-red-500/10 rounded-lg transition" title="Delete Batch">
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
