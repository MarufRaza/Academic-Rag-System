import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { User, Sparkles, Copy, Check, GitCommit } from 'lucide-react';
import SourceCitations from './SourceCitations';

export default function ChatMessage({ message }) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const copyContent = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-4 group">
        <div className="max-w-2xl flex items-start space-x-3 flex-row-reverse space-x-reverse">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center text-white shrink-0 shadow-md shadow-indigo-600/20">
            <User className="w-4 h-4" />
          </div>
          <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-none px-4 py-3 shadow-md">
            <p className="text-sm whitespace-pre-wrap leading-relaxed">
              {message.content}
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start mb-6 group">
      <div className="w-full max-w-3xl flex items-start space-x-3.5">
        {/* Assistant Avatar */}
        <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-indigo-500 to-sky-400 flex items-center justify-center text-white shrink-0 shadow-md shadow-indigo-500/20 mt-1">
          <Sparkles className="w-4 h-4" />
        </div>

        {/* Message Card */}
        <div className="flex-1 bg-slate-800/90 border border-slate-700/70 rounded-2xl rounded-tl-none p-5 shadow-lg backdrop-blur-sm text-slate-100">
          {/* Header info & rephrase notice */}
          <div className="flex items-center justify-between mb-2 pb-2 border-b border-slate-700/40">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-indigo-300">
                Academic AI Assistant
              </span>
              {message.standalone_question && (
                <span
                  title={`Condensed from conversation history: "${message.standalone_question}"`}
                  className="inline-flex items-center text-[10px] px-2 py-0.5 rounded-full bg-slate-700/70 text-slate-300 border border-slate-600/50"
                >
                  <GitCommit className="w-3 h-3 mr-1 text-sky-400" />
                  Context-aware Query
                </span>
              )}
            </div>

            {/* Copy button */}
            <button
              onClick={copyContent}
              className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-700/50 transition-colors inline-flex items-center space-x-1 text-xs"
              title="Copy answer"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="text-[11px] text-emerald-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span className="text-[11px] hidden sm:inline">Copy</span>
                </>
              )}
            </button>
          </div>

          {/* Formatted Markdown Content */}
          <div className="prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed space-y-3">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 leading-relaxed text-sm text-slate-200">{children}</p>,
                ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1 text-sm text-slate-200">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1 text-sm text-slate-200">{children}</ol>,
                li: ({ children }) => <li className="text-sm text-slate-200">{children}</li>,
                h1: ({ children }) => <h1 className="text-base font-bold text-white mt-3 mb-1">{children}</h1>,
                h2: ({ children }) => <h2 className="text-sm font-bold text-white mt-2.5 mb-1">{children}</h2>,
                h3: ({ children }) => <h3 className="text-xs font-bold text-white mt-2 mb-1">{children}</h3>,
                code: ({ node, inline, children, ...props }) => {
                  return inline ? (
                    <code className="bg-slate-900 text-indigo-300 px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
                      {children}
                    </code>
                  ) : (
                    <pre className="bg-slate-900/90 text-slate-200 p-3 rounded-lg overflow-x-auto text-xs font-mono border border-slate-700/60 my-2">
                      <code>{children}</code>
                    </pre>
                  );
                },
                strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Sources Section */}
          {message.sources && message.sources.length > 0 && (
            <SourceCitations sources={message.sources} />
          )}
        </div>
      </div>
    </div>
  );
}
