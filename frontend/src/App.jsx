import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import UploadCard from './components/UploadCard';
import DocumentList from './components/DocumentList';
import ChatArea from './components/ChatArea';
import Toast from './components/Toast';
import api from './services/api';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [totalChunks, setTotalChunks] = useState(0);
  const [systemHealth, setSystemHealth] = useState(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((toast) => {
    const id = Date.now() + Math.random().toString(36).substr(2, 4);
    setToasts((prev) => [...prev, { id, ...toast }]);

    // Auto-dismiss after 5s
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const dismissToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const loadHealth = useCallback(async () => {
    setIsCheckingHealth(true);
    try {
      const data = await api.getHealth();
      setSystemHealth(data);
      setTotalChunks(data.total_chunks || 0);
    } catch (err) {
      setSystemHealth({ status: 'offline', llm_provider: 'unknown', embedding_provider: 'unknown' });
      addToast({
        type: 'error',
        title: 'Backend Connection Error',
        message: 'Could not connect to FastAPI backend server. Ensure backend is running on port 8000.',
      });
    } finally {
      setIsCheckingHealth(false);
    }
  }, [addToast]);

  const loadDocuments = useCallback(async () => {
    setIsLoadingDocs(true);
    try {
      const data = await api.getDocuments();
      setDocuments(data.documents || []);
      setTotalChunks(data.total_chunks || 0);
    } catch (err) {
      // Error handled by health check
    } finally {
      setIsLoadingDocs(false);
    }
  }, []);

  useEffect(() => {
    loadHealth();
    loadDocuments();
  }, [loadHealth, loadDocuments]);

  const handleDocumentChange = () => {
    loadDocuments();
    loadHealth();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navbar */}
      <Header
        systemHealth={systemHealth}
        isCheckingHealth={isCheckingHealth}
        onRefreshHealth={() => {
          loadHealth();
          loadDocuments();
        }}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column: Upload & Ingested Document Management */}
          <div className="lg:col-span-5 space-y-6 flex flex-col">
            <UploadCard
              onUploadSuccess={handleDocumentChange}
              onNotify={addToast}
            />

            <div className="flex-1">
              <DocumentList
                documents={documents}
                totalChunks={totalChunks}
                isLoading={isLoadingDocs}
                onDocumentDeleted={handleDocumentChange}
                onNotify={addToast}
              />
            </div>
          </div>

          {/* Right Column: Interactive RAG Chat Session */}
          <div className="lg:col-span-7">
            <ChatArea
              documentCount={documents.length}
              onNotify={addToast}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col items-center gap-2">
          <span>
            Academic Question Answering System Using RAG &bull; Grounded responses with source citations
          </span>
          <span role="note" className="max-w-4xl text-amber-300">
            This system may produce inaccurate or hallucinated answers. Always verify against the source excerpts shown. Do not use for legal or medical advice without expert review.
          </span>
        </div>
      </footer>

      {/* Notification Toast Stack */}
      <Toast toasts={toasts} onDismiss={dismissToast} />
    </div>
  );
}
