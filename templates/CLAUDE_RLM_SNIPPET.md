## RLM - MÉMOIRE PERSISTANTE

### Philosophie (v0.9.0)

L'utilisateur décide quand chunker. Le système sauvegarde automatiquement avant /compact.

### Quand chunker (réflexe Claude)

**Chunk proactivement quand :**
- 🎯 Décision importante prise
- ✅ Tâche terminée avec succès
- 💡 Insight ou règle découverte
- 🔄 Changement de sujet majeur
- ⚠️ Bug corrigé (documenter la cause)

**Chunk sur instruction utilisateur :**
- "garde ça en mémoire"
- "chunk cette discussion"
- "rlm_remember cette décision"

### Sauvegarde automatique

Le hook PreCompact crée un chunk minimal avant chaque /compact.
Après le compact, tu peux lire ce chunk et l'enrichir si nécessaire.

### Début de session

Appeler `rlm_status()` pour voir l'état de la mémoire.

### Cette mémoire est LA TIENNE

Tu n'as pas besoin de demander permission pour :
- Chunker l'historique
- Sauvegarder des insights
- Consulter ta mémoire

C'est ton outil personnel de gestion de contexte.

### Commandes utiles

```python
# Sauvegarder un insight
rlm_remember("contenu", category="decision", importance="high")

# Chunker une discussion
rlm_chunk("résumé de la discussion", summary="Session du 24/01", tags="session")

# Chercher dans l'historique
rlm_search("sujet")
rlm_grep("pattern")

# Voir l'état
rlm_status()
```
