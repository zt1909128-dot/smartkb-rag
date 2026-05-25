"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { listKBs, createKB, deleteKB, KnowledgeBase } from "@/lib/api";

export default function HomePage() {
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    try {
      setKbs(await listKBs());
    } catch {
      toast.error("加载失败，请确认后端已启动");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setCreating(true);
    try {
      await createKB(name.trim(), desc.trim());
      toast.success("知识库创建成功");
      setShowCreate(false);
      setName("");
      setDesc("");
      load();
    } catch {
      toast.error("创建失败");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string, kbName: string) => {
    if (!confirm(`确定删除「${kbName}」？`)) return;
    await deleteKB(id);
    toast.success("已删除");
    load();
  };

  return (
    <div className="max-w-4xl mx-auto w-full p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold">我的知识库</h2>
          <p className="text-sm text-zinc-500 mt-1">创建知识库，上传文档，AI 智能问答</p>
        </div>
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogTrigger><Button>新建知识库</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>新建知识库</DialogTitle></DialogHeader>
            <div className="space-y-4 mt-2">
              <Input placeholder="名称，如：产品手册" value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreate()} />
              <Input placeholder="描述（可选）" value={desc}
                onChange={(e) => setDesc(e.target.value)} />
              <Button onClick={handleCreate} disabled={creating} className="w-full">
                {creating ? "创建中..." : "创建"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <p className="text-zinc-400 text-center py-20">加载中...</p>
      ) : kbs.length === 0 ? (
        <div className="text-center py-20 text-zinc-400">
          <p className="text-4xl mb-4">📚</p>
          <p>还没有知识库，点击上方按钮创建第一个</p>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {kbs.map((kb) => (
            <Card key={kb.id} className="hover:shadow-md transition-shadow">
              <Link href={`/kb?id=${kb.id}`}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-lg">📄 {kb.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  {kb.description && <p className="text-sm text-zinc-500 mb-2">{kb.description}</p>}
                  <div className="flex gap-4 text-xs text-zinc-400">
                    <span>{kb.document_count} 个文档</span>
                    <span>{kb.chunk_count} 个片段</span>
                  </div>
                </CardContent>
              </Link>
              <div className="px-6 pb-4">
                <button className="text-xs text-red-400 hover:text-red-600"
                  onClick={(e) => { e.preventDefault(); handleDelete(kb.id, kb.name); }}>
                  删除
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
