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
        batch_size = 5000  # Use a safe batch size under the limit
        total_chunks = len(chunks)

        for i in range(0, total_chunks, batch_size):
            end_idx = min(i + batch_size, total_chunks)
            batch_chunks = chunks[i:end_idx]
            batch_embeddings = embeddings[i:end_idx]

            ids = [f"{c.source_file}:{i + idx}" for idx, c in enumerate(batch_chunks)]
            metadatas = []
            for c in batch_chunks:
                metadata = {"source": c.source_file, "condition": c.condition_tag}
                if c.pmid is not None:
                    metadata["pmid"] = c.pmid
                metadatas.append(metadata)

            self.collection.add(
                ids=ids,
                documents=[c.text for c in batch_chunks],
                metadatas=metadatas,
                embeddings=batch_embeddings,
            )

            print(f"Added batch {i // batch_size + 1}: {len(batch_chunks)} chunks")

    def save(self) -> None:
        pass  # Chroma auto-persists
