import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import get_settings

logger = logging.getLogger("support_coach.vector_store")

class VectorStoreError(Exception):
    """Base exception for ChromaDB vector store operations."""
    pass

class VectorStore:
    """
    Manages persistent local ChromaDB vector storage.
    Enforces chunk traceability, duplicate prevention, and cosine similarity search.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None
    ):
        settings = get_settings()
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME

        os.makedirs(self.persist_directory, exist_ok=True)
        logger.info("Initializing ChromaDB PersistentClient at '%s'...", self.persist_directory)

        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            # Create or get collection with cosine distance metric
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(
                "ChromaDB collection '%s' ready (current count: %d)",
                self.collection_name, self.collection.count()
            )
        except Exception as e:
            logger.error("Failed to initialize ChromaDB: %s", str(e))
            raise VectorStoreError(f"ChromaDB initialization failure: {str(e)}")

    def add_chunks(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ):
        """
        Inserts document chunks into ChromaDB.
        Performs upsert to prevent duplicate primary key collisions.
        """
        if not chunk_ids:
            return

        try:
            # Clean metadatas: ChromaDB requires primitive types (str, int, float, bool)
            cleaned_metadatas = []
            for meta in metadatas:
                clean_meta = {}
                for k, v in meta.items():
                    if v is None:
                        clean_meta[k] = ""
                    elif isinstance(v, (str, int, float, bool)):
                        clean_meta[k] = v
                    else:
                        clean_meta[k] = str(v)
                cleaned_metadatas.append(clean_meta)

            self.collection.upsert(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=cleaned_metadatas
            )
            logger.info("Successfully indexed %d chunks in ChromaDB collection '%s'", len(chunk_ids), self.collection_name)
        except Exception as e:
            logger.error("Failed to add chunks to ChromaDB: %s", str(e))
            raise VectorStoreError(f"Error adding chunks to ChromaDB: {str(e)}")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 4,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs similarity search using query embedding.
        Returns list of matched chunks with metadata and computed cosine similarity score.
        """
        try:
            total_count = self.collection.count()
            if total_count == 0:
                logger.warning("Search called on empty ChromaDB collection.")
                return []

            n_results = min(top_k, total_count)
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )

            matched_chunks: List[Dict[str, Any]] = []
            if not results or not results.get("ids") or not results["ids"][0]:
                return matched_chunks

            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            for rank_idx, (c_id, doc, meta, dist) in enumerate(zip(ids, docs, metas, distances), start=1):
                # For cosine distance, distance = 1 - cosine_sim
                # Therefore, cosine_sim = 1 - distance
                relevance_score = max(0.0, min(1.0, 1.0 - float(dist)))

                matched_chunks.append({
                    "chunk_id_str": c_id,
                    "text": doc,
                    "metadata": meta,
                    "distance": float(dist),
                    "relevance_score": round(relevance_score, 4),
                    "rank": rank_idx
                })

            return matched_chunks
        except Exception as e:
            logger.error("ChromaDB search failed: %s", str(e))
            raise VectorStoreError(f"Vector search failed: {str(e)}")

    def delete_document_chunks(self, document_id: int):
        """Removes all chunks belonging to a document from ChromaDB."""
        try:
            self.collection.delete(where={"document_id": document_id})
            logger.info("Deleted chunks for document_id %d from ChromaDB", document_id)
        except Exception as e:
            logger.error("Failed to delete chunks for document_id %d: %s", document_id, str(e))
            raise VectorStoreError(f"Failed to delete document chunks from vector store: {str(e)}")

    def get_count(self) -> int:
        """Returns total number of chunks currently stored in ChromaDB."""
        return self.collection.count()

    def reset_collection(self):
        """Clears all vectors from collection (primarily for tests)."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB collection '%s' reset successfully.", self.collection_name)
        except Exception as e:
            logger.error("Failed to reset ChromaDB collection: %s", str(e))
            raise VectorStoreError(f"Vector collection reset failed: {str(e)}")

# Singleton instance
_vector_store_instance: Optional[VectorStore] = None

def get_vector_store(
    persist_directory: Optional[str] = None,
    collection_name: Optional[str] = None
) -> VectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore(
            persist_directory=persist_directory,
            collection_name=collection_name
        )
    return _vector_store_instance
