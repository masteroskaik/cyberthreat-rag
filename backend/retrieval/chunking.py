"""
Construction des chunks textuels à partir des CVE, KEV et techniques ATT&CK
stockées en base, prêts à être vectorisés.

Approche volontairement simple ("from scratch") : un chunk = un enregistrement
enrichi de son contexte (statut KEV notamment), plutôt qu'un découpage par
taille de token. C'est adapté ici car chaque CVE/technique est déjà une unité
sémantique courte et cohérente.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import get_connection


def build_cve_chunks(conn) -> list:
    """Construit un chunk texte par CVE, enrichi du statut KEV si présent."""
    chunks = []

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.description, c.cvss_score, c.cvss_severity,
                   c.published_at, c.affected_products,
                   k.vulnerability_name, k.known_ransomware_use, k.required_action
            FROM cves c
            LEFT JOIN kev_entries k ON k.cve_id = c.id
            """
        )
        rows = cur.fetchall()

    for row in rows:
        (cve_id, description, cvss_score, cvss_severity, published_at,
         affected_products, kev_name, ransomware_use, required_action) = row

        text = f"CVE {cve_id}\n"
        text += f"Description : {description}\n"
        text += f"Score CVSS : {cvss_score} ({cvss_severity})\n"
        text += f"Publiée le : {published_at}\n"

        if affected_products:
            products = ", ".join(affected_products[:5]) if isinstance(affected_products, list) else str(affected_products)
            text += f"Produits affectés : {products}\n"

        is_kev = kev_name is not None
        text += f"Exploitée activement (CISA KEV) : {'oui' if is_kev else 'non'}\n"
        if is_kev:
            text += f"Nom KEV : {kev_name}\n"
            text += f"Utilisation ransomware connue : {ransomware_use}\n"
            text += f"Action recommandée : {required_action}\n"

        chunks.append({
            "source_type": "cve",
            "source_id": cve_id,
            "content": text,
            "metadata": {
                "cvss_score": float(cvss_score) if cvss_score else None,
                "cvss_severity": cvss_severity,
                "is_kev": is_kev,
            },
        })

    return chunks


def build_attack_chunks(conn) -> list:
    """Construit un chunk texte par technique MITRE ATT&CK."""
    chunks = []

    with conn.cursor() as cur:
        cur.execute("SELECT id, name, description, tactics FROM attack_techniques")
        rows = cur.fetchall()

    for technique_id, name, description, tactics in rows:
        tactics_str = ", ".join(tactics) if isinstance(tactics, list) else str(tactics)
        text = f"Technique ATT&CK {technique_id} : {name}\n"
        text += f"Tactiques associées : {tactics_str}\n"
        text += f"Description : {description[:1000]}\n"

        chunks.append({
            "source_type": "attack_technique",
            "source_id": technique_id,
            "content": text,
            "metadata": {"tactics": tactics},
        })

    return chunks


def build_all_chunks() -> list:
    """Construit l'ensemble des chunks (CVE + techniques ATT&CK)."""
    with get_connection() as conn:
        chunks = build_cve_chunks(conn) + build_attack_chunks(conn)

    print(f"{len(chunks)} chunks construits.")
    return chunks


if __name__ == "__main__":
    chunks = build_all_chunks()
    if chunks:
        print("\nExemple de chunk :\n")
        print(chunks[0]["content"])
