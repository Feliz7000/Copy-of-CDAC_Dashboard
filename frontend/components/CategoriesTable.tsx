'use client';

import { Edit2, Trash2, Loader2, Award, Hash, Zap } from 'lucide-react';

interface CategoriesTableProps {
  categories: any[];
  isLoading: boolean;
  onEdit: (category: any) => void;
  onDelete: (code: string) => void;
}

export const CategoriesTable = ({
  categories,
  isLoading,
  onEdit,
  onDelete
}: CategoriesTableProps) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  if (!categories || categories.length === 0) {
    return (
      <div className="text-center py-20 bg-muted/20 rounded-2xl border border-dashed border-white/10">
        <Award size={48} className="mx-auto text-muted-foreground opacity-20 mb-4" />
        <p className="text-muted-foreground font-medium">No categories defined.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b border-white/5">
          <tr>
            <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase tracking-wider">Category</th>
            <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase tracking-wider">Configuration</th>
            <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase tracking-wider">Total Max Marks</th>
            <th className="px-6 py-4 text-right font-bold text-muted-foreground uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {categories.map((category) => {
            const totalMaxMarks = (category.no_of_subtests || 0) * (category.max_marks || 0);
            return (
              <tr
                key={category.category_code}
                className="hover:bg-primary/5 transition-colors group"
              >
                <td className="px-6 py-4">
                  <div className="flex flex-col">
                    <span className="font-bold text-foreground text-base">{category.category_name}</span>
                    <span className="text-xs font-mono text-primary bg-primary/10 px-2 py-0.5 rounded w-fit mt-1">
                      {category.category_code}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-col gap-1.5 text-xs text-muted-foreground font-medium">
                    <div className="flex items-center gap-2">
                      <Hash size={14} className="text-primary" />
                      <span>{category.no_of_subtests} Subtests</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Zap size={14} className="text-primary" />
                      <span>Max {category.max_marks || '0'} Marks / Subtest</span>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-col">
                    <span className="text-lg font-black text-foreground">{totalMaxMarks.toFixed(2)}</span>
                    <span className="text-[10px] text-muted-foreground uppercase tracking-tight font-bold">Accumulated Max</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => onEdit(category)}
                      className="p-2 text-primary hover:bg-primary/10 rounded-lg transition"
                      title="Edit Category"
                    >
                      <Edit2 size={18} />
                    </button>
                    <button
                      onClick={() => onDelete(category.category_code)}
                      className="p-2 text-red-500 hover:bg-red-500/10 rounded-lg transition"
                      title="Delete Category"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
