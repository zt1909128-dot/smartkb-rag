"""RAG 问答引擎 — 检索 + Claude 生成 + 流式输出"""

from typing import AsyncGenerator, List, Dict
from anthropic import AsyncAnthropic

from app.config import settings
from app.services.embedding_service import embed_single
from app.services.vector_store import search_similar


SYSTEM_PROMPT = """你是一个智能知识库助手，基于用户上传的文档内容回答问题。

规则：
1. 只基于提供的文档片段回答，不要编造信息
2. 如果文档中没有相关信息，诚实地说"文档中未找到相关内容"
3. 回答时引用具体的文档片段作为依据
4. 回答简洁清晰，使用中文
5. 如果问题超出文档范围，礼貌地说明"""


def retrieve_context(kb_id: str, question: str, top_k: int = 5) -> List[Dict]:
    """检索与问题相关的文档片段"""
    query_embedding = embed_single(question)
    chunks = search_similar(kb_id, query_embedding, top_k)
    return chunks


def build_prompt(question: str, chunks: List[Dict]) -> str:
    """构建带上下文的 prompt"""
    if not chunks:
        return question

    contexts = []
    for i, chunk in enumerate(chunks, 1):
        contexts.append(f"[片段 {i}] (来源: {chunk['doc_id']})\n{chunk['content']}")

    context_text = "\n\n---\n\n".join(contexts)

    return f"""以下是知识库中与问题相关的文档片段：

{context_text}

---
基于以上文档片段，请回答用户的问题。

用户问题：{question}

回答："""


async def ask_stream(kb_id: str, question: str) -> AsyncGenerator[str, None]:
    """流式 RAG 问答，逐字返回"""
    chunks = retrieve_context(kb_id, question)
    prompt = build_prompt(question, chunks)

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async with client.messages.stream(
        model=settings.llm_model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def ask_sync(kb_id: str, question: str) -> Dict:
    """同步 RAG 问答，返回完整结果"""
    chunks = retrieve_context(kb_id, question)
    prompt = build_prompt(question, chunks)

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    message = await client.messages.create(
        model=settings.llm_model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "answer": message.content[0].text,
        "sources": [
            {"id": c["id"], "content": c["content"][:200], "doc_id": c["doc_id"]}
            for c in chunks
        ],
    }
