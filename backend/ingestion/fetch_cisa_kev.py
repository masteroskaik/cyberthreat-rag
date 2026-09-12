"""
Ingestion du catalogue CISA KEV (Known Exploited Vulnerabilities).
Flux JSON public, aucune clé API nécessaire.
"""

import sys
import os
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CISA_KEV_URL
from db.connection import get_connection


def fetch_kev_catalog() -> dict:
    """Télécharge le catalogue CISA KEV complet."""
    response = requests.get(CISA_KEV_URL, timeout=30)
    response.raise_for_status()
    return response.json()


def save_kev_entry(conn, entry: dict) -> None:
    """Insère ou met à jour une entrée KEV (la CVE existe déjà en base à ce stade)."""
    cve_id = entry.get("cveID")

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO kev_entries (cve_id, vulnerability_name, date_added,
                                      required_action, due_date, known_ransomware_use)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (cve_id) DO UPDATE SET
                vulnerability_name = EXCLUDED.vulnerability_name,
                required_action = EXCLUDED.required_action,
                due_date = EXCLUDED.due_date,
                known_ransomware_use = EXCLUDED.known_ransomware_use
            """,
            (
                cve_id,
                entry.get("vulnerabilityName"),
                entry.get("dateAdded"),
                entry.get("requiredAction"),
                entry.get("dueDate"),
                entry.get("knownRansomwareCampaignUse"),
            ),
        )


def ingest_cisa_kev() -> int:
    """Ingère les entrées KEV qui correspondent à des CVE déjà en base."""
    catalog = fetch_kev_catalog()
    vulnerabilities = catalog.get("vulnerabilities", [])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM cves")
            existing_ids = {row[0] for row in cur.fetchall()}

        relevant_entries = [e for e in vulnerabilities if e.get("cveID") in existing_ids]
        print(f"{len(relevant_entries)} entrées KEV correspondent à des CVE déjà en base (sur {len(vulnerabilities)} au total).")

        for entry in relevant_entries:
            save_kev_entry(conn, entry)

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM kev_entries")
            matched = cur.fetchone()[0]

    print(f"{matched} entrées KEV liées à des CVE en base.")
    return matched


if __name__ == "__main__":
    ingest_cisa_kev()
