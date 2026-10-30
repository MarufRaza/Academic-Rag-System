import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Copy, Check, ExternalLink } from 'lucide-react';

export default function SourceCitations({ sources }) {
  const [expandedIndices, setExpandedIndices] = useState({});
  const [copiedSnippetIndex, setCopiedSnippetIndex] = useState(null);

  const citationSources = Array.isArray(sources) ? sources : [];

  const toggleExpand = (idx) => {
    setExpandedIndices((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const copySnippet = (snippet, idx) => {
    navigator.clipboard.writeText(snippet);
    setCopiedSnippetIndex(idx);
    setTimeout(() => setCopiedSnippetIndex(null), 2000);
  };

  return (
    <div className="mt-4 pt-3 border-t border-slate-700/60">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center">
          <FileText className="w-3.5 h-3.5 mr-1.5 text-indigo-400" />
          Sources ({citationSources.length})
        </span>
        <span className="text-[11px] text-slate-500">
          Retrieved excerpts for verification
        </span>
      </div>

      <div className="space-y-2">
        {citationSources.length === 0 ? (
          <p className="rounded-lg bg-slate-900/70 border border-slate-800 px-3 py-2 text-xs text-slate-400">
            No supporting sources found in the documents
          </p>
        ) : citationSources.map((source, idx) => {
          const isExpanded = !!expandedIndices[idx];
          const hasCopied = copiedSnippetIndex === idx;
          const scorePercent = source.score ? Math.round(source.score * 100) : null;

          return (
            <div
              key={idx}
              className="rounded-lg bg-slate-900/90 border border-slate-800 hover:border-slate-700 transition-colors overflow-hidden"
            >
              {/* Source Header Button */}
              <div
                onClick={() => toggleExpand(idx)}
                className="w-full px-3 py-2 flex items-center justify-between text-left cursor-pointer hover:bg-slate-800/50 transition-colors"
              >
                <div className="flex items-center space-x-2 min-w-0">
                  <div className="w-6 h-6 rounded bg-indigo-500/10 text-indigo-400 flex items-center justify-center shrink-0">
                    <FileText className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-xs font-medium text-slate-200 truncate">
                    {source.document}
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-[11px] font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 shrink-0">
                    Page {source.page}
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-[11px] font-medium bg-slate-700/70 text-slate-300 border border-slate-600/50 shrink-0">
                    Chunk {source.chunk_index}
                  </span>
                  {scorePercent !== null && (
                    <span className="px-1.5 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shrink-0 hidden sm:inline">
                      {scorePercent}% match
                    </span>
                  )}
                </div>

                <div className="flex items-center space-x-1 ml-2 shrink-0">
                  <span className="text-[11px] text-slate-400">
                    {isExpanded ? 'Hide excerpt' : 'View excerpt'}
                  </span>
                  {isExpanded ? (
                    <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                  )}
                </div>
              </div>

              {/* Collapsible Snippet Content */}
              {isExpanded && (
                <div className="px-3 pb-3 pt-1 border-t border-slate-800/80 bg-slate-950/60">
                  <div className="flex items-center justify-between mb-1.5 text-[11px] text-slate-400">
                    <span className="italic">Cited Academic Text Excerpt:</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        copySnippet(source.content, idx);
                      }}
                      className="inline-flex items-center space-x-1 text-slate-400 hover:text-white transition-colors"
                      title="Copy snippet"
                    >
                      {hasCopied ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-400" />
                          <span className="text-emerald-400">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy snippet</span>
                        </>
                      )}
                    </button>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-mono bg-slate-900/80 p-2.5 rounded border border-slate-800/80 select-text whitespace-pre-wrap">
                    {source.content}
                  </p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
