'use client';

import { useState } from 'react';
import { Loader2 } from 'lucide-react';

interface CategoryFormProps {
  onSubmit: (data: any) => Promise<void>;
  initialData?: any;
  isLoading?: boolean;
}

export const CategoryForm = ({
  onSubmit,
  initialData,
  isLoading = false
}: CategoryFormProps) => {
  const [formData, setFormData] = useState({
    category_code: initialData?.category_code || '',
    category_name: initialData?.category_name || '',
    no_of_subtests: initialData?.no_of_subtests || 0,
    scaled_marks: initialData?.scaled_marks || 0,
    max_marks: initialData?.max_marks || 0,
    description: initialData?.description || ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.category_code.trim()) {
      newErrors.category_code = 'Category code is required';
    }
    if (!formData.category_name.trim()) {
      newErrors.category_name = 'Category name is required';
    }
    if (formData.no_of_subtests < 0) {
      newErrors.no_of_subtests = 'Number of subtests must be non-negative';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    const isNumeric = ['no_of_subtests', 'scaled_marks', 'max_marks'].includes(name);
    
    setFormData(prev => ({
      ...prev,
      [name]: isNumeric ? (value ? parseInt(value, 10) : 0) : value
    }));
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    await onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">Category Code</label>
          <input
            type="text"
            name="category_code"
            value={formData.category_code}
            onChange={handleChange}
            disabled={isLoading || !!initialData}
            placeholder="e.g. SCIENCE_01"
            className={`w-full bg-background border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all ${
              errors.category_code ? 'border-red-500' : 'border-border'
            } ${initialData ? 'opacity-50 cursor-not-allowed' : ''}`}
          />
          {errors.category_code && <p className="text-xs text-red-500 font-medium">{errors.category_code}</p>}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">Category Name</label>
          <input
            type="text"
            name="category_name"
            value={formData.category_name}
            onChange={handleChange}
            disabled={isLoading}
            placeholder="e.g. Science"
            className={`w-full bg-background border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all ${
              errors.category_name ? 'border-red-500' : 'border-border'
            }`}
          />
          {errors.category_name && <p className="text-xs text-red-500 font-medium">{errors.category_name}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">No. of Subtests</label>
          <input
            type="number"
            name="no_of_subtests"
            value={formData.no_of_subtests}
            onChange={handleChange}
            disabled={isLoading}
            min="0"
            className="w-full bg-background border border-border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all font-bold"
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">Max Marks (Per Subtest)</label>
          <input
            type="number"
            name="max_marks"
            value={formData.max_marks}
            onChange={handleChange}
            disabled={isLoading}
            min="0"
            className="w-full bg-background border border-border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all font-bold"
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-semibold text-muted-foreground">Description</label>
        <textarea
          name="description"
          value={formData.description}
          onChange={handleChange}
          disabled={isLoading}
          rows={3}
          placeholder="Detailed description of the category..."
          className="w-full bg-background border border-border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all resize-none"
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-3 bg-primary text-primary-foreground rounded-xl font-bold hover:opacity-90 transition shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <Loader2 className="animate-spin" size={20} />
          ) : (
            initialData ? 'Update Category' : 'Create Category'
          )}
        </button>
      </div>
    </form>
  );
};

