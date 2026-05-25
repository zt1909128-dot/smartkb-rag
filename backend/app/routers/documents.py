"""文档上传和管理 API"""

import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Document, DocumentStatus, KnowledgeBase
from app.services.database import get_db
from app.services.document_processor import process_document, SUPPORTED_TYPES
from app.services.embedding_service import embed_texts
from app.services.vector_store import add_chunks, delete_document

router = APIRouter(prefix="/api/knowledge-bases", tags=["文档管理"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")


class DocResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    created_at: str
    error_message: str = ""

    model_config = {"from_attributes": True}


def _process_document_background(doc_id: str, kb_id: str, filepath: str, filename: str, db_session_factory):
    """后台处理文档：分块 → 嵌入 → 存向量库"""
    db = db_session_factory()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return

        doc.status = DocumentStatus.PROCESSING
        db.commit()

        chunks = process_document(filepath, filename)
        if not chunks:
            doc.status = DocumentStatus.READY
            doc.chunk_count = 0
            db.commit()
            return

        # 批量嵌入
        texts = [c["content"] for c in chunks]
        embeddings = embed_texts(texts)

        # 存入向量库
        add_chunks(kb_id, doc_id, chunks, embeddings)

        doc.status = DocumentStatus.READY
        doc.chunk_count = len(chunks)
        db.commit()

    except Exception as e:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = DocumentStatus.ERROR
            doc.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.get("/{kb_id}/documents", response_model=List[DocResponse])
def list_documents(kb_id: str, db: Session = Depends(get_db)):
    """列出知识库中所有文档"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    docs = db.query(Document).filter(Document.knowledge_base_id == kb_id).order_by(Document.created_at.desc()).all()
    return [DocResponse(
        id=d.id,
        filename=d.filename,
        file_type=d.file_type,
        file_size=d.file_size,
        status=d.status.value if d.status else "pending",
        chunk_count=d.chunk_count,
        created_at=d.created_at.isoformat() if d.created_at else "",
        error_message=d.error_message or "",
    ) for d in docs]


@router.post("/{kb_id}/documents", response_model=DocResponse, status_code=201)
async def upload_document(
    kb_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """上传文档到知识库"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")

    # 校验文件类型
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in SUPPORTED_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}。支持: {', '.join(SUPPORTED_TYPES.keys())}")

    # 校验文件大小
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > settings.max_upload_size_mb:
        raise HTTPException(status_code=400, detail=f"文件超过最大限制 {settings.max_upload_size_mb}MB")

    # 保存文件
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(UPLOAD_DIR, safe_name)
    with open(filepath, "wb") as f:
        f.write(content)

    # 创建文档记录
    doc = Document(
        knowledge_base_id=kb_id,
        filename=file.filename or "unknown",
        file_type=SUPPORTED_TYPES[ext],
        file_size=len(content),
        status=DocumentStatus.PENDING,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 后台处理
    from app.services.database import SessionLocal
    background_tasks.add_task(_process_document_background, doc.id, kb_id, filepath, file.filename, SessionLocal)

    return DocResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        status=doc.status.value,
        chunk_count=0,
        created_at=doc.created_at.isoformat() if doc.created_at else "",
    )


@router.delete("/{kb_id}/documents/{doc_id}", status_code=204)
def remove_document(kb_id: str, doc_id: str, db: Session = Depends(get_db)):
    """删除文档及关联向量"""
    doc = db.query(Document).filter(
        Document.id == doc_id, Document.knowledge_base_id == kb_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    db.delete(doc)
    db.commit()
    delete_document(kb_id, doc_id)
