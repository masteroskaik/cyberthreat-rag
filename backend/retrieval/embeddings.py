"""
Génération d'embeddings via l'API Cohere Embed (embed-v4.0), gratuite
en mode essai, et stockage dans la table `chunks` (colonne vector de pgvector).

Choix d'une API plutôt qu'un modèle local : évite de charger PyTorch en
mémoire dans le service API en production, ce qui dépasserait les 512 Mo
de RAM disponibles sur les plateformes d'hébergement gratuites (ex: Render
free tier).

Le mode essai de Cohere est limité en débit (tokens par minute) : les
appels sont espacés et retentés automatiquement en cas d'erreur 429.
"""

import sys
import os
import json
import time
import cohere
from cohere.errors import TooManyRequestsError

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COHERE_API_KEY, EMBEDDING_MODEL_NAME, EMBEDDING_DIM, check_required_env
from db.connection import get_connection
from retrieval.chunking import build_all_chunks

_client = None
_BATCH_LIMIT = 96
_BATCH_PAUSE_SECONDS = 25
_MAX_RETRIES = 6
_RETRY_WAIT_SECONDS = 60


def get_embedding_client() -> cohere.ClientV2:
    global _client
    if _client is None:
        check_required_env("COHERE_API_KEY")
        _client = cohere.ClientV2(api_key=COHERE_API_KEY)
    return _client


def _embed_batch_with_retry(client, batch: list, input_type: str):
    """Appelle l'API Cohere, avec nouvelles tentatives si la limite de débit est atteinte."""
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            return client.embed(
                model=EMBEDDING_MODEL_NAME,
                texts=batch,
                input_type=input_type,
                embedding_types=["float"],
                output_dimension=EMBEDDING_DIM,
            )
        except TooManyRequestsError:
            if attempt == _MAX_RETRIES:
                raise
            wait = _RETRY_WAIT_SECONDS
            print(f"  Limite de débit Cohere atteinte (tentative {attempt}/{_MAX_RETRIES}), pause de {wait}s...")
            time.sleep(wait)


def embed_texts(texts: list, input_type: str = "search_document", pause_between_batches: bool = False) -> list:
    """
    Calcule les embeddings pour une liste de textes via l'API Cohere.
    input_type doit être "search_document" pour indexer des chunks,
    ou "search_query" pour embedder une question posée par l'utilisateur.
    pause_between_batches espace les lots (utile pour l'ingestion en masse,
    inutile pour une simple question utilisateur).
    """
    if not texts:
        return []

    client = get_embedding_client()
    all_embeddings = []
    total_batches = (len(texts) + _BATCH_LIMIT - 1) // _BATCH_LIMIT

    for batch_index, i in enumerate(range(0, len(texts), _BATCH_LIMIT), start=1):
        batch = texts[i:i + _BATCH_LIMIT]
        response = _embed_batch_with_retry(client, batch, input_type)
        all_embeddings.extend(response.embeddings.float)

        if total_batches > 1:
            print(f"Embeddings calculés : {min(i + _BATCH_LIMIT, len(texts))}/{len(texts)}")

        if pause_between_batches and batch_index < total_batches:
            time.sleep(_BATCH_PAUSE_SECONDS)

    return all_embeddings


def save_chunk_with_embedding(conn, chunk: dict, embedding: list) -> None:
    """Insère un chunk avec son embedding dans la base."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chunks (source_type, source_id, content, embedding, metadata)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                chunk["source_type"],
                chunk["source_id"],
                chunk["content"],
                embedding,
                json.dumps(chunk["metadata"]),
            ),
        )


def index_all_chunks(batch_size: int = 90) -> int:
    """
    Pipeline complet : construit les chunks, calcule TOUS leurs embeddings
    via Cohere, puis seulement ensuite remplace le contenu de la table
    chunks. Ainsi, si le calcul des embeddings échoue en cours de route,
    l'ancien index reste intact et l'application continue de fonctionner.

    Une connexion séparée est ouverte pour chaque lot d'insertion (plutôt
    qu'une connexion unique), pour éviter les coupures du pooler Neon.
    """
    chunks = build_all_chunks()
    if not chunks:
        print("Aucun chunk à indexer. As-tu bien lancé l'ingestion NVD/KEV/ATT&CK ?")
        return 0

    print(f"{len(chunks)} chunks à vectoriser...")
    texts = [c["content"] for c in chunks]
    embeddings = embed_texts(texts, input_type="search_document", pause_between_batches=True)

    print("Embeddings terminés, remplacement de l'index en base...")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE chunks")
            cur.execute("DROP INDEX IF EXISTS idx_chunks_embedding")
            cur.execute(f"ALTER TABLE chunks ALTER COLUMN embedding TYPE vector({EMBEDDING_DIM})")

    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]

        with get_connection() as conn:
            for chunk, embedding in zip(batch_chunks, batch_embeddings):
                save_chunk_with_embedding(conn, chunk, embedding)

        print(f"Inséré {min(i + batch_size, len(chunks))}/{len(chunks)} chunks.")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunks_embedding "
                "ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
            )
            print("Index ivfflat reconstruit après chargement des données.")

    print(f"{len(chunks)} chunks indexés avec succès.")
    return len(chunks)


if __name__ == "__main__":
    index_all_chunks()
