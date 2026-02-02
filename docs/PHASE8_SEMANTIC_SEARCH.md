# Phase 8 — Recherche Sémantique (Embeddings)

> **Statut** : R&D — Recherche complétée, prêt pour implémentation
> **Date** : 2026-02-01
> **Objectif** : Ajouter une couche de recherche sémantique à RLM pour compléter BM25

---

## Le problème

BM25 cherche par mots-clés. Si le vocabulaire diffère entre la requête et le chunk, la recherche échoue :

```
User: "comment on a résolu le problème de performance ?"
Chunk: "optimisation requêtes SQL avec index sur product_template"
BM25: ❌ aucun mot en commun
Embeddings: ✅ même champ sémantique
```

Avec 100+ chunks et une croissance continue, ce problème va s'aggraver.

---

## Approche : Recherche Hybride

Pas remplacer BM25, mais le combiner avec des embeddings vectoriels.

**Score final** = α × cosine_similarity + (1-α) × BM25_normalisé

### Flux à l'écriture (rlm_chunk)

```
rlm_chunk("discussion API redesign...")
    ├── Stocke le texte (existant)
    ├── Indexe BM25 (existant)
    └── [NOUVEAU] Génère embedding → stocke dans embeddings.npz
```

### Flux à la recherche (rlm_search)

```
rlm_search("problème de performance")
    ├── BM25 → tous les chunks + scores normalisés (min-max)
    ├── Cosine similarity → tous les chunks + scores
    └── Fusion pondérée (α=0.6) → top 5 résultats
```

---

## Recherche effectuée (2026-02-01)

### État de l'art MCP

| MCP Server | Embedding lib | Stockage | Approche |
|------------|---------------|----------|----------|
| **Qdrant MCP** (officiel) | FastEmbed (ONNX) | Qdrant | Dense seul |
| **rag-memory-mcp** | sentence-transformers | sqlite-vec | Hybride + knowledge graph |
| **mcp-local-rag** (shinpr) | Transformers.js | LanceDB | Hybride keyword+dense |
| **mcp-memory-service** (doobidoo) | sentence-transformers | ChromaDB | Dense, ~5ms retrieval |
| **Zilliz claude-context** | OpenAI/VoyageAI | Milvus | Hybride BM25+dense |

**Consensus** : Hybride est la norme. sqlite-vec = sweet spot pour MCP léger.

### Comparatif bibliothèques d'embeddings

| Critère | **Model2Vec** | **FastEmbed** | **EmbeddingGemma 300M** |
|---------|---------------|---------------|-------------------------|
| Dépendance | numpy seul | ONNX Runtime | ONNX Runtime |
| Taille lib + deps | **~5 MB** | ~150 MB | ~150 MB |
| Taille modèle | **~30 MB** | 80-400 MB | 80-600 MB |
| PyTorch requis | Non | Non | Non |
| ONNX Runtime requis | **Non** | Oui | Oui |
| RAM | **20-50 MB** | 200-500 MB | 200-600 MB |
| Cold start | **<100ms** | 1-3s | 2-5s |
| Qualité FR/EN | ~90% de LaBSE (101 langues) | ~100% transformer | SOTA pour sa taille |
| Qualité court texte | ~85-92% du transformer | Excellent | Excellent |
| Maturité | EMNLP 2025, intégré LangChain | Qdrant ecosystem, mature | Google, sept 2025 |
| Modèle recommandé | `potion-multilingual-128M` | `multilingual-e5-small` | q4 quantized |

**txtai** et **sentence-transformers ONNX** : éliminés (PyTorch obligatoire).
**LightEmbed** : fonctionnellement identique à FastEmbed, communauté plus petite.

### Stratégie de fusion

| Méthode | Qualité | Complexité | Tuning requis |
|---------|---------|------------|---------------|
| **Convex combination** | Meilleure (Bruch et al., ACM TOIS) | Simple | α statique suffit |
| RRF (k=60) | Bonne | Simple | Plus sensible qu'on croit |
| Cross-encoder reranking | Excellente | Ajout d'un modèle | Overkill pour <500 docs |

