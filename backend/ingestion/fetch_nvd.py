"""
Ingestion des CVE depuis l'API NVD, avec stockage direct dans PostgreSQL.
"""

import sys
import os
import time
import requests
import psycopg2
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NVD_API_KEY, NVD_BASE_URL, check_required_env
from db.connection import get_connection


def fetch_cve_page(results_per_page: int = 50, start_index: int = 0,
                    pub_start_date: str = None, pub_end_date: str = None,
                    max_retries: int = 3) -> dict:
    """Interroge l'API NVD pour une page de résultats, filtrée sur une plage de dates de publication.
    Retente automatiquement en cas d'erreur réseau transitoire (SSL, timeout)."""
    headers = {"apiKey": NVD_API_KEY} if NVD_API_KEY else {}
    params = {"resultsPerPage": results_per_page, "startIndex": start_index}

    if pub_start_date and pub_end_date:
        params["pubStartDate"] = pub_start_date
        params["pubEndDate"] = pub_end_date

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(NVD_BASE_URL, headers=headers, params=params, timeout=30)

            if response.status_code == 403:
                raise RuntimeError("Accès refusé : vérifie ta clé API NVD.")
            if response.status_code == 429:
                time.sleep(10)
                continue
            response.raise_for_status()
            return response.json()

        except (requests.exceptions.ConnectionError, requests.exceptions.SSLError,
                requests.exceptions.Timeout) as e:
            wait = 3 * attempt
            print(f"  Erreur réseau (tentative {attempt}/{max_retries}), nouvelle tentative dans {wait}s...")
            time.sleep(wait)
            if attempt == max_retries:
                raise

    return {"vulnerabilities": []}


def parse_cve(cve_item: dict) -> dict:
    """Extrait les champs utiles d'un objet CVE brut."""
    cve = cve_item["cve"]

    description = next(
        (d["value"] for d in cve.get("descriptions", []) if d["lang"] == "en"),
        "",
    )

    metrics = cve.get("metrics", {})
    cvss_score, cvss_severity = None, None
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        if key in metrics:
            data = metrics[key][0]["cvssData"]
            cvss_score = data.get("baseScore")
            cvss_severity = metrics[key][0].get("baseSeverity", data.get("baseSeverity"))
            break

    affected_products = []
    for config in cve.get("configurations", []):
        for node in config.get("nodes", []):
            for cpe_match in node.get("cpeMatch", []):
                if cpe_match.get("vulnerable"):
                    affected_products.append(cpe_match.get("criteria"))

    return {
        "id": cve["id"],
        "description": description,
        "cvss_score": cvss_score,
        "cvss_severity": cvss_severity,
        "published_at": cve.get("published"),
        "last_modified_at": cve.get("lastModified"),
        "affected_products": affected_products[:10],
    }


