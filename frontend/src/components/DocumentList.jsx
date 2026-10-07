import React, { useState } from 'react';
import { FileText, Trash2, Layers, Book, Calendar, Loader2, AlertTriangle } from 'lucide-react';
import api from '../services/api';

export default function DocumentList({ documents, totalChunks, isLoading, onDocumentDeleted, onNotify }) {
  const [deletingId, setDeletingId] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);

  const handleDelete = async (docId, filename) => {
    setDeletingId(docId);
    try {
      const res = await api.deleteDocument(docId);
      onNotify({
        type: 'success',
        message: `Deleted '${filename}' and purged ${res.deleted_chunks} vectors from ChromaDB.`,
      });
      setConfirmDeleteId(null);
      if (onDocumentDeleted) onDocumentDeleted();
    } catch (err) {
      const errorMsg =
        err.response?.data?.message ||
        err.response?.data?.detail ||
        err.message ||
        'Failed to delete document.';
      onNotify({
        type: 'error',
        message: errorMsg,
      });
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl backdrop-blur-md flex flex-col h-full">
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800">
        <div>
          <h2 className="text-sm font-bold text-white flex items-center">
            <Book className="w-4 h-4 mr-2 text-indigo-400" />
            Ingested Study Library
          </h2>
          <p className="text-[11px] text-slate-400">
            {documents.length} document{documents.length === 1 ? '' : 's'} • {totalChunks} vector chunks indexed
          </p>
        </div>
      </div>

      {/* Loading state */}
      {isLoading ? (
        <div className="flex-1 flex flex-col items-center justify-center py-10 text-slate-500">
          <Loader2 className="w-6 h-6 animate-spin text-indigo-400 mb-2" />
          <span className="text-xs">Loading study library...</span>
        </div>
      ) : documents.length === 0 ? (
        /* Empty State */
        <div className="flex-1 flex flex-col items-center justify-center py-10 text-center px-4 border border-dashed border-slate-800 rounded-xl bg-slate-950/30">
          <div className="w-12 h-12 rounded-xl bg-slate-800/80 text-slate-500 flex items-center justify-center mb-3">
            <FileText className="w-6 h-6" />
          </div>
          <h3 className="text-xs font-semibold text-slate-300">No Documents Uploaded</h3>
          <p className="text-[11px] text-slate-500 mt-1 max-w-xs">
            Upload course notes, textbook chapters, or question banks above to enable grounded RAG answering.
          </p>
        </div>
      ) : (
        /* Documents Scrollable List */
        <div className="space-y-2.5 overflow-y-auto max-h-[380px] pr-1">
          {documents.map((doc) => {
            const isDeleting = deletingId === doc.document_id;
            const isConfirming = confirmDeleteId === doc.document_id;

            return (
              <div
                key={doc.document_id}
                className="p-3 rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/50 hover:border-slate-600/80 transition-all text-xs"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-start space-x-2.5 min-w-0 flex-1">
                    <div className="w-7 h-7 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center shrink-0 mt-0.5">
                      <FileText className="w-4 h-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <h4 className="font-semibold text-slate-200 truncate" title={doc.filename}>
                        {doc.filename}
                      </h4>
                      <div className="flex flex-wrap items-center gap-2 mt-1.5 text-[11px] text-slate-400">
                        <span className="inline-flex items-center px-1.5 py-0.2 rounded bg-slate-700/60 text-slate-300">
                          {doc.page_count} pages
                        </span>
                        <span className="inline-flex items-center px-1.5 py-0.2 rounded bg-indigo-500/15 text-indigo-300">
                          <Layers className="w-3 h-3 mr-1" />
                          {doc.chunk_count} chunks
                        </span>
                        <span className="text-slate-500">{doc.file_size_formatted}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions / Delete */}
                  <div className="shrink-0">
                    {isConfirming ? (
                      <div className="flex items-center space-x-1 bg-rose-950/80 border border-rose-800 p-1 rounded-lg">
                        <button
                          onClick={() => handleDelete(doc.document_id, doc.filename)}
                          disabled={isDeleting}
                          className="px-2 py-0.5 rounded bg-rose-600 hover:bg-rose-500 text-white text-[10px] font-semibold transition-colors"
                        >
                          {isDeleting ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Confirm'}
                        </button>
                        <button
                          onClick={() => setConfirmDeleteId(null)}
                          className="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px]"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setConfirmDeleteId(doc.document_id)}
                        className="text-slate-500 hover:text-rose-400 p-1.5 rounded-lg hover:bg-slate-700/50 transition-colors"
                        title="Delete document and purge vectors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
