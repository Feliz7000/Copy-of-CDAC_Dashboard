'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';

interface BatchFormProps {
  onSubmit: (data: any) => Promise<void>;
  initialData?: any;
  isLoading?: boolean;
}

export const BatchForm = ({ onSubmit, initialData, isLoading = false }: BatchFormProps) => {
  const [formData, setFormData] = useState({
    batch_name: initialData?.batch_name || '',
    batch_month: initialData?.batch_month || '02',
    batch_year: initialData?.batch_year || new Date().getFullYear(),
    is_active: initialData?.is_active ?? true
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const e: Record<string, string> = {};
    if (!formData.batch_name.trim()) e.batch_name = 'Batch name is required';
    if (!formData.batch_year || formData.batch_year < 2000) e.batch_year = 'Enter a valid year';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as HTMLInputElement;
    setFormData(prev => ({ ...prev, [name]: type === 'number' ? Number(value) : value }));
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: '' }));
  };

  const handleCheckbox = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    setFormData(prev => ({ ...prev, [name]: checked }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    await onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">Batch Name</label>
          <input
            name="batch_name"
            value={formData.batch_name}
            onChange={handleChange}
            disabled={isLoading || !!initialData}
            placeholder="e.g. Feb/26"
            className={`w-full bg-background border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all ${
              errors.batch_name ? 'border-red-500' : 'border-border'
            } ${initialData ? 'opacity-50 cursor-not-allowed' : ''}`}
          />
          {errors.batch_name && <p className="text-xs text-red-500">{errors.batch_name}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">Batch Month</label>
          <select
            name="batch_month"
            value={formData.batch_month}
            onChange={handleChange}
            disabled={isLoading}
            className="w-full bg-background border border-border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all"
          >
            <option value="02">February</option>
            <option value="08">August</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">Batch Year</label>
          <input
            type="number"
            name="batch_year"
            value={formData.batch_year}
            onChange={handleChange}
            disabled={isLoading}
            min={2000}
            className="w-full bg-background border border-border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all font-bold"
          />
          {errors.batch_year && <p className="text-xs text-red-500">{errors.batch_year}</p>}
        </div>

        <div className="space-y-2 flex items-end">
          <label className="flex items-center gap-3 text-sm font-medium">
            <input
              type="checkbox"
              name="is_active"
              checked={!!formData.is_active}
              onChange={handleCheckbox}
              disabled={isLoading}
              className="w-4 h-4"
            />
            Active
          </label>
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3 bg-primary text-primary-foreground rounded-xl font-bold hover:opacity-90 transition shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {isLoading ? <Loader2 className="animate-spin" size={20} /> : (initialData ? 'Update Batch' : 'Create Batch')}
        </button>
      </div>
    </form>
  );
};
