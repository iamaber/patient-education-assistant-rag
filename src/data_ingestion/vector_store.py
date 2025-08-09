from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import chromadb
from chromadb.config import Settings as ChromaSettings

from .schemas import GuidelineChunk


class VectorStore(ABC):
    @abstractmethod
    def add_chunks(
        self, chunks: List[GuidelineChunk], embeddings: List[List[float]]
    ) -> None: ...

    @abstractmethod
    def save(self) -> None: ...


class ChromaVectorStore(VectorStore):
    def __init__(self, persist_dir: Path, collection_name: str = "guidelines") -> None:
        self.client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_chunks(
        self, chunks: List[GuidelineChunk], embeddings: List[List[float]]
    ) -> None:
        ids = [f"{c.source_file}:{i}" for i, c in enumerate(chunks)]
        metadatas = [
            {"source": c.source_file, "condition": c.condition_tag, "pmid": c.pmid}
            for c in chunks
        ]
        self.collection.add(
            ids=ids,
            documents=[c.text for c in chunks],
            metadatas=metadatas,
            embeddings=embeddings,
        )

    def save(self) -> None:
        pass  # Chroma auto-persists
