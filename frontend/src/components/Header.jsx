import React from 'react';
import { BookOpen, Cpu, Database, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

export default function Header({ systemHealth, isCheckingHealth, onRefreshHealth }) {
  const isOnline = systemHealth?.status === 'ok';

  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        {/* Brand & Subtitle */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-sky-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 text-white">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold tracking-tight text-white">
                Academic AI Assistant
              </h1>
              <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                RAG 1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Ask questions from your study materials using RAG
            </p>
          </div>
        </div>

        {/* System Status Badges */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {/* Health indicator */}
          <div
            className={`inline-flex items-center px-2.5 py-1 rounded-lg border font-medium ${
              isOnline
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full mr-1.5 ${
                isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'
              }`}
            />
            {isOnline ? 'Backend Online' : 'Backend Offline'}
          </div>

          {/* Active LLM Provider */}
          {systemHealth && (
            <div className="inline-flex items-center px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300">
              <Cpu className="w-3.5 h-3.5 mr-1.5 text-indigo-400" />
              <span>LLM: <strong className="text-white capitalize">{systemHealth.llm_provider}</strong></span>
              <span className="ml-1 text-[11px] text-slate-400">({systemHealth.llm_model})</span>
            </div>
          )}

          {/* Active Embedding Provider */}
          {systemHealth && (
            <div className="inline-flex items-center px-2.5 py-1 rounded-lg bg-slate-800/80 border border-slate-700/60 text-slate-300">
              <Database className="w-3.5 h-3.5 mr-1.5 text-sky-400" />
              <span>Embeddings: <strong className="text-white capitalize">{systemHealth.embedding_provider}</strong></span>
              <span className="ml-1 text-[11px] text-slate-400">
                ({systemHealth.total_chunks || 0} chunks)
              </span>
            </div>
          )}

          {/* Refresh Button */}
          <button
            onClick={onRefreshHealth}
            disabled={isCheckingHealth}
            title="Refresh system status"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isCheckingHealth ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
}
