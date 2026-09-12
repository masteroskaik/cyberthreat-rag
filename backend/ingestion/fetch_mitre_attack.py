"""
Ingestion des techniques MITRE ATT&CK (format STIX).
Fichier public sur GitHub, aucune clé API nécessaire.

Attention : le fichier enterprise-attack.json fait plusieurs dizaines de Mo,
le téléchargement peut prendre un moment selon la connexion.
"""

import sys
import os
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MITRE_ATTACK_URL
from db.connection import get_connection


def fetch_attack_bundle() -> dict:
    """Télécharge le bundle STIX complet d'ATT&CK Enterprise."""
    response = requests.get(MITRE_ATTACK_URL, timeout=120)
    response.raise_for_status()
    return response.json()


def extract_technique_id(stix_object: dict) -> str:
    """Extrait l'identifiant ATT&CK (ex: T1059) depuis les external_references."""
    for ref in stix_object.get("external_references", []):
        if ref.get("source_name") == "mitre-attack":
            return ref.get("external_id")
    return None


def parse_techniques(bundle: dict) -> list:
    """Filtre et transforme les objets STIX de type 'attack-pattern' (techniques)."""
    techniques = []

    for obj in bundle.get("objects", []):
        if obj.get("type") != "attack-pattern":
            continue
        if obj.get("revoked") or obj.get("x_mitre_deprecated"):
            continue

        technique_id = extract_technique_id(obj)
        if not technique_id:
            continue

        tactics = [
            phase["phase_name"]
            for phase in obj.get("kill_chain_phases", [])
            if phase.get("kill_chain_name") == "mitre-attack"
        ]

        techniques.append(
            {
                "id": technique_id,
                "name": obj.get("name", ""),
                "description": obj.get("description", ""),
                "tactics": tactics,
            }
        )

    return techniques


def save_techniques_batch(conn, techniques: list) -> None:
    import json
    import psycopg2.extras

    rows = [
        (t["id"], t["name"], t["description"], json.dumps(t["tactics"]))
        for t in techniques
    ]

    with conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO attack_techniques (id, name, description, tactics)
            VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                tactics = EXCLUDED.tactics
            """,
            rows,
        )


def ingest_mitre_attack() -> int:
    """Ingère toutes les techniques ATT&CK Enterprise en base."""
    print("Téléchargement du bundle MITRE ATT&CK (peut prendre 1-2 minutes)...")
    bundle = fetch_attack_bundle()

    techniques = parse_techniques(bundle)
    print(f"{len(techniques)} techniques extraites, insertion en base...")

    with get_connection() as conn:
        save_techniques_batch(conn, techniques)

    print(f"{len(techniques)} techniques ATT&CK ingérées avec succès.")
    return len(techniques)


if __name__ == "__main__":
    ingest_mitre_attack()
