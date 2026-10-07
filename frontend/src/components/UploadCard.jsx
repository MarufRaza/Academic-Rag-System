import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, Loader2, X } from 'lucide-react';
import api from '../services/api';

export default function UploadCard({ onUploadSuccess, onNotify }) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStage, setUploadStage] = useState('');
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesSelected(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFilesSelected(Array.from(e.target.files));
    }
  };

  const handleFilesSelected = (files) => {
    // Filter for PDFs
    const pdfFiles = files.filter((f) => f.name.toLowerCase().endsWith('.pdf'));
    const nonPdfs = files.filter((f) => !f.name.toLowerCase().endsWith('.pdf'));

    if (nonPdfs.length > 0) {
      onNotify({
        type: 'warning',
        message: `Skipped ${nonPdfs.length} non-PDF file(s). Only .pdf documents are supported.`,
      });
    }

    if (pdfFiles.length === 0) return;

    // Check size limit (25MB)
    const validFiles = [];
    for (const f of pdfFiles) {
      if (f.size > 25 * 1024 * 1024) {
        onNotify({
          type: 'error',
          message: `File '${f.name}' exceeds the 25MB maximum size limit.`,
        });
      } else {
        validFiles.push(f);
      }
    }

    setSelectedFiles(validFiles);
  };

  const removeFile = (idx) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);
    setUploadProgress(10);
    setUploadStage('Validating PDF structures & magic bytes...');

    try {
      setUploadProgress(40);
      setUploadStage('Extracting text & cleaning academic formatting...');

      const result = await api.uploadDocuments(selectedFiles, (percent) => {
        setUploadProgress(Math.min(90, Math.max(40, percent)));
      });

      setUploadProgress(95);
      setUploadStage('Generating dense embeddings & saving to ChromaDB...');

      if (result.success) {
        onNotify({
          type: 'success',
          message: `Successfully indexed ${result.uploaded.length} document(s)!`,
        });
        setSelectedFiles([]);
        if (fileInputRef.current) fileInputRef.current.value = '';
        if (onUploadSuccess) onUploadSuccess();
      }

      if (result.errors && result.errors.length > 0) {
        result.errors.forEach((err) => {
          onNotify({
            type: 'error',
            message: err,
          });
        });
      }
    } catch (err) {
      const errorMsg =
        err.response?.data?.message ||
        err.response?.data?.detail ||
        err.message ||
        'Failed to upload documents.';
      onNotify({
        type: 'error',
        message: errorMsg,
      });
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      setUploadStage('');
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-md">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-bold text-white flex items-center">
          <UploadCloud className="w-4 h-4 mr-2 text-indigo-400" />
          Upload Study Material
        </h2>
        <span className="text-[11px] text-slate-400 font-medium">
          Max 25MB • PDF Only
        </span>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all duration-200 ${
          isDragging
            ? 'border-indigo-500 bg-indigo-500/10 scale-[0.99]'
            : 'border-slate-700/70 hover:border-slate-600 bg-slate-950/40 hover:bg-slate-950/60'
        } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          multiple
          onChange={handleFileInputChange}
          className="hidden"
          disabled={isUploading}
        />

        <div className="w-12 h-12 mx-auto mb-3 rounded-full bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
          <UploadCloud className="w-6 h-6" />
        </div>

        <p className="text-sm font-medium text-slate-200">
          <span className="text-indigo-400 font-semibold hover:underline">Click to browse</span> or drag and drop PDFs
        </p>
        <p className="text-xs text-slate-500 mt-1">
          Lecture notes, academic textbooks, syllabi, or research papers
        </p>
      </div>

      {/* Selected Files Staging List */}
      {selectedFiles.length > 0 && !isUploading && (
        <div className="mt-4 space-y-2">
          <div className="text-xs font-semibold text-slate-400 flex items-center justify-between">
            <span>Ready to Index ({selectedFiles.length})</span>
            <button
              onClick={() => setSelectedFiles([])}
              className="text-[11px] text-slate-500 hover:text-slate-300"
            >
              Clear selection
            </button>
          </div>
          <div className="max-h-36 overflow-y-auto space-y-1.5 pr-1">
            {selectedFiles.map((f, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between px-3 py-2 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs"
              >
                <div className="flex items-center space-x-2 truncate">
                  <FileText className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                  <span className="text-slate-200 truncate font-medium">{f.name}</span>
                  <span className="text-slate-500 text-[11px] shrink-0">
                    ({(f.size / (1024 * 1024)).toFixed(2)} MB)
                  </span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(idx);
                  }}
                  className="text-slate-500 hover:text-rose-400 p-0.5 rounded transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>

          <button
            onClick={handleUpload}
            className="w-full mt-3 py-2.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-sky-500 hover:from-indigo-500 hover:to-sky-400 text-white font-semibold text-xs shadow-lg shadow-indigo-600/25 transition-all flex items-center justify-center space-x-2 cursor-pointer"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Process & Ingest {selectedFiles.length} Document(s)</span>
          </button>
        </div>
      )}

      {/* Uploading / Indexing Progress Indicator */}
      {isUploading && (
        <div className="mt-4 p-4 rounded-xl bg-slate-950/60 border border-indigo-500/30">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="font-semibold text-indigo-300 flex items-center">
              <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin text-indigo-400" />
              {uploadStage || 'Indexing documents...'}
            </span>
            <span className="font-mono text-slate-400">{uploadProgress}%</span>
          </div>
          <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-sky-400 transition-all duration-300 rounded-full"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <p className="text-[11px] text-slate-500 mt-2 text-center">
            Extracting text, splitting into semantically rich chunks & generating vector embeddings...
          </p>
        </div>
      )}
    </div>
  );
}
