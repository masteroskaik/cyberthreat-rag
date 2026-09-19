<div align="center">

# 🛡️ CyberThreat RAG

**Plateforme de Cyber Threat Intelligence pilotée par un système RAG construit from scratch**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?logo=postgresql&logoColor=white)](https://neon.tech)
[![Groq](https://img.shields.io/badge/LLM-Groq-F55036)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](#licence)
[![Status](https://img.shields.io/badge/Status-MVP%20actif-success)](#roadmap)

</div>

---

## Sommaire

- [Aperçu](#aperçu)
- [Pourquoi ce projet](#pourquoi-ce-projet)
- [Architecture](#architecture)
- [Stack technique](#stack-technique)
- [Exemple d'utilisation](#exemple-dutilisation)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Structure du projet](#structure-du-projet)
- [Sécurité](#sécurité)
- [Roadmap](#roadmap)
- [Licence](#licence)
- [Auteur](#auteur)
- [Avertissement](#avertissement)

## Aperçu

**CyberThreat RAG** agrège des données publiques de cybersécurité — vulnérabilités (NVD), exploitation active confirmée (CISA KEV) et techniques d'attaque (MITRE ATT&CK) — dans une base vectorielle interrogeable en langage naturel. Le système restitue des rapports d'analyse CTI structurés et **sourcés**, générés par un LLM à partir des documents les plus pertinents retrouvés par recherche hybride et reranking.

## Pourquoi ce projet

Ce projet a été conçu **sans framework RAG** (pas de LangChain, pas de LlamaIndex) afin de maîtriser et démontrer chaque brique du pipeline de bout en bout :

- Ingestion et normalisation de données depuis 3 API publiques hétérogènes
- Indexation vectorielle avec PostgreSQL + pgvector
- Recherche hybride (similarité vectorielle + full-text) fusionnée par Reciprocal Rank Fusion
- Reranking sémantique
- Génération augmentée par récupération (RAG), avec citation systématique des sources
- API sécurisée par authentification JWT

L'ensemble tourne sur des services **100 % gratuits**, sans carte bancaire.

## Architecture

```
┌─────────────┐   ┌─────────────┐   ┌──────────────┐
│     NVD     │   │  CISA KEV   │   │ MITRE ATT&CK │
└──────┬──────┘   └──────┬──────┘   └──────┬───────┘
       │                 │                 │
       └────────────────────────────────────┘
                          │
                 Ingestion & normalisation
                          │
                          ▼
              PostgreSQL + pgvector (Neon)
                          │
                Chunking & Embeddings
                    (bge-small-en-v1.5)
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
                   API FastAPI (JWT)
                          │
                          ▼
                  Dashboard React (à venir)
```

## Stack technique

| Composant            | Technologie                        | Coût    |
|-----------------------|-------------------------------------|---------|
| Base de données       | PostgreSQL + pgvector (Neon)        | Gratuit |
| Embeddings             | `BAAI/bge-small-en-v1.5` (local)     | Gratuit |
| Reranking              | Cohere Rerank (`rerank-v3.5`, API)   | Gratuit |
| Génération LLM         | Groq (`openai/gpt-oss-120b`)         | Gratuit |
| API                    | FastAPI + JWT                        | —       |
| Hébergement API        | Render                               | Gratuit |
| Frontend               | React (à venir)                      | —       |
| Hébergement Frontend   | Vercel (à venir)                     | Gratuit |

## Exemple d'utilisation

**Requête :**
> Quelles techniques MITRE ATT&CK sont liées à l'exploitation de vulnérabilités visant les outils de défense ?

**Rapport généré (extrait) :**
```
=== RAPPORT CTI ===

Résumé
Les techniques identifiées concernent l'exploitation de vulnérabilités
pour compromettre les outils de défense (EDR, antivirus) et le firmware
système, permettant persistance et évasion.

Techniques d'attaque associées
- T1687 – Exploitation for Defense Impairment
- T1685 – Disable or Modify Tools
- T1542.001 – System Firmware

Recommandations
1. Surveiller les bulletins de sécurité pour les CVE liées aux EDR/antivirus.
2. Activer Secure Boot et la vérification d'intégrité du firmware.
...

=== SOURCES ===
- attack_technique T1687 (score: 0.72)
- attack_technique T1685 (score: 0.68)
- attack_technique T1542.001 (score: 0.61)
```

## Prérequis

- Python 3.10 ou supérieur
- Un compte [Neon](https://neon.tech) (PostgreSQL managé avec pgvector) — gratuit, sans carte bancaire
- Une clé API [NVD](https://nvd.nist.gov/developers/request-an-api-key) — gratuite
- Une clé API [Groq](https://console.groq.com/keys) — gratuite
- Une clé API [Cohere](https://dashboard.cohere.com/api-keys) — gratuite

## Installation

```bash
git clone https://github.com/<ton-pseudo>/cyberthreat-rag.git
cd cyberthreat-rag/backend
python -m venv venv
source venv/bin/activate      # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Configuration

Renseigner les variables suivantes dans le fichier `.env` :

| Variable              | Description                                                |
|------------------------|--------------------------------------------------------------|
| `NVD_API_KEY`          | Clé API NVD                                                  |
| `DATABASE_URL`         | URL de connexion PostgreSQL (Neon), avec pgvector activé     |
| `GROQ_API_KEY`         | Clé API Groq                                                 |
| `COHERE_API_KEY`       | Clé API Cohere (reranking)                                   |
| `JWT_SECRET_KEY`       | Clé secrète pour signer les tokens JWT                       |
| `ADMIN_USERNAME`       | Nom d'utilisateur pour l'authentification à l'API            |
| `ADMIN_PASSWORD_HASH`  | Hash bcrypt du mot de passe admin                            |

Le fichier `GUIDE.txt` détaille pas à pas comment obtenir et générer chacune de ces valeurs.

## Utilisation

### Pipeline de données (ingestion, indexation, génération)

```bash
python main.py
```

Ou étape par étape :

```bash
python -m db.connection
python -m ingestion.fetch_nvd
python -m ingestion.fetch_cisa_kev
python -m ingestion.fetch_mitre_attack
python -m retrieval.embeddings
python -m generation.generate_report
```

### API

```bash
uvicorn api.main:app --reload
```

Documentation interactive : `http://127.0.0.1:8000/docs`

## Structure du projet

```
cyberthreat-rag/
├── backend/
│   ├── api/                  # API FastAPI (routes, auth JWT, schémas)
│   ├── db/                   # Connexion PostgreSQL et schéma SQL
│   ├── ingestion/            # Récupération des données NVD, CISA KEV, MITRE ATT&CK
│   ├── retrieval/            # Chunking, embeddings, recherche hybride, reranking
│   ├── generation/           # Génération de rapports CTI via Groq
│   ├── main.py               # Orchestrateur du pipeline complet
│   ├── generate_password_hash.py
│   ├── requirements.txt
│   └── GUIDE.txt             # Guide pas à pas de configuration
├── frontend/                 # Dashboard React (à venir)
└── README.md
```

## Sécurité

- Authentification par JWT sur les routes sensibles de l'API (`/query`, `/cves/{id}`)
- Mots de passe hashés avec `bcrypt`, jamais stockés en clair
- Aucune clé API ni secret n'est commité (voir `.gitignore` et `.env.example`)
- Variables sensibles injectées uniquement via l'environnement d'exécution (local `.env`, ou variables d'environnement Render en production)

## Roadmap

- [x] Ingestion NVD, CISA KEV, MITRE ATT&CK
- [x] Indexation vectorielle (PostgreSQL + pgvector)
- [x] Recherche hybride et reranking
- [x] Génération de rapports CTI sourcés
- [x] API FastAPI avec authentification JWT
- [ ] Dashboard React
- [ ] Déploiement (Render + Vercel)
- [ ] Conteneurisation Docker et CI/CD GitHub Actions
- [ ] Évaluation quantitative du RAG (Recall@K, Precision@K, MRR, Faithfulness)
- [ ] Monitoring (Prometheus / Grafana)

## Licence

Distribué sous licence [MIT](LICENSE).

## Auteur

**RAZAFIMAHATRATRA Livanirina Bernardin** (Liva) — M'ôskaik Studio
Étudiant en M1 Intelligence Artificielle, ENI Fianarantsoa, Madagascar

## Avertissement

Ce projet utilise l'API NVD mais n'est ni endossé ni certifié par la NVD. Les données CISA KEV et MITRE ATT&CK sont utilisées à des fins éducatives et de démonstration technique.
