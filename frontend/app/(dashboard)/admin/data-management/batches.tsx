'use client';

import { useState, useEffect } from 'react';
import { Plus, AlertCircle } from 'lucide-react';
import { getBatches, createBatch, updateBatch, deleteBatch } from '@/lib/api';
import { BatchForm } from '@/components/BatchForm';
import { BatchesTable } from '@/components/BatchesTable';

export default function BatchesPage() {
  const [batches, setBatches] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => { fetchBatches(); }, []);

  const fetchBatches = async () => {
    try {
      setIsLoading(true);
      const data = await getBatches();
      setBatches(data);
      setError('');
    } catch (err: any) {
      setError('Failed to load batches');
      console.error(err);
    } finally { setIsLoading(false); }
  };

  const handleCreateClick = () => { setEditing(null); setIsModalOpen(true); };
  const handleEditClick = (b: any) => { setEditing(b); setIsModalOpen(true); };
  const handleClose = () => { setIsModalOpen(false); setEditing(null); };

  const handleSubmit = async (formData: any) => {
    try {
      setIsSubmitting(true); setError('');
      if (editing) {
        await updateBatch(editing.batch_name, formData);
        setSuccess('Batch updated successfully');
      } else {
        await createBatch(formData);
        setSuccess('Batch created successfully');
      }
      await fetchBatches();
      handleClose();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to save batch';
      setError(errorMsg);
    } finally { setIsSubmitting(false); }
  };

  const handleDelete = async (batchName: string) => {
    try {
      setError('');
      await deleteBatch(batchName);
      setSuccess('Batch deleted (marked inactive)');
      await fetchBatches();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to delete batch';
      setError(errorMsg);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-foreground">Batches</h2>
          <p className="text-muted-foreground mt-1 text-sm">Manage enrolment batches (Feb/Aug)</p>
        </div>
        <button onClick={handleCreateClick} className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-xl hover:opacity-90 transition shadow-lg font-bold">
          <Plus size={20} /> Add Batch
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-3 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          <AlertCircle size={20} />
          <p>{error}</p>
        </div>
      )}

      {success && (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">{success}</div>
      )}

      <div className="bg-card/50 backdrop-blur-sm border border-white/10 rounded-2xl shadow-xl overflow-hidden">
        <BatchesTable batches={batches} isLoading={isLoading} onEdit={handleEditClick} onDelete={handleDelete} />
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-card border border-white/10 rounded-2xl shadow-2xl w-full max-w-md p-8">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">{editing ? 'Edit Batch' : 'Create New Batch'}</h2>
              <button onClick={handleClose} className="p-2 hover:bg-muted rounded-full transition">✕</button>
            </div>
            <BatchForm onSubmit={handleSubmit} initialData={editing} isLoading={isSubmitting} />
            <button onClick={handleClose} disabled={isSubmitting} className="mt-6 w-full px-4 py-3 border border-white/10 rounded-xl hover:bg-muted disabled:opacity-50 transition font-medium">Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
