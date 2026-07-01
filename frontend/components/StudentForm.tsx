'use client';

import { useState, useEffect } from 'react';

interface StudentFormProps {
  onSubmit: (data: any) => Promise<void>;
  initialData?: any;
  isLoading?: boolean;
  centres: any[];
  courses: any[];
  batches: any[];
}

export const StudentForm = ({
  onSubmit,
  initialData,
  isLoading = false,
  centres,
  courses,
  batches
}: StudentFormProps) => {
  const [formData, setFormData] = useState({
    prn: initialData?.prn || '',
    student_full_name: initialData?.student_full_name || initialData?.full_name || '',
    centre: initialData?.centre || '',
    course: initialData?.course || '',
    batch: initialData?.batch || ''
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [derivedFields, setDerivedFields] = useState({
    centre_code: initialData?.centre_code || '',
    course_code: initialData?.course_code || '',
    centre_name: initialData?.centre_name || '',
    course_name: initialData?.course_name || ''
  });

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (!formData.prn.trim()) {
      newErrors.prn = 'PRN is required';
    }
    if (!formData.student_full_name.trim()) {
      newErrors.student_full_name = 'Full name is required';
    }
    if (!formData.centre) {
      newErrors.centre = 'Centre is required';
    }
    if (!formData.course) {
      newErrors.course = 'Course is required';
    }
    if (!formData.batch) {
      newErrors.batch = 'Batch is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Auto-fill derived fields
    if (name === 'centre') {
      const centre = centres.find((c: any) => c.centre_code === value);
      if (centre) {
        setDerivedFields(prev => ({
          ...prev,
          centre_code: centre.centre_code,
          centre_name: centre.centre_name
        }));
      }
    } else if (name === 'course') {
      const course = courses.find((c: any) => c.course_code === value);
      if (course) {
        setDerivedFields(prev => ({
          ...prev,
          course_code: course.course_code,
          course_name: course.course_name
        }));
      }
    }
    
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
          <label className="text-sm font-semibold text-muted-foreground">
            PRN *
          </label>
          <input
            type="text"
            name="prn"
            value={formData.prn}
            onChange={handleChange}
            disabled={isLoading || !!initialData}
            className={`w-full bg-background border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all font-mono ${
              errors.prn ? 'border-red-500' : 'border-border'
            } ${initialData ? 'opacity-50 cursor-not-allowed bg-muted/10' : ''}`}
            placeholder="e.g., 2023001"
          />
          {errors.prn && (
            <p className="text-red-500 text-xs font-medium mt-1">{errors.prn}</p>
          )}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">
            Full Name *
          </label>
          <input
            type="text"
            name="student_full_name"
            value={formData.student_full_name}
            onChange={handleChange}
            disabled={isLoading}
            className={`w-full bg-background border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all ${
              errors.student_full_name ? 'border-red-500' : 'border-border'
            }`}
            placeholder="e.g., John Doe"
          />
          {errors.student_full_name && (
            <p className="text-red-500 text-xs font-medium mt-1">{errors.student_full_name}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">
            Centre *
          </label>
          <select
            name="centre"
            value={formData.centre}
            onChange={handleChange}
            disabled={isLoading || !!initialData}
            className={`w-full bg-background border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all ${
              errors.centre ? 'border-red-500' : 'border-border'
            } ${initialData ? 'opacity-50 cursor-not-allowed bg-muted/10' : ''}`}
          >
            <option value="">Select Centre</option>
            {centres.map((centre: any) => (
              <option key={centre.centre_code} value={centre.centre_code}>
                {centre.centre_name}
              </option>
            ))}
          </select>
          {errors.centre && (
            <p className="text-red-500 text-xs font-medium mt-1">{errors.centre}</p>
          )}
        </div>

        <div className="space-y-2">
          <label className="text-sm font-semibold text-muted-foreground">
            Course *
          </label>
          <select
            name="course"
            value={formData.course}
            onChange={handleChange}
            disabled={isLoading || !!initialData}
            className={`w-full bg-background border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all ${
              errors.course ? 'border-red-500' : 'border-border'
            } ${initialData ? 'opacity-50 cursor-not-allowed bg-muted/10' : ''}`}
          >
            <option value="">Select Course</option>
            {courses.map((course: any) => (
              <option key={course.course_code} value={course.course_code}>
                {course.course_name}
              </option>
            ))}
          </select>
          {errors.course && (
            <p className="text-red-500 text-xs font-medium mt-1">{errors.course}</p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-semibold text-muted-foreground">
          Batch *
        </label>
        <select
          name="batch"
          value={formData.batch}
          onChange={handleChange}
          disabled={isLoading || !!initialData}
          className={`w-full bg-background border rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-primary/50 transition-all ${
            errors.batch ? 'border-red-500' : 'border-border'
          } ${initialData ? 'opacity-50 cursor-not-allowed bg-muted/10' : ''}`}
        >
          <option value="">Select Batch</option>
          {batches.map((batch: any) => (
            <option key={batch.batch_name} value={batch.batch_name}>
              {batch.batch_name}
            </option>
          ))}
        </select>
        {errors.batch && (
          <p className="text-red-500 text-xs font-medium mt-1">{errors.batch}</p>
        )}
      </div>

      {/* Derived Fields (Read-only) */}
      {(derivedFields.centre_code || derivedFields.course_code) && (
        <div className="p-5 bg-muted/20 rounded-2xl border border-white/5 backdrop-blur-md">
          <div className="grid grid-cols-2 gap-6 text-sm">
            {derivedFields.centre_code && (
              <div className="space-y-1">
                <label className="text-[10px] text-muted-foreground uppercase font-bold">Centre Code</label>
                <p className="text-foreground font-mono font-bold">{derivedFields.centre_code}</p>
              </div>
            )}
            {derivedFields.course_code && (
              <div className="space-y-1">
                <label className="text-[10px] text-muted-foreground uppercase font-bold">Course Code</label>
                <p className="text-foreground font-mono font-bold">{derivedFields.course_code}</p>
              </div>
            )}
            {derivedFields.centre_name && (
              <div className="space-y-1">
                <label className="text-[10px] text-muted-foreground uppercase font-bold">Centre Name</label>
                <p className="text-foreground font-bold">{derivedFields.centre_name}</p>
              </div>
            )}
            {derivedFields.course_name && (
              <div className="space-y-1">
                <label className="text-[10px] text-muted-foreground uppercase font-bold">Course Name</label>
                <p className="text-foreground font-bold">{derivedFields.course_name}</p>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="flex gap-4 pt-4">
        <button
          type="submit"
          disabled={isLoading}
          className="flex-1 py-3 bg-primary text-primary-foreground rounded-xl font-bold hover:opacity-90 transition shadow-lg disabled:opacity-50"
        >
          {isLoading ? 'Saving...' : (initialData ? 'Update Student Profile' : 'Create Student Profile')}
        </button>
      </div>
    </form>
  );
};
