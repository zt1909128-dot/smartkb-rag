"""文本嵌入服务 — OpenAI Embeddings"""

from typing import List
from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def embed_texts(texts: List[str]) -> List[List[float]]:
    """批量生成文本嵌入向量"""
    if not texts:
        return []

    client = get_client()
    resp = client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
    )
    return [d.embedding for d in resp.data]


def embed_single(text: str) -> List[float]:
    """单条文本嵌入"""
    return embed_texts([text])[0]
