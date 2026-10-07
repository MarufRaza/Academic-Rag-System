import React, { useEffect } from 'react';
import { CheckCircle2, AlertTriangle, AlertCircle, X } from 'lucide-react';

export default function Toast({ toasts, onDismiss }) {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col space-y-2 max-w-md w-full pointer-events-none px-4">
      {toasts.map((toast) => {
        const isSuccess = toast.type === 'success';
        const isWarning = toast.type === 'warning';
        const isError = toast.type === 'error';

        return (
          <div
            key={toast.id}
            className={`pointer-events-auto flex items-start space-x-3 p-3.5 rounded-xl shadow-2xl border backdrop-blur-md transition-all duration-300 transform translate-y-0 ${
              isSuccess
                ? 'bg-emerald-950/90 border-emerald-500/30 text-emerald-200'
                : isWarning
                ? 'bg-amber-950/90 border-amber-500/30 text-amber-200'
                : 'bg-rose-950/90 border-rose-500/30 text-rose-200'
            }`}
          >
            <div className="shrink-0 mt-0.5">
              {isSuccess && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
              {isWarning && <AlertTriangle className="w-4 h-4 text-amber-400" />}
              {isError && <AlertCircle className="w-4 h-4 text-rose-400" />}
            </div>

            <div className="flex-1 text-xs leading-relaxed">
              {toast.title && <p className="font-semibold text-white mb-0.5">{toast.title}</p>}
              <p>{toast.message}</p>
            </div>

            <button
              onClick={() => onDismiss(toast.id)}
              className="shrink-0 text-slate-400 hover:text-white p-0.5 rounded transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
