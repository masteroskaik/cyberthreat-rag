<div align="center">

# 🛡️ CyberThreat RAG

**Plateforme de Cyber Threat Intelligence pilotée par un système RAG construit *from scratch***

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-Vite-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)](https://neon.tech)
[![Groq](https://img.shields.io/badge/LLM-Groq-F55036)](https://groq.com/)
[![Cohere](https://img.shields.io/badge/Embeddings%20%2F%20Rerank-Cohere-39594C)](https://cohere.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#licence)
[![Status](https://img.shields.io/badge/Status-Production-success)](#déploiement)

**[🌐 Démo en ligne](https://cyberthreat-rag.vercel.app)** · **[📄 API docs](https://cyberthreat-rag.onrender.com/docs)**

</div>

---

## Pourquoi ce projet

La plupart des projets "RAG sur des CVE" qu'on trouve en portfolio se contentent d'indexer une liste de vulnérabilités. **CyberThreat RAG** va plus loin : il relie trois sources officielles — vulnérabilité (NVD), confirmation d'exploitation active (CISA KEV), et technique d'attaque réelle (MITRE ATT&CK) — pour répondre non pas à *"quelles sont les CVE ?"* mais à *"qu'est-ce qui est réellement dangereux, et comment est-ce exploité ?"*.

L'intégralité du pipeline RAG (chunking, recherche hybride, fusion de classements, reranking) est **construite sans framework** (pas de LangChain, pas de LlamaIndex), pour démontrer une maîtrise de bout en bout plutôt qu'un assemblage de bibliothèques.

## Aperçu du produit

| Dashboard | Assistant IA |
|---|---|
| KPI, priorisation des menaces, statut des sources en temps réel | Questions en langage naturel, rapports sourcés |

- 🎯 **Priorisation automatique** — croise score CVSS et statut d'exploitation active (KEV)
- 🤖 **Assistant IA** — pose une question, reçois un rapport CTI structuré avec sources citées
- 📄 **Export Word** — chaque rapport généré est exportable en `.docx` proprement formaté
- 🔍 **Recherche hybride** — combine similarité vectorielle et recherche par mots-clés (Reciprocal Rank Fusion)
- 🗂️ **Catalogue ATT&CK consultable** — 697 techniques, avec plateformes et références officielles
- 🔄 **Ingestion automatisée** — GitHub Actions programmé, aucune intervention manuelle nécessaire
- 🔒 **Sécurisé** — authentification JWT, mots de passe hashés (bcrypt)
- 💸 **100 % gratuit** — toute la stack tourne sur des services gratuits, sans carte bancaire

## Architecture

```
┌─────────────┐   ┌─────────────┐   ┌──────────────┐
│     NVD     │   │  CISA KEV   │   │ MITRE ATT&CK │
└──────┬──────┘   └──────┬──────┘   └──────┬───────┘
       │                 │                 │
       └────────────────────────────────────┘
                          │
        Ingestion automatisée (GitHub Actions, 2x/semaine)
                          │
                          ▼
              PostgreSQL + pgvector (Neon)
                          │
                Chunking & Embeddings (Cohere)
                          │
                          ▼
          Recherche hybride (vectorielle + full-text)
                  Fusion par Reciprocal Rank Fusion
                          │
                          ▼
                 Reranking (Cohere Rerank)
                          │
                          ▼
          Génération de rapport CTI sourcé (Groq)
                          │
                          ▼
                   API FastAPI (JWT) — Render
                          │
                          ▼
              Dashboard React (Vite) — Vercel
```

## Stack technique

| Couche | Technologie | Pourquoi ce choix |
|---|---|---|
| Base de données | PostgreSQL + **pgvector** (Neon) | Un seul moteur pour données relationnelles et vectorielles |
| Embeddings | **Cohere Embed** (embed-v4.0) | API légère — évite de charger PyTorch en production (contrainte mémoire réelle rencontrée sur Render) |
| Reranking | **Cohere Rerank** (rerank-v3.5) | Reranking sémantique précis, sans modèle local |
| Génération | **Groq** (openai/gpt-oss-120b) | Inférence LLM rapide et gratuite |
| API | **FastAPI** + JWT | Performances, typage, documentation auto-générée |
| Frontend | **React** + Vite | SPA légère, pas de besoin de SSR pour une app privée |
| Automatisation | **GitHub Actions** | Ingestion planifiée sans serveur dédié |
| Hébergement | **Render** (API) + **Vercel** (frontend) + **Neon** (DB) | 100 % gratuit, déploiement continu |

## Exemple d'utilisation

**Requête :**
> Quelles techniques MITRE ATT&CK sont liées à l'exploitation de vulnérabilités visant les outils de défense ?

**Rapport généré :**
```
Résumé
Les techniques identifiées concernent l'exploitation de vulnérabilités pour
compromettre les outils de défense (EDR, antivirus) et le firmware système,
permettant persistance et évasion.

Techniques d'attaque associées
- T1687 – Exploitation for Defense Impairment
- T1685 – Disable or Modify Tools
- T1542.001 – System Firmware

Recommandations
1. Surveiller les bulletins de sécurité pour les CVE liées aux EDR/antivirus.
2. Activer Secure Boot et la vérification d'intégrité du firmware.
...

Sources : T1687 (0.72) · T1685 (0.68) · T1542.001 (0.61)
```

## Structure du dépôt

```
cyberthreat-rag/
├── backend/                  # API FastAPI + pipeline RAG (voir backend/README.md)
│   ├── api/                  # Routes (auth, query, cves, techniques, reports)
│   ├── db/                   # Schéma PostgreSQL et connexion
│   ├── ingestion/             # NVD, CISA KEV, MITRE ATT&CK
│   ├── retrieval/             # Chunking, embeddings, recherche hybride, reranking
│   ├── generation/             # Génération de rapports via Groq
│   └── main.py                # Orchestrateur du pipeline d'ingestion
├── frontend/                 # Dashboard React (Dashboard, Assistant, Reports, Techniques, CVEs)
├── .github/workflows/         # Ingestion automatisée (GitHub Actions, cron)
└── README.md                 # Ce fichier
```

## Démarrage rapide

```bash
git clone https://github.com/masteroskaik/cyberthreat-rag.git

# Backend
cd cyberthreat-rag/backend
python -m venv venv && source venv/bin/activate   # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # renseigner les clés (voir GUIDE.txt)
python main.py         # ingestion initiale
uvicorn api.main:app --reload

# Frontend (nouveau terminal)
cd ../frontend
npm install
cp .env.example .env   # VITE_API_URL vers l'API locale ou déployée
npm run dev
```

Documentation détaillée : [`backend/README.md`](backend/README.md) et [`backend/GUIDE.txt`](backend/GUIDE.txt).

## Sécurité

- Authentification JWT sur toutes les routes sensibles
- Mots de passe hashés avec `bcrypt`, jamais stockés en clair
- Aucun secret commité (`.gitignore`, `.env.example`) — variables injectées via l'environnement d'exécution (local ou secrets Render/GitHub Actions)

## Difficultés techniques rencontrées

Quelques problèmes réels résolus pendant le développement (détaillés dans le rapport technique complet) :

- **Limite mémoire Render (512 Mo)** → migration des embeddings d'un modèle local (PyTorch) vers l'API Cohere
- **Index vectoriel entraîné sur une table vide** → reconstruction automatique (`REINDEX`) après chaque ingestion
- **0 % de correspondance avec CISA KEV** sur un échantillon aléatoire → ingestion ciblée des CVE listées dans KEV
- **Coupures réseau pendant l'ingestion** → logique de nouvelle tentative avec délai croissant

## Roadmap

- [x] Pipeline RAG complet (ingestion, recherche hybride, reranking, génération)
- [x] API sécurisée (JWT) et dashboard React
- [x] Déploiement complet (Render + Vercel + Neon)
- [x] Ingestion automatisée (GitHub Actions)
- [x] Export de rapports en Word
- [ ] Intégration MISP / AlienVault OTX (indicateurs de compromission)
- [ ] Graphique d'évolution temporelle des vulnérabilités
- [ ] Classement des vendeurs/produits les plus touchés
- [ ] Évaluation quantitative du RAG (Recall@K, Precision@K, Faithfulness)

## Auteur

**RAZAFIMAHATRATRA Livanirina Bernardin** (Liva)
M1 Intelligence Artificielle — ENI Fianarantsoa, Madagascar
[GitHub](https://github.com/masteroskaik)

## Licence

Distribué sous licence [MIT](backend/LICENSE).

---

*Ce projet utilise l'API NVD mais n'est ni endossé ni certifié par la NVD. Les données CISA KEV et MITRE ATT&CK sont utilisées à des fins éducatives et de démonstration technique.*
