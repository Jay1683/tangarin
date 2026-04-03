# file_handler.py
import os
from pathlib import Path

import pandas as pd
from langchain_community.document_loaders import CSVLoader, UnstructuredExcelLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

UPLOADS_DIR = "uploads"

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def get_thread_dir(thread_id: str) -> Path:
    path = Path(UPLOADS_DIR) / thread_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_faiss_path(thread_id: str) -> Path:
    return get_thread_dir(thread_id) / "faiss_index"


def load_faiss(thread_id: str) -> FAISS | None:
    faiss_path = get_faiss_path(thread_id)
    if faiss_path.exists():
        return FAISS.load_local(
            str(faiss_path),
            embeddings,
            allow_dangerous_deserialization=True,
        )
    return None


def _build_and_save_vector_store(documents: list, thread_id: str) -> FAISS:
    """Shared logic: chunk docs, build FAISS, persist to disk."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(documents)

    # If an index already exists (e.g. from a previous file), merge into it
    faiss_path = get_faiss_path(thread_id)
    if faiss_path.exists():
        vector_store = FAISS.load_local(
            str(faiss_path),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        vector_store.add_documents(chunks)
    else:
        vector_store = FAISS.from_documents(chunks, embeddings)

    vector_store.save_local(str(faiss_path))
    return vector_store


async def process_csv_excel(file_path: str, thread_id: str) -> FAISS:
    ext = Path(file_path).suffix.lower()

    if ext == ".csv":
        loader = CSVLoader(file_path=file_path)
    elif ext in [".xlsx", ".xls"]:
        loader = UnstructuredExcelLoader(file_path=file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    documents = loader.load()
    return _build_and_save_vector_store(documents, thread_id)


async def process_pdf(file_path: str, thread_id: str) -> FAISS:
    loader = PyPDFLoader(file_path=file_path)
    documents = loader.load()
    return _build_and_save_vector_store(documents, thread_id)
