import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("support_coach.embedder")

class EmbeddingError(Exception):
    """Raised when embedding generation fails."""
    pass

class EmbeddingService:
    """
    Embedding service utilizing sentence-transformers/all-MiniLM-L6-v2.
    Ensures identical preprocessing for both document indexing and query retrieval.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        logger.info("Initializing SentenceTransformer with model '%s'...", self.model_name)
        try:
            self.model = SentenceTransformer(self.model_name, local_files_only=True)
        except Exception:
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.error("Failed to load embedding model '%s': %s", self.model_name, str(e))
                raise EmbeddingError(f"Could not initialize embedding model '{self.model_name}': {str(e)}")

        if hasattr(self.model, "get_embedding_dimension"):
            self.embedding_dimension = self.model.get_embedding_dimension()
        else:
            self.embedding_dimension = self.model.get_sentence_embedding_dimension()
        logger.info("SentenceTransformer '%s' ready (dimension: %d)", self.model_name, self.embedding_dimension)

    @property
    def tokenizer(self):
        """Returns underlying model tokenizer for accurate token counting."""
        return getattr(self.model, "tokenizer", None)

    def _preprocess(self, text: str) -> str:
        """Standardized text preprocessing before encoding."""
        if not text:
            return ""
        # Normalizes whitespace and strips
        return " ".join(text.split()).strip()

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Generates normalized embedding vectors for a list of chunk texts.
        Returns List of 384-dimensional float lists.
        """
        if not texts:
            return []

        clean_texts = [self._preprocess(t) for t in texts]
        try:
            embeddings = self.model.encode(
                clean_texts,
                batch_size=batch_size,
                show_progress_bar=False,
                normalize_embeddings=True,  # Unit length for exact cosine similarity
                convert_to_numpy=True
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error("Embedding generation failed for batch of %d items: %s", len(texts), str(e))
            raise EmbeddingError(f"Failed to generate chunk embeddings: {str(e)}")

    def embed_query(self, query: str) -> List[float]:
        """
        Generates a normalized embedding vector for a customer query.
        Uses the exact same preprocessing and normalization as document chunks.
        """
        clean_query = self._preprocess(query)
        if not clean_query:
            raise EmbeddingError("Cannot generate embedding for empty query.")

        try:
            embedding = self.model.encode(
                clean_query,
                normalize_embeddings=True,
                convert_to_numpy=True
            )
            return embedding.tolist()
        except Exception as e:
            logger.error("Query embedding generation failed: %s", str(e))
            raise EmbeddingError(f"Failed to generate query embedding: {str(e)}")

# Singleton instance accessor
_embedding_service_instance: Optional[EmbeddingService] = None

def get_embedding_service(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingService:
    global _embedding_service_instance
    if _embedding_service_instance is None or _embedding_service_instance.model_name != model_name:
        _embedding_service_instance = EmbeddingService(model_name=model_name)
    return _embedding_service_instance
