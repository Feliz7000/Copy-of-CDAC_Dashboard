'use client';

import { useState, useEffect } from 'react';
import { Plus, AlertCircle, Upload, FileSpreadsheet, Trash2 } from 'lucide-react';
import {
  getAllTestMappings,
  createTestMapping,
  updateTestMapping,
  deleteTestMapping,
  getLookups,
  uploadTestMappings,
  downloadTestMappingTemplate,
  bulkDeleteTestMappings
} from '@/lib/api';
import { TestMappingForm } from '@/components/TestMappingForm';
import { TestMappingsTable } from '@/components/TestMappingsTable';
import { MultiFilterDropdown } from '@/components/MultiFilterDropdown';
import { BulkUploadModal } from '@/components/BulkUploadModal';

export default function TestsPage() {
  const [mappings, setMappings] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingMapping, setEditingMapping] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [filters, setFilters] = useState<Record<string, string>>({});
  
  const [selectedRows, setSelectedRows] = useState<number[]>([]);
  const [bulkUploadModalOpen, setBulkUploadModalOpen] = useState(false);
  
  const [categories, setCategories] = useState([]);
  const [centres, setCentres] = useState([]);
  const [courses, setCourses] = useState([]);
  const [batches, setBatches] = useState([]);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    fetchMappings();
  }, [filters]);

  const loadInitialData = async () => {
    try {
      const lookups = await getLookups();
      setCategories(lookups.categories || []);
      setCentres(lookups.centres || []);
      setCourses(lookups.courses || []);
      setBatches(lookups.batches || []);
    } catch (err: any) {
      console.error('Failed to load lookups:', err);
    }
  };

  const fetchMappings = async () => {
    try {
      setIsLoading(true);
      const data = await getAllTestMappings(filters);
      setMappings(data);
      setSelectedRows([]);
      setError('');
    } catch (err: any) {
      setError('Failed to load test mappings');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateClick = () => {
    setEditingMapping(null);
    setIsModalOpen(true);
  };

  const handleEditClick = (mapping: any) => {
    setEditingMapping(mapping);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingMapping(null);
  };

  const handleFormSubmit = async (formData: any) => {
    try {
      setIsSubmitting(true);
      setError('');
      
      if (editingMapping) {
        await updateTestMapping(editingMapping.id, formData);
        setSuccess('Test mapping updated successfully');
      } else {
        await createTestMapping(formData);
        setSuccess('Test mapping created successfully');
      }
      
      await fetchMappings();
      handleCloseModal();
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      console.error('Save error:', err);
      const data = err.response?.data;
      let errorMsg = 'Failed to save mapping';
      
      if (data) {
        if (typeof data === 'string') errorMsg = data;
        else if (data.non_field_errors) errorMsg = data.non_field_errors.join(', ');
        else if (data.detail) errorMsg = data.detail;
        else if (typeof data === 'object') {
          errorMsg = Object.entries(data)
            .map(([key, val]) => `${key}: ${Array.isArray(val) ? val.join(', ') : val}`)
            .join(' | ');
        }
      } else {
        errorMsg = err.message || errorMsg;
      }
      
      setError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      setError('');
      await deleteTestMapping(id);
      setSuccess('Mapping deleted successfully');
      await fetchMappings();
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to delete mapping');
    }
  };

  const handleBulkDelete = async () => {
    if (selectedRows.length === 0) return;
    if (!confirm(`Are you sure you want to delete ${selectedRows.length} test mappings?`)) return;
    
    try {
      setError('');
      setIsLoading(true);
      await bulkDeleteTestMappings(selectedRows);
      setSuccess(`Successfully deleted ${selectedRows.length} mappings`);
      setSelectedRows([]);
      await fetchMappings();
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to delete mappings');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const blob = await downloadTestMappingTemplate();
      const url = window.URL.createObjectURL(new Blob([blob]));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'test_mapping_template.xlsx';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError('Failed to download template');
    }
  };

  const handleBulkUpload = async (file: File) => {
    try {
      const result = await uploadTestMappings(file);
      await fetchMappings();
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

  const filterOptions = [
    {
      key: 'category_code',
      label: 'Category',
      type: 'select' as const,
      options: categories.map((c: any) => ({
        label: c.category_name,
        value: c.category_code
      }))
    },
    {
      key: 'centre_code',
      label: 'Centre',
      type: 'select' as const,
      options: centres.map((c: any) => ({
        label: c.centre_name,
        value: c.centre_code
      }))
    },
    {
      key: 'course_code',
      label: 'Course',
      type: 'select' as const,
      options: courses.map((c: any) => ({
        label: c.course_name,
        value: c.course_code
      }))
    },
    {
      key: 'batch_name',
      label: 'Batch',
      type: 'select' as const,
      options: batches.map((b: any) => ({
        label: b.batch_name,
        value: b.batch_name
      }))
    }
  ];

  return (
    <div className="space-y-6">
      {/* Top Control Panel */}
      <div className="bg-card/30 backdrop-blur-md border border-white/10 rounded-3xl p-8 shadow-2xl relative group z-30">
        <div className="absolute -top-24 -right-24 w-64 h-64 bg-primary/10 rounded-full blur-3xl group-hover:bg-primary/20 transition-all duration-1000" />
        
        <div className="relative flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div>
            <h2 className="text-3xl font-black text-foreground tracking-tight">Test Management</h2>
            <p className="text-muted-foreground mt-1 text-sm font-medium">Configure subtests and map them to score columns</p>
          </div>
          
          <div className="flex flex-wrap items-center gap-3">
            <MultiFilterDropdown
              filters={filterOptions}
              onFilterChange={setFilters}
              onReset={() => setFilters({})}
            />
            
            {selectedRows.length > 0 && (
              <button
                onClick={handleBulkDelete}
                className="flex items-center gap-2 px-4 py-2.5 bg-red-500/10 text-red-500 border border-red-500/20 rounded-xl hover:bg-red-500 hover:text-white transition-all shadow-lg font-bold text-sm"
              >
                <Trash2 size={18} /> Delete Selected ({selectedRows.length})
              </button>
            )}
            
            <div className="h-8 w-[1px] bg-white/10 mx-2 hidden md:block" />
            
            <button
              onClick={handleDownloadTemplate}
              className="flex items-center gap-2 px-4 py-2.5 bg-primary/10 text-primary border border-primary/20 rounded-xl hover:bg-primary hover:text-white transition-all shadow-lg font-bold text-sm"
            >
              <FileSpreadsheet size={18} /> Template
            </button>
            
            <button
              onClick={() => setBulkUploadModalOpen(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600/10 text-emerald-500 border border-emerald-500/20 rounded-xl hover:bg-emerald-600 hover:text-white transition-all shadow-lg font-bold text-sm"
            >
              <Upload size={18} /> Bulk Import
            </button>
            
            <button
              onClick={handleCreateClick}
              className="flex items-center gap-2 px-6 py-2.5 bg-primary text-primary-foreground rounded-xl hover:opacity-90 transition shadow-xl font-bold text-sm"
            >
              <Plus size={18} /> Add Subtest
            </button>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-2xl text-red-500">
          <AlertCircle size={20} />
          <p className="text-sm font-bold">{error}</p>
        </div>
      )}

      {success && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-2xl text-emerald-400 font-bold text-sm">
          {success}
        </div>
      )}

      {/* Table */}
      <div className="bg-card/50 backdrop-blur-sm border border-white/10 rounded-2xl shadow-xl overflow-hidden">
        <TestMappingsTable
          mappings={mappings}
          isLoading={isLoading}
          selectedRows={selectedRows}
          onSelectionChange={setSelectedRows}
          onEdit={handleEditClick}
          onDelete={handleDelete}
        />
      </div>

      {/* Form Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 overflow-y-auto p-4">
          <div className="bg-card border border-white/10 rounded-2xl shadow-2xl w-full max-w-2xl p-8 animate-in zoom-in-95 duration-200 my-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-foreground">
                {editingMapping ? 'Edit Subtest Mapping' : 'Define New Subtest Mapping'}
              </h2>
              <button onClick={handleCloseModal} className="p-2 hover:bg-muted rounded-full transition">
                <Plus size={24} className="rotate-45 text-muted-foreground" />
              </button>
            </div>
            <TestMappingForm
              onSubmit={handleFormSubmit}
              initialData={editingMapping}
              isLoading={isSubmitting}
              categories={categories}
              centres={centres}
              batches={batches}
            />
            <button
              onClick={handleCloseModal}
              disabled={isSubmitting}
              className="mt-6 w-full px-4 py-3 border border-white/10 rounded-xl hover:bg-muted disabled:opacity-50 transition font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <BulkUploadModal
        isOpen={bulkUploadModalOpen}
        onClose={() => setBulkUploadModalOpen(false)}
        uploadFn={handleBulkUpload}
        title="Bulk Import Test Mappings"
        expectedColumns={[
          'centre_code',
          'batch_name',
          'category_code',
          'logical_name',
          'column_slot (e.g., test_01)',
          'max_marks',
          'sequence'
        ]}
      />
    </div>
  );
}
