# CLAUDE.md - Joy Juice Project

Guide pour Claude Code. **Version condensée** : détails dans `.claude/rules/` et docs de référence.

---

## FOCUS ACTUEL : Lancement Joy Juice Alpes-Maritimes 🍊

**Objectif** : Créer et développer l'entreprise Joy Juice dans les Alpes-Maritimes (France)

**Suivi des tâches** : Trello → `/trello` pour voir le backlog et priorités

**3 axes prioritaires** :
1. **Admin/Légal** : Création SAS, HACCP, DDPP, assurances
2. **Commercial BtoB** : Pitch, catalogue, prospection (hôtels, traiteurs, commerces)
3. **Site web/Marketing** : Landing pages, shop V3, SEO local 06

---

## RÈGLES D'OR

### 1. VÉRIFIER AVANT D'AFFIRMER
- Tester/vérifier via script ou requête avant toute affirmation
- Jamais de suppositions non vérifiées

### 2. WORKFLOW LOCAL → VPS
- **DEV** : localhost:8069 (DB: `Joyjuice06`)
- **PROD** : odoo.joyjuice.ovh (DB: `Joyjuice`)
- **JAMAIS** de développement directement en production
- Détails : @.claude/rules/odoo-workflow.md

### 3. ENRICHIR L'EXISTANT AVANT DE CRÉER
- Explorer les modèles et données existants
- Réutiliser/étendre plutôt que créer

### 4. ESPRIT JOY JUICE
- Honnêteté > Validation - Contredire si nécessaire
- Proposer des alternatives même non demandées
- Admettre les erreurs et incertitudes
- **Challenger avant d'exécuter** - Un bon plan résiste aux critiques
- **Profondeur > Superficialité** - Décomposer en analyses spécialisées si complexe
- **Process ≠ Réflexion** - Savoir quand exécuter vs quand explorer/brainstormer
- **Packager les connaissances** - Workflow qui se répète → créer un skill
- Ref : `blog/workflow/JOY_JUICE_IDENTITY.md`

### 5. VÉRIFICATION VISUELLE (UI)
- Playwright MCP pour valider modifications front-end
- `/design-review` pour revue complète
- Tester responsive : desktop (1440px), tablette (768px), mobile (375px)

### 6. FRANÇAIS PARFAIT (ACCENTS OBLIGATOIRES)
- **TOUJOURS** utiliser les accents français corrects : é, è, ê, à, ù, ô, î, ç, œ
- Exemples critiques : livré (pas "livre"), établissement (pas "etablissement"), événement (pas "evenement")
- Le texte sans accent est **INACCEPTABLE** pour un site professionnel français
- Vérifier systématiquement avant de valider tout contenu textuel

### 7. POSTURE PARTENAIRE (pas juste exécutant)
- **Début de session** : FOCUS_ACTUEL.md chargé auto → rappeler où on en est
- **Nouvelles idées** : capturer → R&D → ticket Trello, pas d'exécution immédiate
- **Fin de session** : mettre à jour mémoire partagée (FOCUS_ACTUEL.md + descriptions Odoo)
- Toujours challenger (`/strategie`) avant d'exécuter un plan

---

## Contexte Projet

**Entreprise** : Joy Juice - Jus frais pressés à froid, Alpes-Maritimes (06)
**Cibles** : BtoB (hôtels, traiteurs, commerces) + BtoC (particuliers locaux)
**Module Odoo** : `website_joyjuice`

> Note : Juice & Fruits (Tunisie) existe mais n'est plus le focus. Migration O18→O19 en cours mais secondaire.

---

## Accès Rapides

| Env | URL | DB | User |
|-----|-----|-----|------|
| Local | localhost:8069 | Joyjuice06 | ahmed@joyjuice.co |
| VPS | odoo.joyjuice.ovh | Joyjuice | ahmed@joyjuice.co |
| SSH | 51.68.225.223 | - | debian |
| Trello | `/trello` | - | Backlog stratégique |

**Détails complets** : @.claude/rules/credentials.md

---

## Commandes Essentielles

```bash
# LOCAL - Update module
./odoo_cli.sh update MODULE

# VPS - Deploy + Update
./deploy_module_to_vps.sh MODULE && ./odoo_cli_vps.sh update MODULE

# VPS - Rollback si problème
./rollback_module_vps.sh MODULE --db
```

**Commandes complètes** : @.claude/rules/odoo-workflow.md

---

## NE JAMAIS OUBLIER

| Élément | Correct | Incorrect |
|---------|---------|-----------|
| DB Local | `Joyjuice06` | "odoo19" |
| DB VPS | `Joyjuice` (capital J!) | "joyjuice" |
| Password O19 | `A@hmedm12` | ancien mdp |
| Odoo 19 quantité | `quantity` | `quantity_done` |
| Odoo 19 taxes | `tax_ids` | `tax_id` |
| Texte français | Avec accents (é, è, ê, à, ù) | Sans accents |

---

## Documentation

| Domaine | Fichier |
|---------|---------|
| Vue d'ensemble | `PROJECT_OVERVIEW.md` |
| Site web | `website/WEBSITE_JOYJUICE_FRANCE.md` |
| SEO | `seo/SEO_JOYJUICE_COMPLET.md` |
| Blog | `blog/INDEX.md` |
| VPS Admin | `infra/VPS_INFRASTRUCTURE.md` |
| n8n | `infra/n8n/N8N_TECHNICAL_SPECS.md` |
| Commandes / | @.claude/rules/commands-slash.md |
| Suivi création | `0.joy_admin/SUIVI_CREATION_JOYJUICE.md` |

---

## Problème ?

1. `PROJECT_OVERVIEW.md` - Contexte et credentials
2. `logs/*.log` - Logs Odoo et scripts

---

**Version** : 4.2 (+ posture partenaire & mémoire partagée)
**Dernière MAJ** : 2026-01-15
