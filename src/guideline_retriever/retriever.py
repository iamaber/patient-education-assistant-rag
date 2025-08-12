import chromadb
from sentence_transformers import SentenceTransformer
from typing import List
from src.condition_extractor.schemas import Condition
from config.settings import (
    PERSIST_DIRECTORY,
    EMBEDDING_MODEL,
    RETRIEVER_TOP_K,
    RERANK_CROSS_ENCODER,
)
from .schemas import RetrievedChunk
from sentence_transformers import CrossEncoder


class GuidelineRetriever:
    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(path=str(PERSIST_DIRECTORY))
        self.collection = self.client.get_collection("guidelines")
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        self.reranker = (
            CrossEncoder(RERANK_CROSS_ENCODER) if RERANK_CROSS_ENCODER else None
        )

    def retrieve(self, conditions: List[Condition]) -> List[RetrievedChunk]:
        query = " ".join(c.name for c in conditions)
        query_vec = self.embedder.encode([query]).tolist()

        hits = self.collection.query(
            query_embeddings=query_vec,
            n_results=RETRIEVER_TOP_K * 2,  # over-fetch for reranking
        )

        # Build candidates
        candidates = [
            RetrievedChunk(
                text=hits["documents"][0][i],
                source_file=hits["metadatas"][0][i]["source"],
                page=hits["metadatas"][0][i].get("page"),
                score=hits["distances"][0][i],  # lower is better (cosine distance)
            )
            for i in range(len(hits["documents"][0]))
        ]

        # Optional cross-encoder rerank
        if self.reranker:
            pairs = [(query, c.text) for c in candidates]
            rerank_scores = self.reranker.predict(pairs)
            for c, s in zip(candidates, rerank_scores):
                c.score = -s  # higher score → better
            candidates.sort(key=lambda x: x.score, reverse=True)

        return candidates[:RETRIEVER_TOP_K]
