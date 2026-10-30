import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes timeout for LLM / large PDF indexing
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Health & System Info
  async getHealth() {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // Document Management
  async getDocuments() {
    const res = await apiClient.get('/documents');
    return res.data;
  },

  async uploadDocuments(files, onUploadProgress) {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    const res = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onUploadProgress(percentCompleted);
        }
      },
    });
    return res.data;
  },

  async deleteDocument(documentId) {
    const res = await apiClient.delete(`/documents/${documentId}`);
    return res.data;
  },

  // Chat / RAG (Standard blocking)
  async askQuestion(question, chatHistory = []) {
    const payload = {
      question: question.trim(),
      chat_history: chatHistory.map((msg) => ({
        role: msg.role,
        content: msg.content,
      })),
    };

    const res = await apiClient.post('/chat', payload);
    return res.data;
  },

  // Real-time Token Streaming via SSE
  async askQuestionStream(question, chatHistory = [], { onToken, onSources, onStandalone, onError }) {
    const payload = {
      question: question.trim(),
      chat_history: chatHistory.map((msg) => ({
        role: msg.role,
        content: msg.content,
      })),
    };

    const response = await fetch(`${API_BASE_URL}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.message || `Server error ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          let data;
          try {
            data = JSON.parse(line.slice(6));
          } catch {
            continue;
          }

          if (data.type === 'error') {
            const streamError = new Error(data.message || 'LLM service unavailable.');
            streamError.name = 'StreamResponseError';
            if (onError) onError(streamError.message);
            throw streamError;
          }
          if (data.type === 'token' && onToken) onToken(data.content);
          if (data.type === 'sources' && onSources) onSources(data.sources);
          if (data.type === 'standalone' && onStandalone) onStandalone(data.question);
        }
      }
    }
  },
};

export default api;
