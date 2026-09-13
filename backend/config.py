"""
Configuration centralisée du projet CyberThreat RAG.
Charge les variables d'environnement depuis le fichier .env.
"""

import os
from dotenv import load_dotenv

load_dotenv()

NVD_API_KEY = os.getenv("NVD_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

NVD_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
MITRE_ATTACK_URL = (
    "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
)

EMBEDDING_MODEL_NAME = "embed-v4.0"
EMBEDDING_DIM = 256

RERANKER_MODEL_NAME = "rerank-v3.5"

GROQ_MODEL_NAME = "openai/gpt-oss-120b"

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 60

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")


def check_required_env(*keys: str) -> None:
    """Vérifie que les variables d'environnement nécessaires sont bien définies."""
    missing = [k for k in keys if not globals().get(k)]
    if missing:
        raise EnvironmentError(
            f"Variables d'environnement manquantes dans .env : {', '.join(missing)}"
        )
