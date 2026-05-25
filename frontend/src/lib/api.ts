/** 后端 API 客户端 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  document_count: number;
  chunk_count: number;
  created_at: string;
}

export interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  chunk_count: number;
  created_at: string;
  error_message?: string;
}

export interface Answer {
  answer: string;
  sources: Array<{ id: string; content: string; doc_id: string }>;
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `请求失败: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

// 知识库
export const listKBs = () => request<KnowledgeBase[]>("/api/knowledge-bases");
export const getKB = (id: string) => request<KnowledgeBase>(`/api/knowledge-bases/${id}`);
export const createKB = (name: string, description?: string) =>
  request<KnowledgeBase>("/api/knowledge-bases", { method: "POST", body: JSON.stringify({ name, description }) });
export const deleteKB = (id: string) =>
  request<void>(`/api/knowledge-bases/${id}`, { method: "DELETE" });

// 文档
export const listDocs = (kbId: string) => request<Document[]>(`/api/knowledge-bases/${kbId}/documents`);
export const uploadDoc = async (kbId: string, file: File) => {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_URL}/api/knowledge-bases/${kbId}/documents`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "上传失败");
  }
  return res.json() as Promise<Document>;
};
export const deleteDoc = (kbId: string, docId: string) =>
  request<void>(`/api/knowledge-bases/${kbId}/documents/${docId}`, { method: "DELETE" });

// 问答
export const askQuestion = (kbId: string, question: string) =>
  request<Answer>(`/api/knowledge-bases/${kbId}/qa`, { method: "POST", body: JSON.stringify({ question }) });

export function askStreamUrl(kbId: string): string {
  return `${API_URL}/api/knowledge-bases/${kbId}/qa/stream`;
}
