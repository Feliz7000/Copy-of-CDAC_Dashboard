'use client';

import { useState } from 'react';
import { Loader2, Info, Hash } from 'lucide-react';

interface TestMappingFormProps {
  onSubmit: (data: any) => Promise<void>;
  initialData?: any;
  isLoading?: boolean;
  categories: any[];
  centres: any[];
  batches: any[];
}

export const TestMappingForm = ({
  onSubmit,
  initialData,
  isLoading = false,
  categories,
  centres,
  batches
}: TestMappingFormProps) => {
  const [formData, setFormData] = useState({
    batch_name: initialData?.batch_name || '',
    category_code: initialData?.category_code || '',
    logical_name: initialData?.logical_name || '',
    column_slot: initialData?.column_slot || 'test_01',
    max_marks: initialData?.max_marks || 100,
    sequence: initialData?.sequence || 1,
    is_active: initialData?.is_active ?? true
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.logical_name) newErrors.logical_name = 'Test name is required';
    if (!formData.category_code) newErrors.category_code = 'Category is required';
    if (!formData.batch_name) newErrors.batch_name = 'Batch is required';
    if (!formData.column_slot) newErrors.column_slot = 'Slot is required';
    if (formData.max_marks <= 0) newErrors.max_marks = 'Max marks must be > 0';
    if (formData.sequence < 1) newErrors.sequence = 'Sequence must be >= 1';

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as any;
    let finalValue = value;

    if (type === 'checkbox') {
      finalValue = (e.target as any).checked;
    } else if (name === 'max_marks' || name === 'sequence') {
      // If empty string, keep as empty to allow typing, otherwise parse
      finalValue = value === '' ? '' : parseInt(value, 10);
      if (isNaN(finalValue as any) && value !== '') finalValue = 0;
    }

    setFormData(prev => ({
      ...prev,
      [name]: finalValue
    }));
    if (errors[name]) setErrors(prev => ({ ...prev, [name]: '' }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    await onSubmit(formData);
  };

  // Generate slot options (test_01 to test_50)
  const slotOptions = Array.from({ length: 50 }, (_, i) => {
    const slot = `test_${(i + 1).toString().padStart(2, '0')}`;
    return { value: slot, label: `Slot ${i + 1} (${slot})` };
  });

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Scope Header */}
      <div className="bg-primary/5 p-4 rounded-xl border border-primary/10 flex items-center gap-3 mb-2">
        <div className="p-2 bg-primary/10 rounded-lg">
          <Info size={18} className="text-primary" />
        </div>
        <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider">
          Mappings are specific to the selected Batch and Category.
        </p>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-semibold text-muted-foreground">Test Name (Visible to Users)</label>
        <input
          type="text"
          name="logical_name"
          value={formData.logical_name}
          onChange={handleChange}
          placeholder="e.g. Logic & Reasoning"
          className={`w-full bg-background border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all ${
            errors.logical_name ? 'border-red-500' : 'border-border'
          }`}
        />
        {errors.logical_name && <p className="text-xs text-red-500 font-medium">{errors.logical_name}</p>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">Category</label>
          <select
            name="category_code"
            value={formData.category_code}
            onChange={handleChange}
            className={`w-full bg-background border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all ${
              errors.category_code ? 'border-red-500' : 'border-border'
            }`}
          >
            <option value="">Select Category</option>
            {categories.map((cat) => (
              <option key={cat.category_code} value={cat.category_code}>
                {cat.category_name} (Max {cat.no_of_subtests} tests)
              </option>
            ))}
          </select>
          {errors.category_code && <p className="text-xs text-red-500 font-medium">{errors.category_code}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">Database Column Slot</label>
          <select
            name="column_slot"
            value={formData.column_slot}
            onChange={handleChange}
            className="w-full bg-background border border-border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all"
          >
            {slotOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <p className="text-[10px] text-muted-foreground mt-1">This determines which partitioned column stores the marks.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Centre Dropdown Removed */}

        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">Batch</label>
          <select
            name="batch_name"
            value={formData.batch_name}
            onChange={handleChange}
            className="w-full bg-background border border-border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all"
          >
            <option value="">Select Batch</option>
            {batches.map((batch) => (
              <option key={batch.batch_name} value={batch.batch_name}>{batch.batch_name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">Max Marks</label>
          <input
            type="number"
            name="max_marks"
            value={formData.max_marks ?? ''}
            onChange={handleChange}
            min="1"
            className="w-full bg-background border border-border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all font-bold"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground flex items-center gap-2">
            <Hash size={14} /> Display Sequence
          </label>
          <input
            type="number"
            name="sequence"
            value={formData.sequence ?? ''}
            onChange={handleChange}
            min="1"
            className="w-full bg-background border border-border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all font-bold"
          />
        </div>
      </div>

      <div className="flex items-center gap-2 pt-2">
        <input
          type="checkbox"
          id="is_active"
          name="is_active"
          checked={formData.is_active}
          onChange={handleChange}
          className="w-4 h-4 rounded border-border text-primary focus:ring-primary"
        />
        <label htmlFor="is_active" className="text-sm font-semibold text-foreground cursor-pointer">
          Mapping is Active (Visible in Score Matrix)
        </label>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full py-3 bg-primary text-primary-foreground rounded-xl font-bold hover:opacity-90 transition shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
      >
        {isLoading ? <Loader2 className="animate-spin" size={20} /> : (initialData ? 'Update Mapping' : 'Create Mapping')}
      </button>
    </form>
  );
};