**Normalisation BM25** : min-max par batch → [0, 1]
**Alpha** : 0.5-0.6 par défaut (dense-léger dominant)
**Brute-force** : cosine sur <500 vecteurs = microsecondes (pas d'ANN)

---

## Décisions

### Choix : Model2Vec (primaire) + FastEmbed (fallback)

**Model2Vec `potion-multilingual-128M`** est le meilleur fit pour RLM :

1. **Empreinte minimale** : 5 MB deps + 30 MB modèle = 35 MB total vs 230+ MB pour FastEmbed
2. **RAM négligeable** : 30-50 MB vs 200-500 MB — un MCP server doit rester léger
3. **Cold start instantané** : <100ms vs 1-3s — pas de lazy loading complexe nécessaire
4. **Qualité suffisante** : Dans un système hybride BM25+dense, la perte de ~10% sur le dense est compensée par le BM25 qui rattrape les matchs exacts
5. **101 langues** : FR/EN couvert, publié à EMNLP 2025

**Upgrade path** : Si la qualité sémantique s'avère insuffisante sur du contenu technique FR, basculer vers FastEmbed sans changer l'architecture (interface abstraite).

### Stockage : numpy .npz

Brute-force cosine sur <500 vecteurs de dimension 256 = microsecondes. Pas besoin de sqlite-vec ni d'ANN.

### Fusion : Convex combination

```python
score = alpha * cosine_sim + (1 - alpha) * bm25_normalized
alpha = 0.6  # default, dense-dominant
```

Normalisation BM25 : min-max par batch de résultats.

### Dépendance optionnelle

```toml
[project.optional-dependencies]
semantic = ["model2vec>=0.4.0"]
```

→ `pip install mcp-rlm-server[semantic]`

Sans le package, `rlm_search` reste BM25 pur. Pattern de dégradation gracieuse existant (comme `thefuzz`).

---

## Architecture

### Interface abstraite (swap Model2Vec → FastEmbed sans friction)

```python
class EmbeddingProvider:
    """Abstract embedding provider."""
    def encode(self, texts: list[str]) -> np.ndarray: ...
    def dim(self) -> int: ...

class Model2VecProvider(EmbeddingProvider):
    def __init__(self):
        from model2vec import StaticModel
        self.model = StaticModel.from_pretrained("minishlab/potion-multilingual-128M")

    def encode(self, texts):
        return self.model.encode(texts)

    def dim(self):
        return 256  # potion-multilingual-128M

class FastEmbedProvider(EmbeddingProvider):
    def __init__(self):
        from fastembed import TextEmbedding
        self.model = TextEmbedding("intfloat/multilingual-e5-small")

    def encode(self, texts):
        return np.array(list(self.model.embed(texts)))

    def dim(self):
        return 384  # multilingual-e5-small
```

### Fichiers à créer/modifier

| Fichier | Action |
|---------|--------|
| `src/mcp_server/tools/embeddings.py` | **Nouveau** — EmbeddingProvider, store/load/cosine |
| `src/mcp_server/tools/navigation.py` | Modifier `chunk()` — générer embedding à la création |
| `src/mcp_server/tools/search.py` | Modifier `search()` — mode hybride si dispo |
| `scripts/backfill_embeddings.py` | **Nouveau** — embeddings pour les 104+ chunks existants |
| `tests/test_semantic_search.py` | **Nouveau** — tests recherche hybride |
| `pyproject.toml` | Ajouter optional dep `[semantic]` |

---

## Risques identifiés

| Risque | Probabilité | Mitigation |
|--------|------------|------------|
| Qualité Model2Vec insuffisante sur FR technique | Moyenne | Interface abstraite → swap FastEmbed |
| Cold start modèle (1er lancement) | Faible | Model2Vec = <100ms, pas de download HTTP |
| RAM trop élevée | Faible | 30 MB pour Model2Vec, acceptable |
| Backfill lent sur 104 chunks | Faible | Model2Vec = ~0.02ms/texte, total <1s |
| Breaking change Model2Vec | Faible | Pin version, API simple |

---

## Checklist recherche

- [x] State of the art : MCP servers avec recherche sémantique
- [x] Benchmarks fastembed vs Model2Vec vs alternatives légères
- [x] Retours communauté sur fastembed en production
- [x] Modèles multilingues FR/EN performants et légers
- [x] Patterns d'intégration hybride BM25 + embeddings

---

## Références

### Bibliothèques
- [Model2Vec](https://github.com/MinishLab/model2vec) — Static embeddings, EMNLP 2025
- [potion-multilingual-128M](https://huggingface.co/minishlab/potion-multilingual-128M) — 101 langues, 256 dim
- [FastEmbed](https://github.com/qdrant/fastembed) — ONNX-based (fallback)
- [EmbeddingGemma](https://huggingface.co/onnx-community/embeddinggemma-300m-ONNX) — Google, SOTA petite taille

### MCP Servers de référence
- [Qdrant MCP](https://github.com/qdrant/mcp-server-qdrant) — FastEmbed
- [rag-memory-mcp](https://github.com/ttommyth/rag-memory-mcp) — sqlite-vec + knowledge graph
- [mcp-local-rag](https://github.com/shinpr/mcp-local-rag) — LanceDB hybride
- [mcp-memory-service](https://github.com/doobidoo/mcp-memory-service) — ChromaDB, populaire

### Recherche hybride
- [Bruch et al., "Analysis of Fusion Functions"](https://dl.acm.org/doi/10.1145/3596512) — Convex > RRF (ACM TOIS)
- [Weaviate Hybrid Search](https://weaviate.io/blog/hybrid-search-explained) — Guide pratique
- [Qdrant Hybrid Search](https://qdrant.tech/articles/hybrid-search/) — Normalisation des scores

---

**Version** : 0.2 (recherche complétée, décisions prises)
**Prochaine étape** : Implémentation
