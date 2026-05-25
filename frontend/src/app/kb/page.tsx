"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { getKB, listDocs, uploadDoc, deleteDoc, askQuestion, KnowledgeBase, Document } from "@/lib/api";

function KBDetailInner() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const kbId = searchParams.get("id") || "";

  const [kb, setKb] = useState<KnowledgeBase | null>(null);
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  // 聊天状态
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState<Array<{ role: "user" | "bot"; text: string; sources?: Array<{ id: string; content: string }> }>>([]);
  const [asking, setAsking] = useState(false);

  const loadData = useCallback(async () => {
    if (!kbId) return;
    try {
      const [kbData, docsData] = await Promise.all([getKB(kbId), listDocs(kbId)]);
      setKb(kbData);
      setDocs(docsData);
    } catch {
      toast.error("加载知识库失败");
    } finally {
      setLoading(false);
    }
  }, [kbId]);

  useEffect(() => { loadData(); }, [loadData]);

  // 自动刷新文档状态
  useEffect(() => {
    const hasProcessing = docs.some((d) => d.status === "pending" || d.status === "processing");
    if (!hasProcessing) return;
    const timer = setInterval(async () => {
      try {
        const fresh = await listDocs(kbId);
        setDocs(fresh);
        const stillProcessing = fresh.some((d) => d.status === "pending" || d.status === "processing");
        if (!stillProcessing) clearInterval(timer);
      } catch { /* ignore */ }
    }, 2000);
    return () => clearInterval(timer);
  }, [docs, kbId]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await uploadDoc(kbId, file);
      toast.success(`「${file.name}」上传成功，正在处理...`);
      loadData();
    } catch (err: any) {
      toast.error(err.message || "上传失败");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDoc = async (docId: string, filename: string) => {
    if (!confirm(`确定删除「${filename}」？`)) return;
    await deleteDoc(kbId, docId);
    toast.success("已删除");
    loadData();
  };

  const handleAsk = async () => {
    if (!question.trim()) return;
    const q = question.trim();
    setChat((prev) => [...prev, { role: "user", text: q }]);
    setQuestion("");
    setAsking(true);
    try {
      // 使用流式问答
      const url = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/knowledge-bases/${kbId}/qa/stream`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      if (!res.ok) throw new Error("请求失败");
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let answer = "";
      setChat((prev) => [...prev, { role: "bot", text: "" }]);
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          answer += decoder.decode(value, { stream: true });
          setChat((prev) => {
            const copy = [...prev];
            copy[copy.length - 1] = { role: "bot", text: answer };
            return copy;
          });
        }
      }
    } catch {
      setChat((prev) => [...prev, { role: "bot", text: "抱歉，问答请求失败。请检查后端和 AI API 配置。" }]);
    } finally {
      setAsking(false);
    }
  };

  if (!kbId) {
    return (
      <div className="max-w-2xl mx-auto p-6 text-center text-zinc-400 mt-20">
        <p>未指定知识库 ID，请从首页进入</p>
      </div>
    );
  }

  if (loading) {
    return <p className="text-zinc-400 text-center py-20">加载中...</p>;
  }

  return (
    <div className="flex-1 flex max-w-6xl mx-auto w-full p-6 gap-6 h-[calc(100vh-64px)]">
      {/* 左侧：文档管理 */}
      <div className="w-80 shrink-0 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-bold text-lg">{kb?.name}</h2>
            <p className="text-xs text-zinc-500">{docs.length} 个文档 · {kb?.chunk_count} 个片段</p>
          </div>
          <Button variant="outline" size="sm" onClick={() => router.push("/")}>← 返回</Button>
        </div>
        <Separator />
        <div>
          <label className={`inline-flex items-center justify-center rounded-md text-sm font-medium h-10 px-4 border cursor-pointer w-full ${uploading ? "opacity-50 pointer-events-none" : "hover:bg-zinc-100"}`}>
            {uploading ? "上传中..." : "📎 上传文档"}
            <input type="file" className="hidden" accept=".pdf,.txt,.md,.docx,.html"
              onChange={handleUpload} disabled={uploading} />
          </label>
          <p className="text-xs text-zinc-400 mt-1">支持 PDF / TXT / MD / DOCX / HTML</p>
        </div>
        <ScrollArea className="flex-1">
          <div className="space-y-2">
            {docs.map((doc) => (
              <Card key={doc.id} className="text-sm">
                <CardContent className="p-3 flex items-center justify-between">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{doc.filename}</p>
                    <span className={`text-xs ${
                      doc.status === "ready" ? "text-green-500" :
                      doc.status === "error" ? "text-red-400" : "text-amber-500"
                    }`}>
                      {doc.status === "ready" ? `✓ ${doc.chunk_count} 片段` :
                       doc.status === "error" ? `✗ ${doc.error_message || "失败"}` :
                       doc.status === "processing" ? "处理中..." : "等待中"}
                    </span>
                  </div>
                  <button className="text-xs text-red-400 hover:text-red-600 shrink-0 ml-2"
                    onClick={() => handleDeleteDoc(doc.id, doc.filename)}>
                    删除
                  </button>
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* 右侧：问答面板 */}
      <div className="flex-1 flex flex-col border rounded-lg bg-white">
        <CardHeader className="pb-2 shrink-0">
          <CardTitle className="text-lg">💬 AI 问答</CardTitle>
        </CardHeader>
        <Separator />
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {chat.length === 0 && (
              <p className="text-zinc-400 text-center py-10">
                上传文档后，在此向 AI 提问文档内容
              </p>
            )}
            {chat.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className={`max-w-[80%] rounded-lg px-4 py-2 text-sm whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-zinc-900 text-white"
                    : "bg-zinc-100 text-zinc-900"
                }`}>
                  {msg.text || (asking && msg.role === "bot" ? "思考中..." : "")}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
        <Separator />
        <div className="p-4 flex gap-2 shrink-0">
          <Textarea
            placeholder="输入问题..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleAsk();
              }
            }}
            rows={2}
            disabled={asking || docs.length === 0}
          />
          <Button onClick={handleAsk} disabled={asking || !question.trim()} className="self-end">
            {asking ? "..." : "发送"}
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function KBDetailPage() {
  return (
    <Suspense fallback={<p className="text-center py-20 text-zinc-400">加载中...</p>}>
      <KBDetailInner />
    </Suspense>
  );
}
