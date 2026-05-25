"""向量存储 — numpy 内存检索 + JSON 持久化（零外部依赖）"""

import os
import json
import numpy as np
from typing import List, Dict

PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "vectors")


def _get_store_path(kb_id: str) -> str:
    os.makedirs(PERSIST_DIR, exist_ok=True)
    return os.path.join(PERSIST_DIR, f"kb_{kb_id}.json")


def _load_store(kb_id: str) -> dict:
    path = _get_store_path(kb_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"chunks": [], "embeddings": [], "metadata": []}


def _save_store(kb_id: str, store: dict):
    path = _get_store_path(kb_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False)


def add_chunks(kb_id: str, doc_id: str, chunks: List[Dict[str, str]], embeddings: List[List[float]]) -> str:
    """添加文档块及嵌入"""
    store = _load_store(kb_id)
    for i, chunk in enumerate(chunks):
        store["chunks"].append(chunk["content"])
        store["embeddings"].append(embeddings[i])
        store["metadata"].append({"doc_id": doc_id, "chunk_index": chunk["index"]})
    _save_store(kb_id, store)
    return doc_id


def search_similar(kb_id: str, query_embedding: List[float], top_k: int = 5) -> List[Dict]:
    """余弦相似度检索"""
    store = _load_store(kb_id)
    if not store["embeddings"]:
        return []

    query_vec = np.array(query_embedding)
    doc_vecs = np.array(store["embeddings"])

    # 归一化后点积 = 余弦相似度
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-10)
    doc_norms = doc_vecs / (np.linalg.norm(doc_vecs, axis=1, keepdims=True) + 1e-10)
    scores = np.dot(doc_norms, query_norm)

    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in top_indices:
        results.append({
            "id": f"{store['metadata'][idx]['doc_id']}_{store['metadata'][idx]['chunk_index']}",
            "content": store["chunks"][idx],
            "doc_id": store["metadata"][idx]["doc_id"],
            "chunk_index": store["metadata"][idx]["chunk_index"],
            "score": float(scores[idx]),
        })
    return results


def delete_document(kb_id: str, doc_id: str):
    """删除文档的所有块"""
    store = _load_store(kb_id)
    keep = [i for i, m in enumerate(store["metadata"]) if m["doc_id"] != doc_id]
    store["chunks"] = [store["chunks"][i] for i in keep]
    store["embeddings"] = [store["embeddings"][i] for i in keep]
    store["metadata"] = [store["metadata"][i] for i in keep]
    _save_store(kb_id, store)


def delete_knowledge_base(kb_id: str):
    """删除知识库向量文件"""
    path = _get_store_path(kb_id)
    if os.path.exists(path):
        os.remove(path)


def count_chunks(kb_id: str) -> int:
    """统计块数"""
    store = _load_store(kb_id)
    return len(store["chunks"])
