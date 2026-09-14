"""
Orchestrateur du pipeline MVP CyberThreat RAG.
Exécute toutes les étapes dans l'ordre : schéma -> ingestion -> indexation
-> exemple de génération de rapport.

Usage :
    python main.py
"""

import sys

from db.connection import init_schema, get_connection
from ingestion.fetch_nvd import ingest_nvd, ingest_specific_cves
from ingestion.fetch_cisa_kev import ingest_cisa_kev, get_recent_kev_cve_ids
from ingestion.fetch_mitre_attack import ingest_mitre_attack
from retrieval.embeddings import index_all_chunks
from generation.generate_report import generate_cti_report


def log_ingestion(source: str, records_count: int) -> None:
    """Enregistre la date et le volume de la dernière ingestion réussie pour une source."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ingestion_log (source, last_run_at, records_count)
                VALUES (%s, NOW(), %s)
                ON CONFLICT (source) DO UPDATE SET
                    last_run_at = NOW(),
                    records_count = EXCLUDED.records_count
                """,
                (source, records_count),
            )


def run_pipeline():
    print("\n========== ÉTAPE 1/5 : Initialisation du schéma ==========")
    init_schema()

    print("\n========== ÉTAPE 2/5 : Ingestion NVD (CVE) ==========")
    print("-- 100 CVE récentes (120 derniers jours) --")
    n1 = ingest_nvd(total_cves=100)

    print("-- 150 CVE listées dans CISA KEV (garantit des correspondances) --")
    kev_cve_ids = get_recent_kev_cve_ids(count=150)
    n2 = ingest_specific_cves(kev_cve_ids)
    log_ingestion("nvd", (n1 or 0) + (n2 or 0))

    print("\n========== ÉTAPE 3/5 : Ingestion CISA KEV ==========")
    n_kev = ingest_cisa_kev()
    log_ingestion("cisa_kev", n_kev or 0)

    print("\n========== ÉTAPE 4/5 : Ingestion MITRE ATT&CK ==========")
    try:
        n_attack = ingest_mitre_attack()
        log_ingestion("mitre_attack", n_attack or 0)
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
