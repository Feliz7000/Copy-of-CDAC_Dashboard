'use client';

import { useState, useEffect } from 'react';
import { Plus, AlertCircle, Upload, Search, Loader2, FileSpreadsheet } from 'lucide-react';
import {
  getStudents,
  createStudent,
  updateStudent,
  deleteStudent,
  uploadStudents,
  getLookups,
  downloadStudentTemplate
} from '@/lib/api';
import { StudentForm } from '@/components/StudentForm';
import { StudentMasterTable } from '@/components/StudentMasterTable';
import { BulkUploadModal } from '@/components/BulkUploadModal';
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { roleDashboardPath } from "@/lib/dashboard-utils";

export default function AdminStudentsPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  
  const [students, setStudents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, string>>({});
  
  const [centres, setCentres] = useState([]);
  const [courses, setCourses] = useState([]);
  const [batches, setBatches] = useState([]);
  
  const [bulkUploadModalOpen, setBulkUploadModalOpen] = useState(false);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login");
    } else if (status === "authenticated" && session?.user?.role !== "admin") {
      router.push(roleDashboardPath(session.user.role));
    }
  }, [status, session, router]);

  useEffect(() => {
    if (status === "authenticated") {
      loadInitialData();
      fetchStudents();
    }
  }, [status, filters]);

  const loadInitialData = async () => {
    try {
      const lookups = await getLookups();
      setCentres(lookups.centres || []);
      setCourses(lookups.courses || []);
      setBatches(lookups.batches || []);
    } catch (err: any) {
      console.error('Failed to load lookups:', err);
    }
  };

  const fetchStudents = async () => {
    try {
      setIsLoading(true);
      const params = {
        ...filters,
        ...(searchQuery && { search: searchQuery })
      };
      const data = await getStudents(Object.keys(params).length > 0 ? params : undefined);
      setStudents(data);
      setError('');
    } catch (err: any) {
      setError('Failed to load students');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleSearchSubmit = () => {
    fetchStudents();
  };

  const handleCreateClick = () => {
    setEditingStudent(null);
    setIsModalOpen(true);
  };

  const handleEditClick = (student: any) => {
    setEditingStudent(student);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingStudent(null);
  };

  const handleFormSubmit = async (formData: any) => {
    try {
      setIsSubmitting(true);
      setError('');
      
      if (editingStudent) {
        await updateStudent(editingStudent.prn, formData);
        setSuccess('Student updated successfully');
      } else {
        await createStudent(formData);
        setSuccess('Student created successfully');
      }
      
      await fetchStudents();
      handleCloseModal();
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      console.error('Save error:', err);
      const data = err.response?.data;
      let errorMsg = 'Failed to save student';
      
      if (data) {
        if (typeof data === 'string') errorMsg = data;
        else if (data.detail) errorMsg = data.detail;
        else if (typeof data === 'object') {
          // Join field errors: "field: error"
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

  const handleDelete = async (prn: string) => {
    if (!confirm(`Are you sure you want to delete student ${prn}?`)) return;
    try {
      setError('');
      await deleteStudent(prn);
      setSuccess('Student deleted successfully');
      await fetchStudents();
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to delete student';
      setError(errorMsg);
    }
  };

  const handleBulkUpload = async (file: File) => {
    try {
      const result = await uploadStudents(file);
      await fetchStudents();
      return result;
    } catch (err: any) {
      return {
        success: false,
        created: 0,
        skipped: 0,
        errors: [err.response?.data?.detail || err.message || 'Upload failed'],
        warnings: []
      };
    }
  };

  if (status === "loading") {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 pb-20">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Student Master</h1>
          <p className="text-muted-foreground mt-1">Manage student information across all centres and batches.</p>
        </div>
        <div className="flex flex-wrap gap-2 w-full sm:w-auto">
          <button
            onClick={async () => {
              try {
                await downloadStudentTemplate();
              } catch (err) {
                setError('Failed to download template');
              }
            }}
            className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-primary/10 text-primary border border-primary/20 rounded-lg hover:bg-primary hover:text-white transition shadow-sm font-medium"
          >
            <FileSpreadsheet size={20} /> <span className="hidden sm:inline">Template</span>
          </button>
          <button
            onClick={() => setBulkUploadModalOpen(true)}
            className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition shadow-sm"
          >
            <Upload size={20} /> <span className="hidden sm:inline">Bulk Import</span>
          </button>
          <button
            onClick={handleCreateClick}
            className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition shadow-sm"
          >
            <Plus size={20} /> <span className="hidden sm:inline">Add Student</span>
          </button>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500">
          <AlertCircle size={20} />
          <p>{typeof error === 'string' ? error : JSON.stringify(error)}</p>
        </div>
      )}

      {success && (
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-500">
          {success}
        </div>
      )}

      {/* Search & Filters */}
      <div className="bg-card/50 backdrop-blur-sm border border-white/10 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 text-muted-foreground" size={20} />
            <input
              type="text"
              placeholder="Search by PRN or Name..."
              value={searchQuery}
              onChange={handleSearch}
              onKeyPress={(e) => e.key === 'Enter' && handleSearchSubmit()}
              className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
            />
          </div>
          <button
            onClick={handleSearchSubmit}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition shadow-sm font-medium"
          >
            Search
          </button>
        </div>
      </div>

      {/* Table Section */}
      <div className="bg-card/50 backdrop-blur-sm border border-white/10 rounded-xl shadow-sm overflow-hidden">
        <StudentMasterTable
          students={students}
          isLoading={isLoading}
          onEdit={handleEditClick}
          onDelete={handleDelete}
        />
      </div>

      {/* Form Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 overflow-y-auto p-4">
          <div className="bg-card border border-white/10 rounded-2xl shadow-2xl w-full max-w-2xl p-8 animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">
                {editingStudent ? 'Edit Student Profile' : 'Register New Student'}
              </h2>
              <button 
                onClick={handleCloseModal}
                className="p-2 hover:bg-muted rounded-full transition"
              >
                <Plus size={24} className="rotate-45 text-muted-foreground" />
              </button>
            </div>
            
            <StudentForm
              onSubmit={handleFormSubmit}
              initialData={editingStudent}
              isLoading={isSubmitting}
              centres={centres}
              courses={courses}
              batches={batches}
            />
            
            <button
              onClick={handleCloseModal}
              disabled={isSubmitting}
              className="mt-6 w-full px-4 py-3 border border-border rounded-xl hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed transition font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Bulk Upload Modal */}
      <BulkUploadModal
        isOpen={bulkUploadModalOpen}
        onClose={() => setBulkUploadModalOpen(false)}
        uploadFn={handleBulkUpload}
        title="Bulk Student Onboarding"
        expectedColumns={[
          'prn',
          'full_name',
          'centre_code',
          'course_code',
          'batch_name'
        ]}
      />
    </div>
  );
}
