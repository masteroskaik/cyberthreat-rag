"""
Génération d'embeddings via l'API Cohere Embed (embed-v4.0).
Version corrigée : retry + pacing sur l'API, et re-indexation atomique
via table de staging (plus jamais de TRUNCATE sans protection).
"""

import sys
import os
import json
import time
import cohere

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COHERE_API_KEY, EMBEDDING_MODEL_NAME, EMBEDDING_DIM, check_required_env
from db.connection import get_connection
from retrieval.chunking import build_all_chunks

_client = None
_BATCH_LIMIT = 96

# Pacing : ~2 lots/min pour rester sous la limite de 100k tokens/min
_BATCH_PAUSE_SECONDS = 35


def get_embedding_client() -> cohere.ClientV2:
    global _client
    if _client is None:
        check_required_env("COHERE_API_KEY")
        _client = cohere.ClientV2(api_key=COHERE_API_KEY)
    return _client


def embed_texts(texts: list, input_type: str = "search_document", max_retries: int = 5) -> list:
    """
    Calcule les embeddings via l'API Cohere, avec :
    - retry sur erreur (429 = rate limit -> pause longue d'une fenêtre complète)
    - pause entre les lots pour ne pas dépasser la limite de tokens/minute
    """
    if not texts:
        return []

    client = get_embedding_client()
    all_embeddings = []

    for i in range(0, len(texts), _BATCH_LIMIT):
        batch = texts[i:i + _BATCH_LIMIT]

        for attempt in range(1, max_retries + 1):
            try:
                response = client.embed(
                    model=EMBEDDING_MODEL_NAME,
                    texts=batch,
                    input_type=input_type,
                    embedding_types=["float"],
                    output_dimension=EMBEDDING_DIM,
                )
                all_embeddings.extend(response.embeddings.float)
                break
            except Exception as e:
                msg = str(e).lower()
                if "rate limit" in msg or "429" in msg:
                    wait = 65
                else:
                    wait = 10 * attempt
                print(f"  Cohere embed erreur (tentative {attempt}/{max_retries}), pause {wait}s...")
                time.sleep(wait)
        else:
            raise RuntimeError(
                f"Échec embeddings sur le lot {i // _BATCH_LIMIT + 1} après {max_retries} tentatives."
            )

        time.sleep(_BATCH_PAUSE_SECONDS)

    return all_embeddings


def save_chunk_with_embedding(conn, chunk: dict, embedding: list) -> None:
    """Insère un chunk avec son embedding dans la table de staging."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chunks_new (source_type, source_id, content, embedding, metadata)
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
    Re-indexation ATOMIQUE :
    1. Embedding dans une table de staging (chunks_new) — la prod reste intacte.
    2. Swap de table en une seule transaction, sans TRUNCATE sur la table prod.
    3. Reconstruction de l'index ivfflat après le chargement.
    """
    chunks = build_all_chunks()
    if not chunks:
        print("Aucun chunk à indexer. As-tu bien lancé l'ingestion NVD/KEV/ATT&CK ?")
        return 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS chunks_new")
            cur.execute("CREATE TABLE chunks_new (LIKE chunks INCLUDING DEFAULTS)")
            cur.execute(f"ALTER TABLE chunks_new ALTER COLUMN embedding TYPE vector({EMBEDDING_DIM})")

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c["content"] for c in batch]
        embeddings = embed_texts(texts, input_type="search_document")

        with get_connection() as conn:
            for chunk, embedding in zip(batch, embeddings):
                save_chunk_with_embedding(conn, chunk, embedding)

        print(f"Indexé {min(i + batch_size, len(chunks))}/{len(chunks)} chunks.")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM chunks_new")
            staged = cur.fetchone()[0]

    if staged < len(chunks):
        raise RuntimeError(
            f"Staging incomplète ({staged}/{len(chunks)}) — swap annulé, la table de production reste intacte."
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("BEGIN")
            cur.execute("DROP INDEX IF EXISTS idx_chunks_embedding")
            cur.execute("ALTER TABLE IF EXISTS chunks RENAME TO chunks_old")
            cur.execute("ALTER TABLE chunks_new RENAME TO chunks")
            cur.execute("DROP TABLE IF EXISTS chunks_old")
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunks_embedding "
                "ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
            )
            cur.execute("COMMIT")

    print(f"{len(chunks)} chunks indexés avec succès (swap atomique effectué).")
    return len(chunks)


if __name__ == "__main__":
    index_all_chunks()
