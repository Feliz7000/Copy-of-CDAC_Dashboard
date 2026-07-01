'use client';

import { useState, useEffect } from 'react';
import { Plus, AlertCircle } from 'lucide-react';
import { getMainCategories, createMainCategory, updateMainCategory, deleteMainCategory } from '@/lib/api';
import { CategoryForm } from '@/components/CategoryForm';
import { CategoriesTable } from '@/components/CategoriesTable';

export default function CategoriesPage() {
  const [categories, setCategories] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCategory, setEditingCategory] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    fetchCategories();
  }, []);

  const fetchCategories = async () => {
    try {
      setIsLoading(true);
      const data = await getMainCategories();
      setCategories(data);
      setError('');
    } catch (err: any) {
      setError('Failed to load categories');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateClick = () => {
    setEditingCategory(null);
    setIsModalOpen(true);
  };

  const handleEditClick = (category: any) => {
    setEditingCategory(category);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingCategory(null);
  };

  const handleFormSubmit = async (formData: any) => {
    try {
      setIsSubmitting(true);
      setError('');
      
      if (editingCategory) {
        await updateMainCategory(editingCategory.category_code, formData);
        setSuccess('Category updated successfully');
      } else {
        await createMainCategory(formData);
        setSuccess('Category created successfully');
      }
      
      await fetchCategories();
      handleCloseModal();
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to save category';
      setError(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (code: string) => {
    try {
      setError('');
      await deleteMainCategory(code);
      setSuccess('Category deleted successfully');
      await fetchCategories();
      
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to delete category';
      setError(errorMsg);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Categories</h2>
          <p className="text-muted-foreground mt-1 text-sm">Manage assessment categories</p>
        </div>
        <button
          onClick={handleCreateClick}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-xl hover:opacity-90 transition shadow-lg font-bold"
        >
          <Plus size={20} /> Add Category
        </button>
      </div>

      {/* Alerts */}
      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          <AlertCircle size={20} />
          <p>{error}</p>
        </div>
      )}

      {success && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
          {success}
        </div>
      )}

      {/* Table */}
      <div className="bg-card/50 backdrop-blur-sm border border-white/10 rounded-2xl shadow-xl overflow-hidden">
        <CategoriesTable
          categories={categories}
          isLoading={isLoading}
          onEdit={handleEditClick}
          onDelete={handleDelete}
        />
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-white/10 rounded-2xl shadow-2xl w-full max-w-md p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">
                {editingCategory ? 'Edit Category' : 'Create New Category'}
              </h2>
              <button onClick={handleCloseModal} className="p-2 hover:bg-muted rounded-full transition">
                <Plus size={24} className="rotate-45 text-muted-foreground" />
              </button>
            </div>
            <CategoryForm
              onSubmit={handleFormSubmit}
              initialData={editingCategory}
              isLoading={isSubmitting}
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
    </div>
  );
}
