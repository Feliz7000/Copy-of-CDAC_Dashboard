'use client';

import { Edit2, Trash2, Loader2, Table, MapPin, Hash, Award, CheckCircle2, XCircle } from 'lucide-react';

interface TestMappingsTableProps {
  mappings: any[];
  isLoading: boolean;
  selectedRows?: number[];
  onSelectionChange?: (ids: number[]) => void;
  onEdit: (mapping: any) => void;
  onDelete: (id: number) => void;
}

export const TestMappingsTable = ({
  mappings,
  isLoading,
  selectedRows = [],
  onSelectionChange,
  onEdit,
  onDelete
}: TestMappingsTableProps) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-primary" size={32} />
      </div>
    );
  }

  if (!mappings || mappings.length === 0) {
    return (
      <div className="text-center py-20 bg-muted/20 rounded-2xl border border-dashed border-white/10">
        <Table size={48} className="mx-auto text-muted-foreground opacity-20 mb-4" />
        <p className="text-muted-foreground font-medium">No test mappings found for this scope.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 border-b border-white/5">
          <tr>
            {onSelectionChange && (
              <th className="px-6 py-4 text-left w-12">
                <input
                  type="checkbox"
                  className="rounded border-white/20 bg-black/20 text-primary focus:ring-primary/50"
                  checked={mappings.length > 0 && selectedRows.length === mappings.length}
                  onChange={(e) => {
                    if (e.target.checked) {
                      onSelectionChange(mappings.map((m) => m.id));
                    } else {
                      onSelectionChange([]);
                    }
                  }}
                />
              </th>
            )}
            <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase tracking-wider">Test / Slot</th>
            <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase tracking-wider">Scope</th>
            <th className="px-6 py-4 text-left font-bold text-muted-foreground uppercase tracking-wider">Config</th>
            <th className="px-6 py-4 text-right font-bold text-muted-foreground uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-white/5">
          {mappings.map((mapping) => (
            <tr
              key={mapping.id}
              className={`hover:bg-primary/5 transition-colors group ${selectedRows.includes(mapping.id) ? 'bg-primary/5' : ''}`}
            >
              {onSelectionChange && (
                <td className="px-6 py-4 w-12">
                  <input
                    type="checkbox"
                    className="rounded border-white/20 bg-black/20 text-primary focus:ring-primary/50"
                    checked={selectedRows.includes(mapping.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        onSelectionChange([...selectedRows, mapping.id]);
                      } else {
                        onSelectionChange(selectedRows.filter((id) => id !== mapping.id));
                      }
                    }}
                  />
                </td>
              )}
              <td className="px-6 py-4">
                <div className="flex flex-col">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-foreground text-base">{mapping.logical_name}</span>
                    {mapping.is_active ? (
                      <CheckCircle2 size={14} className="text-emerald-500" title="Active" />
                    ) : (
                      <XCircle size={14} className="text-muted-foreground/50" title="Inactive" />
                    )}
                  </div>
                  <span className="text-[10px] font-mono text-primary bg-primary/10 px-2 py-0.5 rounded w-fit mt-1 uppercase tracking-tight">
                    {mapping.column_slot}
                  </span>
                </div>
              </td>
              <td className="px-6 py-4">
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Award size={14} className="text-primary" />
                    <span className="font-bold text-foreground/80">{mapping.category_name}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <MapPin size={14} className="text-primary" />
                    <span>{mapping.centre_name} — {mapping.batch_name}</span>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-black text-foreground">{mapping.max_marks}</span>
                    <span className="text-[10px] text-muted-foreground uppercase font-bold">Max Marks</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                    <Hash size={12} className="text-primary" />
                    <span>Sequence {mapping.sequence}</span>
                  </div>
                </div>
              </td>
              <td className="px-6 py-4">
                <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => onEdit(mapping)}
                    className="p-2 text-primary hover:bg-primary/10 rounded-lg transition"
                    title="Edit Mapping"
                  >
                    <Edit2 size={18} />
                  </button>
                  <button
                    onClick={() => onDelete(mapping.id)}
                    className="p-2 text-red-500 hover:bg-red-500/10 rounded-lg transition"
                    title="Delete Mapping"
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
