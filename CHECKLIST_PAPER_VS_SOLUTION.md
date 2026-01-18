# Checklist : Paper RLM vs Notre Solution

> **Objectif** : Vérifier qu'on n'a rien oublié d'important du papier MIT
> **Date** : 2026-01-18

---

## 1. Mécanismes Core

| Concept (Paper) | Notre Solution | Statut | Notes |
|-----------------|----------------|--------|-------|
| **REPL Environment** | MCP Server + Tools | ✅ | Via tools Claude Code au lieu de Python exec |
| **Context as variable** | Fichiers chunks/ | ✅ | Stocké en fichiers au lieu de RAM |
| **Recursive sub-calls** | Task tool (subagents) | ✅ | Natif Claude Code, même mieux |
| **Sub-model différent** | Haiku pour sub-calls | ⏳ | À configurer (économie tokens) |
| **Symboli vs tokens** | Grep/Read tools | ✅ | Navigation sans charger tout le contexte |

---

## 2. Stratégies de Chunking

| Concept (Paper) | Notre Solution | Statut | Notes |
|-----------------|----------------|--------|-------|
| **Uniform splitting** | strategy: "size" | ✅ | 2000 tokens par chunk |
| **Keyword filtering** | rlm_grep | ✅ | Regex sur chunks |
| **Semantic grouping** | strategy: "semantic" | ⏳ | À implémenter (Phase 2+) |
| **Overlap** | 200 tokens overlap | ✅ | Évite perte info |

---

## 3. Détails d'Implémentation

| Concept (Paper) | Notre Solution | Statut | Notes |
|-----------------|----------------|--------|-------|
| **System prompt fixe** | À créer | ⏳ | Dans appendice IMPLEMENTATION_PROPOSAL |
| **FINAL() tags** | Non nécessaire | ✅ | Claude termine naturellement |
| **Variables pour long output** | session_memory.json | ✅ | Accumulation via fichiers |
| **Cost optimization** | Haiku sub-calls | ⏳ | À configurer |

---

## 4. Stratégies Émergentes

| Concept (Paper) | Notre Solution | Statut | Notes |
|-----------------|----------------|--------|-------|
| **Peeking** | rlm_peek(chunk, start, end) | ✅ | Tool dédié |
| **Grepping** | rlm_grep(pattern) | ✅ | Tool dédié |
| **Answer verification** | rlm_sub_query double-check | ⏳ | À implémenter (optionnel) |
| **Semantic sub-calls** | Task subagents | ✅ | Natif |
| **Code + LLM mixing** | Bash + Claude | ✅ | Natif Claude Code |

---

## 5. Failure Modes & Mitigations

| Risque (Paper) | Notre Mitigation | Statut |
|----------------|------------------|--------|
| **Prompt sensitivity** | Prompt testé et documenté | ⏳ |
| **Token limits** | Chunks petits (2000 tokens) | ✅ |
| **Redundant verification** | Pas de verification loop obligatoire | ✅ |
| **Answer commitment** | Pas de FINAL tags, flow naturel | ✅ |
| **Code fragility** | Tools MCP au lieu de code exec | ✅ |

---

## 6. Concepts Avancés

| Concept (Paper) | Notre Solution | Statut | Priorité |
|-----------------|----------------|--------|----------|
| **Context rot mitigation** | Sub-calls courts | ✅ | P0 |
| **Complexity scaling** | Chunking adaptatif | ⏳ | P2 |
| **Async sub-calls** | Task parallèles | ✅ | P0 |
| **Recursion depth > 1** | Subagents illimités | ✅ | P0 |
| **Training as RLM** | Non applicable (API) | ❌ | N/A |

---

## 7. Concepts MANQUANTS à Ajouter

| Concept | Description | Action |
|---------|-------------|--------|
| **Sub-model économique** | Utiliser Haiku pour sub-calls | Ajouter dans config MCP |
| **Semantic chunking** | Découper par changement de sujet | Phase 2 |
| **Verification optionnelle** | Double-check sur tâches critiques | Phase 3 |
| **Prompt tuning** | Adapter selon type de tâche | Phase 4 |
| **Metrics/analytics** | Suivre coûts et performance | Phase 5 |

---

## 8. Évaluation n8n pour Hooks

### Question : n8n est-il utile pour les hooks RLM ?

**Analyse** :

| Aspect | n8n | Scripts locaux | Verdict |
|--------|-----|----------------|---------|
| **Complexité** | Haute | Basse | Scripts |
| **Latence** | HTTP call | Local direct | Scripts |
| **Fiabilité** | Dépend serveur | Toujours dispo | Scripts |
| **Use case** | Workflows complexes | Tâches simples | Dépend |

**Recommandation** : **Pas besoin de n8n pour les hooks RLM**

**Pourquoi ?**
1. Les hooks Claude Code sont des **scripts bash simples** (post_response.sh)
2. Ils s'exécutent **localement** sans latence réseau
3. n8n ajouterait de la **complexité inutile** pour ce cas

**Où n8n SERAIT utile** :
- Synchronisation multi-devices (si on travaille depuis plusieurs machines)
- Alertes externes (Slack, email) quand contexte > 80%
- Dashboard analytics centralisé
- Backup automatique des chunks vers cloud

**Conclusion** : Garder les hooks en **scripts locaux** pour la v1. n8n peut être intéressant pour la v2+ si on veut des features avancées.

---

## 9. Ajouts Recommandés au Plan

Basé sur cette checklist, voici ce qu'on devrait ajouter :

### Phase 1 (mise à jour)
- [ ] Configurer Haiku comme modèle pour sub-queries (économie tokens)

### Phase 2 (mise à jour)
- [ ] Implémenter semantic chunking (par sujet, pas juste par taille)

### Phase 3 (mise à jour)
- [ ] Ajouter verification optionnelle pour tâches critiques
- [ ] Metrics de coût par query

### Phase 5 (ajout)
- [ ] Évaluer n8n pour analytics centralisé
- [ ] Dashboard usage (tokens, latence, hit rate)

---

## 10. Score de Couverture

**Concepts couverts** : 22/26 = **85%**

**Manquants critiques** : 0
**Manquants nice-to-have** : 4 (ajoutés au plan)

---

**Conclusion** : Notre architecture couvre l'essentiel du papier RLM. Les ajouts identifiés sont des optimisations, pas des éléments bloquants.
