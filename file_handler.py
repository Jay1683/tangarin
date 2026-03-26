# file_handler.py
import os
import pandas as pd
from pathlib import Path
from langchain_community.document_loaders import CSVLoader, UnstructuredExcelLoader
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

UPLOADS_DIR = "uploads"

# Using a lightweight local embedding model — no API key needed
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def get_thread_dir(thread_id: str) -> Path:
    path = Path(UPLOADS_DIR) / thread_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_faiss_path(thread_id: str) -> Path:
    return get_thread_dir(thread_id) / "faiss_index"


async def process_csv_excel(file_path: str, thread_id: str) -> FAISS:
    ext = Path(file_path).suffix.lower()

    if ext == ".csv":
        loader = CSVLoader(file_path=file_path)
    elif ext in [".xlsx", ".xls"]:
        loader = UnstructuredExcelLoader(file_path=file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(documents)

    # Build and persist the FAISS index
    vector_store = FAISS.from_documents(chunks, embeddings)
    faiss_path = get_faiss_path(thread_id)
    vector_store.save_local(str(faiss_path))

    return vector_store


def load_faiss(thread_id: str) -> FAISS | None:
    faiss_path = get_faiss_path(thread_id)
    if faiss_path.exists():
        return FAISS.load_local(
            str(faiss_path), embeddings, allow_dangerous_deserialization=True
        )
    return None
