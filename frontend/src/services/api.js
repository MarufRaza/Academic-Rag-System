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

  // Chat / RAG
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
};

export default api;