def save_cve(conn, cve: dict, raw_data: dict) -> None:
    """Insère ou met à jour une CVE en base."""
    import json

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO cves (id, description, cvss_score, cvss_severity,
                               published_at, last_modified_at, affected_products, raw_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                description = EXCLUDED.description,
                cvss_score = EXCLUDED.cvss_score,
                cvss_severity = EXCLUDED.cvss_severity,
                last_modified_at = EXCLUDED.last_modified_at,
                affected_products = EXCLUDED.affected_products,
                raw_data = EXCLUDED.raw_data
            """,
            (
                cve["id"],
                cve["description"],
                cve["cvss_score"],
                cve["cvss_severity"],
                cve["published_at"],
                cve["last_modified_at"],
                json.dumps(cve["affected_products"]),
                json.dumps(raw_data),
            ),
        )


def fetch_cve_by_id(cve_id: str, max_retries: int = 3) -> dict:
    """Interroge l'API NVD pour une CVE précise, par son identifiant.
    Retente automatiquement en cas d'erreur réseau transitoire (SSL, timeout)."""
    headers = {"apiKey": NVD_API_KEY} if NVD_API_KEY else {}
    params = {"cveId": cve_id}

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(NVD_BASE_URL, headers=headers, params=params, timeout=30)

            if response.status_code == 403:
                raise RuntimeError("Accès refusé : vérifie ta clé API NVD.")
            if response.status_code == 429:
                time.sleep(10)
                continue
            response.raise_for_status()
            return response.json()

        except (requests.exceptions.ConnectionError, requests.exceptions.SSLError,
                requests.exceptions.Timeout) as e:
            last_error = e
            wait = 3 * attempt
            print(f"  Erreur réseau pour {cve_id} (tentative {attempt}/{max_retries}), nouvelle tentative dans {wait}s...")
            time.sleep(wait)

    print(f"  {cve_id} ignorée après {max_retries} tentatives échouées ({last_error}).")
    return {"vulnerabilities": []}


def save_cve_with_retry(cve: dict, raw_item: dict, max_retries: int = 3) -> bool:
    """Sauvegarde une CVE en base, avec nouvelles tentatives en cas de coupure Neon."""
    for attempt in range(1, max_retries + 1):
        try:
            with get_connection() as conn:
                save_cve(conn, cve, raw_item)
            return True
        except psycopg2.OperationalError as e:
            wait = 5 * attempt
            print(f"  Connexion à la base échouée (tentative {attempt}/{max_retries}), nouvelle tentative dans {wait}s...")
            time.sleep(wait)
    print(f"  {cve['id']} ignorée après {max_retries} tentatives de connexion échouées.")
    return False


def ingest_specific_cves(cve_ids: list) -> int:
    """
    Ingère une liste précise de CVE (par exemple celles listées dans le
    catalogue CISA KEV), une par une via l'API NVD. Les erreurs réseau
    ponctuelles (API NVD ou connexion à la base) n'interrompent pas le
    reste de l'ingestion.
    """
    check_required_env("NVD_API_KEY")
    count = 0
    skipped = 0

    for cve_id in cve_ids:
        data = fetch_cve_by_id(cve_id)
        vulnerabilities = data.get("vulnerabilities", [])
        if not vulnerabilities:
            skipped += 1
            continue

        cve = parse_cve(vulnerabilities[0])
        if save_cve_with_retry(cve, vulnerabilities[0]):
            count += 1
        else:
            skipped += 1

        if count % 20 == 0 and count > 0:
            print(f"{count}/{len(cve_ids)} CVE KEV ingérées...")

        time.sleep(1)

    print(f"{count} CVE (issues de KEV) ingérées avec succès ({skipped} ignorées).")
    return count


def ingest_nvd(total_cves: int = 200, page_size: int = 50, days_back: int = 120) -> int:
    """
    Ingère les CVE les plus récentes depuis NVD vers PostgreSQL, en filtrant
    sur les `days_back` derniers jours (l'API NVD limite chaque requête à
    une plage de 120 jours maximum).
    Pour un projet portfolio, 100 à 500 CVE suffisent largement.
    """
    check_required_env("NVD_API_KEY")
    count = 0
    start_index = 0

    pub_end_date = datetime.utcnow()
    pub_start_date = pub_end_date - timedelta(days=min(days_back, 120))
    pub_start_str = pub_start_date.strftime("%Y-%m-%dT%H:%M:%S.000")
    pub_end_str = pub_end_date.strftime("%Y-%m-%dT%H:%M:%S.000")

    while count < total_cves:
        print(f"Récupération des CVE {start_index} à {start_index + page_size} (période : {pub_start_date.date()} → {pub_end_date.date()})...")
        data = fetch_cve_page(
            results_per_page=page_size,
            start_index=start_index,
            pub_start_date=pub_start_str,
            pub_end_date=pub_end_str,
        )

        vulnerabilities = data.get("vulnerabilities", [])
        if not vulnerabilities:
            break

        with get_connection() as conn:
            for item in vulnerabilities:
                cve = parse_cve(item)
                save_cve(conn, cve, item)
                count += 1

        start_index += page_size
        time.sleep(6)

    print(f"{count} CVE ingérées avec succès.")
    return count


if __name__ == "__main__":
    ingest_nvd(total_cves=200)
