'use client';

import { useState } from 'react';
import { Upload, X, Check, AlertCircle } from 'lucide-react';

interface UploadResult {
  success: boolean;
  created: number;
  skipped: number;
  errors: string[];
  warnings: string[];
}

interface BulkUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  uploadFn: (file: File) => Promise<UploadResult>;
  title: string;
  expectedColumns: string[];
}

export const BulkUploadModal = ({
  isOpen,
  onClose,
  uploadFn,
  title,
  expectedColumns
}: BulkUploadModalProps) => {
  const [file, setFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFile(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    
    setIsLoading(true);
    try {
      const uploadResult = await uploadFn(file);
      setResult(uploadResult);
    } catch (error: any) {
      setResult({
        success: false,
        created: 0,
        skipped: 0,
        errors: [error.message || 'Upload failed'],
        warnings: []
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setResult(null);
    setDragActive(false);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button
            onClick={handleClose}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {!result ? (
            <>
              {/* File Upload Area */}
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition ${
                  dragActive
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <Upload className="mx-auto mb-3 text-gray-400" size={32} />
                <p className="font-semibold text-gray-700 mb-1">
                  Drag & drop your Excel file
                </p>
                <p className="text-sm text-gray-500 mb-3">or</p>
                <label className="inline-block">
                  <span className="bg-blue-500 text-white px-4 py-2 rounded cursor-pointer hover:bg-blue-600">
                    Browse File
                  </span>
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                </label>
              </div>

              {/* Selected File */}
              {file && (
                <div className="mt-4 p-3 bg-gray-50 rounded flex justify-between items-center">
                  <span className="text-sm text-gray-700">{file.name}</span>
                  <button
                    onClick={() => setFile(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X size={16} />
                  </button>
                </div>
              )}

              {/* Expected Columns Info */}
              <div className="mt-4 p-3 bg-blue-50 rounded text-sm text-gray-700">
                <p className="font-semibold mb-2">Expected columns:</p>
                <ul className="list-disc list-inside space-y-1">
                  {expectedColumns.map((col) => (
                    <li key={col}>{col}</li>
                  ))}
                </ul>
              </div>

              {/* Actions */}
              <div className="mt-6 flex gap-3">
                <button
                  onClick={handleClose}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleUpload}
                  disabled={!file || isLoading}
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </>
          ) : (
            <>
              {/* Result */}
              <div className="space-y-4">
                {/* Status */}
                <div className={`p-4 rounded flex items-start gap-3 ${
                  result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
                }`}>
                  {result.success ? (
                    <Check className="text-green-600 flex-shrink-0 mt-0.5" size={20} />
                  ) : (
                    <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
                  )}
                  <div>
                    <p className={`font-semibold ${result.success ? 'text-green-900' : 'text-red-900'}`}>
                      {result.success ? 'Upload Successful!' : 'Upload Failed'}
                    </p>
                    <p className={`text-sm ${result.success ? 'text-green-700' : 'text-red-700'}`}>
                      Created: {result.created} | Skipped: {result.skipped}
                    </p>
                  </div>
                </div>

                {/* Errors */}
                {result.errors.length > 0 && (
                  <div className="bg-red-50 rounded p-3">
                    <p className="font-semibold text-red-900 text-sm mb-2">Errors:</p>
                    <div className="space-y-1 max-h-48 overflow-y-auto">
                      {result.errors.map((error, i) => (
                        <p key={i} className="text-xs text-red-700">{error}</p>
                      ))}
                    </div>
                  </div>
                )}

                {/* Warnings */}
                {result.warnings.length > 0 && (
                  <div className="bg-yellow-50 rounded p-3">
                    <p className="font-semibold text-yellow-900 text-sm mb-2">Warnings:</p>
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {result.warnings.map((warning, i) => (
                        <p key={i} className="text-xs text-yellow-700">{warning}</p>
                      ))}
                    </div>
                  </div>
                )}

                {/* Close Button */}
                <button
                  onClick={handleClose}
                  className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  Close
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
