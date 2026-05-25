"""知识库问答 API — 流式 + 同步"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services.rag_service import ask_sync, ask_stream

router = APIRouter(prefix="/api/knowledge-bases", tags=["知识库问答"])


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str
    sources: list


@router.post("/{kb_id}/qa", response_model=AnswerResponse)
async def ask_question(kb_id: str, req: QuestionRequest):
    """同步问答 — 完整回答一次性返回"""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")
    try:
        result = await ask_sync(kb_id, req.question.strip())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")


@router.post("/{kb_id}/qa/stream")
async def ask_question_stream(kb_id: str, req: QuestionRequest):
    """流式问答 — SSE 逐字返回"""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="问题不能为空")

    async def generate():
        try:
            async for text in ask_stream(kb_id, req.question.strip()):
                yield text
        except Exception as e:
            yield f"\n\n[错误: {str(e)}]"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")
