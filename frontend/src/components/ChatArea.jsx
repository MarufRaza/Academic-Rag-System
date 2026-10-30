import React, { useState, useRef, useEffect } from 'react';
import { Send, Trash2, Sparkles, HelpCircle, Loader2, ArrowDown, BookOpen } from 'lucide-react';
import ChatMessage from './ChatMessage';
import api from '../services/api';

const EXAMPLE_QUESTIONS = [
  'What is normalization?',
  'Explain the OSI model.',
  'What is the difference between TCP and UDP?',
  'Explain the advantages of cloud computing.',
];

export default function ChatArea({ documentCount, onNotify }) {
  const [messages, setMessages] = useState([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (queryToSend) => {
    const question = (queryToSend || inputQuery).trim();
    if (!question || isLoading) return;

    if (documentCount === 0) {
      onNotify({
        type: 'warning',
        message: 'No study materials uploaded yet! Please upload at least one PDF first.',
      });
      return;
    }

    const userMsg = {
      role: 'user',
      content: question,
    };

    const initialAssistantMsg = {
      role: 'assistant',
      content: '',
      sources: [],
      standalone_question: null,
    };

    const newMessages = [...messages, userMsg];
    setMessages([...newMessages, initialAssistantMsg]);
    setInputQuery('');
    setIsLoading(true);

    let streamedContent = '';
    let streamedSources = [];
    let standaloneQuestion = null;

    try {
      await api.askQuestionStream(question, messages, {
        onToken: (token) => {
          streamedContent += token;
          setMessages((prev) => {
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
              updated[lastIdx] = {
                ...updated[lastIdx],
                content: streamedContent,
              };
            }
            return updated;
          });
        },
        onSources: (sources) => {
          streamedSources = sources;
          setMessages((prev) => {
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
              updated[lastIdx] = {
                ...updated[lastIdx],
                sources: streamedSources,
              };
            }
            return updated;
          });
        },
        onStandalone: (standalone) => {
          standaloneQuestion = standalone;
          setMessages((prev) => {
            const updated = [...prev];
            const lastIdx = updated.length - 1;
            if (lastIdx >= 0 && updated[lastIdx].role === 'assistant') {
              updated[lastIdx] = {
                ...updated[lastIdx],
                standalone_question: standaloneQuestion,
              };
            }
            return updated;
          });
        },
      });
    } catch (err) {
      if (err.name === 'StreamResponseError') {
        onNotify({
          type: 'error',
          message: err.message,
        });
        setMessages([
          ...newMessages,
          {
            role: 'assistant',
            content: err.message,
            sources: [],
          },
        ]);
      } else {
        // Fallback to standard blocking API call if the stream itself failed
        try {
          const response = await api.askQuestion(question, messages);
          setMessages([
            ...newMessages,
            {
              role: 'assistant',
              content: response.answer,
              sources: response.sources || [],
              standalone_question: response.standalone_question,
            },
          ]);
        } catch (fallbackErr) {
          const errorMsg =
            fallbackErr.response?.data?.message ||
            fallbackErr.response?.data?.detail ||
            fallbackErr.message ||
            err.message ||
            'Error retrieving answer.';

          onNotify({
            type: 'error',
            message: errorMsg,
          });

          setMessages([
            ...newMessages,
            {
              role: 'assistant',
              content: `âš ï¸ **Request Error**: ${errorMsg}`,
              sources: [],
            },
          ]);
        }
      }
    } finally {
      setIsLoading(false);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleClearChat = () => {
    if (messages.length === 0) return;
    setMessages([]);
    onNotify({
      type: 'info',
      message: 'Conversation history cleared.',
    });
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl flex flex-col h-[740px] shadow-2xl backdrop-blur-md overflow-hidden">
      {/* Chat Area Top Bar */}
      <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
        <div className="flex items-center space-x-2">
          <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse" />
          <h2 className="text-sm font-bold text-white tracking-wide">
            Academic Discussion Session
          </h2>
          <span className="text-xs text-slate-500 font-normal">
            ({messages.filter((m) => m.role === 'user').length} queries asked)
          </span>
        </div>

        {messages.length > 0 && (
          <button
            onClick={handleClearChat}
            className="inline-flex items-center space-x-1.5 text-xs text-slate-400 hover:text-rose-400 px-2.5 py-1 rounded-lg hover:bg-slate-800/80 transition-colors"
            title="Clear current conversation"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Chat</span>
          </button>
        )}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.length === 0 ? (
          /* Empty State */
          <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto py-10">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600/30 to-sky-500/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 mb-4 shadow-xl shadow-indigo-500/10">
              <Sparkles className="w-8 h-8" />
            </div>

            <h3 className="text-base font-bold text-white mb-2">
              Ready for Your Academic Questions
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed mb-6">
              Ask anything about your uploaded study notes, lectures, and textbooks.
              Answers use retrieved material and include source citations for you to verify.
            </p>

            {/* Clickable Example Questions */}
            <div className="w-full text-left">
              <p className="text-xs font-semibold text-slate-400 mb-2.5 flex items-center">
                <HelpCircle className="w-3.5 h-3.5 mr-1.5 text-indigo-400" />
                Click an example to try out:
              </p>
              <div className="grid grid-cols-1 gap-2">
                {EXAMPLE_QUESTIONS.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(q)}
                    className="p-3 text-left rounded-xl bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-indigo-500/50 text-xs text-slate-300 hover:text-white transition-all duration-150 flex items-center justify-between group cursor-pointer"
                  >
                    <span>{q}</span>
                    <Send className="w-3.5 h-3.5 text-slate-500 group-hover:text-indigo-400 transition-colors shrink-0 ml-2" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          /* Chat Bubbles List */
          <>
            {messages.map((msg, idx) => (
              <ChatMessage key={idx} message={msg} />
            ))}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex justify-start mb-6">
                <div className="flex items-start space-x-3.5 max-w-xl">
                  <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
                    <Loader2 className="w-4 h-4 animate-spin" />
                  </div>
                  <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl rounded-tl-none px-4 py-3 shadow-md">
                    <div className="flex items-center space-x-2 text-xs text-slate-400">
                      <span>Retrieving & synthesizing academic context...</span>
                      <div className="flex space-x-1">
                        <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.3s]" />
                        <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce [animation-delay:-0.15s]" />
                        <span className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-slate-800 bg-slate-950/60">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="relative flex items-end bg-slate-900 border border-slate-700/80 rounded-2xl focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500 transition-all p-2"
        >
          <textarea
            ref={textareaRef}
            rows={1}
            value={inputQuery}
            onChange={(e) => {
              setInputQuery(e.target.value);
              // Auto resize height up to 120px
              e.target.style.height = 'auto';
              e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
            }}
            onKeyDown={handleKeyDown}
            placeholder={
              documentCount === 0
                ? 'Upload a PDF on the left to start asking questions...'
                : 'Ask a question from your study materials (Press Enter to ask, Shift+Enter for newline)...'
            }
            disabled={isLoading}
            className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-xs sm:text-sm px-3 py-2 resize-none focus:outline-none min-h-[38px] max-h-[120px] leading-relaxed"
          />

          <button
            type="submit"
            disabled={!inputQuery.trim() || isLoading}
            className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:hover:bg-indigo-600 text-white transition-colors shrink-0 shadow-md shadow-indigo-600/30 cursor-pointer disabled:cursor-not-allowed"
            title="Submit question"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </form>

        <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2 px-1">
          <span>RAG pipeline: Embed &rarr; Cosine Search (Top-4) &rarr; Prompt Synthesis</span>
          <span>Only facts in uploaded docs are answered</span>
        </div>
      </div>
    </div>
  );
}
