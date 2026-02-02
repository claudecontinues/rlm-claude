"""
RLM Embeddings - Semantic embedding providers for hybrid search.

Phase 8 implementation.

Provides two embedding providers:
- Model2VecProvider: minishlab/potion-multilingual-128M (256 dim, fast)
- FastEmbedProvider: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384 dim, accurate)

Selection via RLM_EMBEDDING_PROVIDER env var (default: model2vec).
All dependencies are optional — returns None if unavailable.
"""

import os
from abc import ABC, abstractmethod

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    def embed(self, texts: list[str]):
        """Embed a list of texts into vectors.

        Args:
            texts: List of text strings to embed

        Returns:
            numpy ndarray of shape (len(texts), dim)
        """

    @abstractmethod
    def dim(self) -> int:
        """Return the embedding dimension."""


class Model2VecProvider(EmbeddingProvider):
    """Embedding provider using Model2Vec (minishlab/potion-multilingual-128M).

    256 dimensions, very fast inference, good multilingual support.
    """

    MODEL_NAME = "minishlab/potion-multilingual-128M"
    DIM = 256

    def __init__(self):
        from model2vec import StaticModel

        self._model = StaticModel.from_pretrained(self.MODEL_NAME)

    def embed(self, texts: list[str]):
        return self._model.encode(texts)

    def dim(self) -> int:
        return self.DIM


class FastEmbedProvider(EmbeddingProvider):
    """Embedding provider using FastEmbed (paraphrase-multilingual-MiniLM-L12-v2).

    384 dimensions, higher accuracy, slightly slower. ONNX-based.
    """

    MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    DIM = 384

    def __init__(self):
        from fastembed import TextEmbedding

        self._model = TextEmbedding(model_name=self.MODEL_NAME)

    def embed(self, texts: list[str]):
        # fastembed returns a generator
        embeddings = list(self._model.embed(texts))
        return np.array(embeddings)

    def dim(self) -> int:
        return self.DIM


# Singleton cache
_cached_provider: EmbeddingProvider | None = None
_provider_loaded: bool = False


def _get_cached_provider() -> EmbeddingProvider | None:
    """Get or create the cached embedding provider (singleton, lazy).

    Reads RLM_EMBEDDING_PROVIDER env var (default: "model2vec").
    Returns None if the required library is not installed.
    """
    global _cached_provider, _provider_loaded

    if _provider_loaded:
        return _cached_provider

    _provider_loaded = True
    provider_name = os.getenv("RLM_EMBEDDING_PROVIDER", "model2vec").lower()

    try:
        if provider_name == "fastembed":
            _cached_provider = FastEmbedProvider()
        else:
            _cached_provider = Model2VecProvider()
    except (ImportError, Exception):
        _cached_provider = None

    return _cached_provider


def get_provider() -> EmbeddingProvider | None:
    """Public API to get the current embedding provider.

    Returns None if the required library is not installed.
    """
    return _get_cached_provider()
