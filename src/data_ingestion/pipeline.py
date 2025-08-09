import logging
from pathlib import Path
from typing import List

from .config import settings
from .schemas import DrugEntry, GuidelineChunk
from .readers import load_drug_entries, iter_guideline_chunks
from .cleaners import clean_chunks
from .embedders import Embedder
from .vector_store import ChromaVectorStore, VectorStore

logger = logging.getLogger(__name__)


class IngestionPipeline:
    def __init__(
        self,
        drug_path: Path,
        guideline_dir: Path,
        embedder: Embedder,
        vector_store: VectorStore,
    ) -> None:
        self.drug_path = drug_path
        self.guideline_dir = guideline_dir
        self.embedder = embedder
        self.vector_store = vector_store

    def run(self) -> None:
        logger.info("Loading drug entries …")
        drugs: List[DrugEntry] = load_drug_entries(self.drug_path)
        logger.info("Loaded %d drug entries", len(drugs))

        logger.info("Streaming & cleaning guideline chunks …")
        chunks: List[GuidelineChunk] = list(iter_guideline_chunks(self.guideline_dir))
        chunks = clean_chunks(chunks)
        logger.info("Prepared %d chunks", len(chunks))

        logger.info("Embedding chunks …")
        texts = [c.text for c in chunks]
        embeddings = self.embedder.encode(texts)

        logger.info("Persisting to vector store …")
        self.vector_store.add_chunks(chunks, embeddings)
        self.vector_store.save()


def build_default_pipeline() -> IngestionPipeline:
    embedder = Embedder(settings["embedding_model"])
    vector_store: VectorStore = ChromaVectorStore(settings["persist_directory"])
    return IngestionPipeline(
        drug_path=settings["drug_db_path"],
        guideline_dir=settings["guideline_dir"],
        embedder=embedder,
        vector_store=vector_store,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_default_pipeline().run()
