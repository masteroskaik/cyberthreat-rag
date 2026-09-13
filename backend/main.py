"""
Orchestrateur du pipeline MVP CyberThreat RAG.
Exécute toutes les étapes dans l'ordre : schéma -> ingestion -> indexation
-> exemple de génération de rapport.

Usage :
    python main.py
"""

import sys

from db.connection import init_schema
from ingestion.fetch_nvd import ingest_nvd, ingest_specific_cves
from ingestion.fetch_cisa_kev import ingest_cisa_kev, get_recent_kev_cve_ids
from ingestion.fetch_mitre_attack import ingest_mitre_attack
from retrieval.embeddings import index_all_chunks
from generation.generate_report import generate_cti_report


def run_pipeline():
    print("\n========== ÉTAPE 1/5 : Initialisation du schéma ==========")
    init_schema()

    print("\n========== ÉTAPE 2/5 : Ingestion NVD (CVE) ==========")
    print("-- 100 CVE récentes (120 derniers jours) --")
    ingest_nvd(total_cves=100)

    print("-- 150 CVE listées dans CISA KEV (garantit des correspondances) --")
    kev_cve_ids = get_recent_kev_cve_ids(count=150)
    ingest_specific_cves(kev_cve_ids)

    print("\n========== ÉTAPE 3/5 : Ingestion CISA KEV ==========")
    ingest_cisa_kev()

    print("\n========== ÉTAPE 4/5 : Ingestion MITRE ATT&CK ==========")
    try:
        ingest_mitre_attack()
    except Exception as e:
        print(f"Ingestion ATT&CK échouée (non bloquant pour le MVP) : {e}")

    print("\n========== ÉTAPE 5/5 : Chunking + Embeddings ==========")
    index_all_chunks()

    print("\n========== TEST : Génération d'un rapport CTI ==========")
    question = "Quelles sont les vulnérabilités critiques activement exploitées récemment ?"
    result = generate_cti_report(question)

    print("\n=== RAPPORT CTI ===\n")
    print(result["answer"])
    print("\n=== SOURCES ===")
    for s in result["sources"]:
        print(f"- {s['type']} {s['id']} (score: {s['score']:.4f})")


if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        print(f"\n❌ Erreur dans le pipeline : {e}")
        sys.exit(1)
