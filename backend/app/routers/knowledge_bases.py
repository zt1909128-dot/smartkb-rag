"""知识库管理 API — CRUD"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import KnowledgeBase
from app.services.database import get_db
from app.services.vector_store import delete_knowledge_base, count_chunks

router = APIRouter(prefix="/api/knowledge-bases", tags=["知识库管理"])


class KBCreate(BaseModel):
    name: str
    description: str = ""


class KBResponse(BaseModel):
    id: str
    name: str
    description: str
    document_count: int = 0
    chunk_count: int = 0
    created_at: str

    model_config = {"from_attributes": True}


@router.get("", response_model=List[KBResponse])
def list_kbs(db: Session = Depends(get_db)):
    """列出所有知识库"""
    kbs = db.query(KnowledgeBase).order_by(KnowledgeBase.created_at.desc()).all()
    results = []
    for kb in kbs:
        doc_count = len(kb.documents)
        chunks = count_chunks(kb.id)
        results.append(KBResponse(
            id=kb.id,
            name=kb.name,
            description=kb.description or "",
            document_count=doc_count,
            chunk_count=chunks,
            created_at=kb.created_at.isoformat() if kb.created_at else "",
        ))
    return results


@router.post("", response_model=KBResponse, status_code=201)
def create_kb(data: KBCreate, db: Session = Depends(get_db)):
    """创建新知识库"""
    kb = KnowledgeBase(name=data.name, description=data.description)
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description or "",
        created_at=kb.created_at.isoformat() if kb.created_at else "",
    )


@router.get("/{kb_id}", response_model=KBResponse)
def get_kb(kb_id: str, db: Session = Depends(get_db)):
    """获取知识库详情"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return KBResponse(
        id=kb.id,
        name=kb.name,
        description=kb.description or "",
        document_count=len(kb.documents),
        chunk_count=count_chunks(kb.id),
        created_at=kb.created_at.isoformat() if kb.created_at else "",
    )


@router.delete("/{kb_id}", status_code=204)
def delete_kb(kb_id: str, db: Session = Depends(get_db)):
    """删除知识库及所有关联数据"""
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    db.delete(kb)
    db.commit()
    delete_knowledge_base(kb_id)
