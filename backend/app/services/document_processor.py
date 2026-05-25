"""文档解析和文本分块"""

import os
import re
from pathlib import Path
from typing import List, Dict


# 支持的文件类型
SUPPORTED_TYPES = {
    ".pdf": "pdf",
    ".txt": "txt",
    ".md": "markdown",
    ".docx": "docx",
    ".html": "html",
    ".htm": "html",
}


def read_file_content(filepath: str) -> str:
    """读取不同格式文件的内容，返回纯文本"""
    ext = Path(filepath).suffix.lower()

    if ext == ".txt" or ext == ".md":
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    if ext == ".pdf":
        from pypdf2 import PdfReader
        reader = PdfReader(filepath)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext == ".docx":
        from docx import Document
        doc = Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)

    if ext in (".html", ".htm"):
        from bs4 import BeautifulSoup
        with open(filepath, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            return soup.get_text(separator="\n")

    raise ValueError(f"不支持的文件类型: {ext}")


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Dict[str, str]]:
    """将文本分割为重叠块，每块带索引"""
    chunks = []
    cleaned = re.sub(r"\n{3,}", "\n\n", text.strip())

    if not cleaned:
        return chunks

    # 按段落优先分割
    paragraphs = cleaned.split("\n\n")
    current = ""
    index = 0

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current) + len(para) <= chunk_size:
            current = (current + "\n\n" + para).strip()
        else:
            if current:
                chunks.append({"content": current, "index": index})
                index += 1
            # 如果段落本身超过 chunk_size，按句子再切
            if len(para) > chunk_size:
                sub_chunks = _split_long_paragraph(para, chunk_size)
                for sc in sub_chunks:
                    chunks.append({"content": sc, "index": index})
                    index += 1
                current = ""
            else:
                current = para

    if current:
        chunks.append({"content": current, "index": index})

    return chunks


def _split_long_paragraph(text: str, chunk_size: int) -> List[str]:
    """按句子分割超长段落"""
    sentences = re.split(r"(?<=[。！？.!?])\s*", text)
    chunks = []
    current = ""
    for s in sentences:
        if len(current) + len(s) <= chunk_size:
            current += s
        else:
            if current:
                chunks.append(current.strip())
            current = s
    if current:
        chunks.append(current.strip())
    return chunks


def process_document(filepath: str, filename: str) -> List[Dict[str, str]]:
    """处理文档：读取 → 分块 → 返回 chunk 列表"""
    text = read_file_content(filepath)
    return chunk_text(text)
