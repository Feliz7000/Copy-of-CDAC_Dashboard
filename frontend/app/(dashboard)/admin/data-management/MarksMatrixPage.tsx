'use client';

import { useState, useEffect } from 'react';
import { Upload, Search, Database, Layers, Filter, FileSpreadsheet, Trash2, AlertCircle, CheckCircle2 } from 'lucide-react';
import {
  getLookups,
  uploadScores,
  getCategoriesForCourse,
  downloadScoreTemplate,
  clearCategoryScores
} from '@/lib/api';
import { BulkUploadModal } from '@/components/BulkUploadModal';
import { ScoreMatrix } from '@/components/ScoreMatrix';

export default function MarksPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Selection state
  const [lookups, setLookups] = useState<any>({ centres: [], courses: [], batches: [] });
  const [categories, setCategories] = useState<any[]>([]);
  
  const [selectedCourse, setSelectedCourse] = useState('');
  const [selectedBatch, setSelectedBatch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  
  const [bulkUploadModalOpen, setBulkUploadModalOpen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    loadInitialData();
  }, []);

  // When course changes, load applicable categories
  useEffect(() => {
    if (selectedCourse) {
      loadCategories(selectedCourse);
    } else {
      setCategories([]);
      setSelectedCategory('');
    }
  }, [selectedCourse]);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      const data = await getLookups();
      setLookups(data);
    } catch (err: any) {
      setError('Failed to load initial data');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadCategories = async (courseCode: string) => {
    try {
      const data = await getCategoriesForCourse(courseCode);
      setCategories(data);
    } catch (err: any) {
      console.error('Error loading categories:', err);
    }
  };

  const handleBulkUpload = async (file: File) => {
    try {
      const result = await uploadScores(file);
      // If we have a matrix open, we might want to refresh it
      return result;
    } catch (err: any) {
      return {
        success: false,
        created: 0,
        skipped: 0,
        errors: [err.response?.data?.error || err.response?.data?.detail || err.message || 'Upload failed'],
        warnings: []
      };
    }
  };

  const handleDownloadTemplate = async () => {
    if (!isScopeSelected) return;
    try {
      const blob = await downloadScoreTemplate(selectedCategory, selectedCourse, selectedBatch);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Template_${selectedCategory}_${selectedBatch.replace('/', '_')}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to download template. Ensure Test Mappings exist for this scope.');
    }
  };

  const handleClearData = async () => {
    if (!isScopeSelected) return;
    
    const confirmClear = window.confirm(
      `⚠️ PERMANENT DELETE WARNING ⚠️\n\nAre you sure you want to delete ALL scores for category "${selectedCategory}" in batch "${selectedBatch}"?\n\nThis action cannot be undone and will permanently remove all marks for the ${lookups.courses.find((c:any) => c.course_code === selectedCourse)?.course_name || 'selected course'}.`
    );
    
    if (!confirmClear) return;
    
    try {
      setIsLoading(true);
      setError('');
      const result = await clearCategoryScores(selectedCategory, selectedCourse, selectedBatch);
      setSuccess(result.message);
      setRefreshKey(prev => prev + 1);
      setTimeout(() => setSuccess(''), 5000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to clear data');
    } finally {
      setIsLoading(false);
    }
  };

  const isScopeSelected = selectedCourse && selectedBatch && selectedCategory;

  return (
    <div className="space-y-8 pb-20">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-black text-foreground tracking-tight">Performance Matrix</h2>
          <p className="text-muted-foreground mt-1 text-sm font-medium">Manage student scores across all categories</p>
        </div>
        <div className="flex gap-3">
          {isScopeSelected && (
            <>
              <button
                onClick={handleClearData}
                className="flex items-center gap-2 px-6 py-2.5 bg-red-600/10 text-red-500 border border-red-500/20 rounded-2xl hover:bg-red-600 hover:text-white transition-all shadow-lg font-bold"
              >
                <Trash2 size={20} /> Clear Data
              </button>
              <button
                onClick={handleDownloadTemplate}
                className="flex items-center gap-2 px-6 py-2.5 bg-primary/10 text-primary border border-primary/20 rounded-2xl hover:bg-primary hover:text-white transition-all shadow-lg font-bold"
              >
                <FileSpreadsheet size={20} /> Download Template
              </button>
            </>
          )}
          <button
            onClick={() => setBulkUploadModalOpen(true)}
            className="flex items-center gap-2 px-6 py-2.5 bg-emerald-600/10 text-emerald-500 border border-emerald-500/20 rounded-2xl hover:bg-emerald-600 hover:text-white transition-all shadow-lg font-bold"
          >
            <Upload size={20} /> Bulk Import Excel
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-500 font-bold flex items-center gap-3 animate-in slide-in-from-top-4 duration-300">
          <AlertCircle size={20} /> {error}
        </div>
      )}
      {success && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl text-emerald-500 font-bold flex items-center gap-3 animate-in slide-in-from-top-4 duration-300">
          <CheckCircle2 size={20} /> {success}
        </div>
      )}

      {/* Scope Selection */}
      <div className="bg-card/30 backdrop-blur-md border border-white/10 rounded-[2.5rem] p-10 shadow-2xl relative overflow-visible group">
        <div className="flex items-center gap-3 mb-8">
          <div className="p-3 bg-primary/10 rounded-2xl text-primary">
            <Filter size={24} />
          </div>
          <h3 className="text-2xl font-black text-foreground">Select Scope</h3>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">

          <div className="space-y-3">
            <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">
              Course
            </label>
            <select
              value={selectedCourse}
              onChange={(e) => setSelectedCourse(e.target.value)}
              className="w-full px-5 py-4 bg-background border-2 border-white/5 rounded-2xl focus:outline-none focus:border-primary/50 focus:ring-4 focus:ring-primary/10 transition-all font-bold text-sm appearance-none cursor-pointer hover:bg-muted/50"
            >
              <option value="">Select Course</option>
              {lookups.courses.map((c: any) => (
                <option key={c.course_code} value={c.course_code}>{c.course_name}</option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
            <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">
              Batch
            </label>
            <select
              value={selectedBatch}
              onChange={(e) => setSelectedBatch(e.target.value)}
              className="w-full px-5 py-4 bg-background border-2 border-white/5 rounded-2xl focus:outline-none focus:border-primary/50 focus:ring-4 focus:ring-primary/10 transition-all font-bold text-sm appearance-none cursor-pointer hover:bg-muted/50"
            >
              <option value="">Select Batch</option>
              {lookups.batches.map((b: any) => (
                <option key={b.batch_name} value={b.batch_name}>{b.batch_name}</option>
              ))}
            </select>
          </div>

          <div className="space-y-3">
            <label className="text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em] ml-1">
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              disabled={!selectedCourse}
              className={`w-full px-5 py-4 bg-background border-2 border-white/5 rounded-2xl focus:outline-none focus:border-primary/50 focus:ring-4 focus:ring-primary/10 transition-all font-bold text-sm appearance-none cursor-pointer hover:bg-muted/50 ${!selectedCourse ? 'opacity-40 cursor-not-allowed' : ''}`}
            >
              <option value="">Select Category</option>
              {categories.map((cat: any) => (
                <option key={cat.category_code} value={cat.category_code}>
                  {cat.category_name} ({cat.category_code})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Main Matrix Area */}
      {isScopeSelected ? (
        <ScoreMatrix
          key={`${selectedCategory}-${selectedCourse}-${selectedBatch}-${refreshKey}`}
          categoryCode={selectedCategory}
          courseCode={selectedCourse}
          batchName={selectedBatch}
        />
      ) : (
        <div className="flex flex-col items-center justify-center py-32 bg-card/10 rounded-[3rem] border-2 border-dashed border-white/5 opacity-40">
          <Database size={64} className="text-muted-foreground mb-6" />
          <h3 className="text-2xl font-bold">Awaiting Selection</h3>
          <p className="text-muted-foreground font-medium mt-2">
            Please select a Course, Batch, and Category above to view the scores.
          </p>
        </div>
      )}

      {/* Bulk Upload Modal */}
      <BulkUploadModal
        isOpen={bulkUploadModalOpen}
        onClose={() => setBulkUploadModalOpen(false)}
        uploadFn={handleBulkUpload}
        title="Bulk Upload Scores (Matrix Format)"
        description="Upload an Excel file where columns match the Logical Names defined in your Test Mappings."
        expectedColumns={[
          'prn',
          'category_code',
          'batch_name',
          '...Logical Test Names...'
        ]}
      />
    </div>
  );
}
