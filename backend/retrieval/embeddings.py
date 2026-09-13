"""
Génération d'embeddings via l'API Cohere Embed (embed-v4.0), gratuite
jusqu'à 1000 requêtes/mois, et stockage dans la table `chunks`
(colonne vector de pgvector).

Choix d'une API plutôt qu'un modèle local : évite de charger PyTorch en
mémoire dans le service API en production, ce qui dépasserait les 512 Mo
de RAM disponibles sur les plateformes d'hébergement gratuites (ex: Render
free tier).
"""

import sys
import os
import json
import cohere

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COHERE_API_KEY, EMBEDDING_MODEL_NAME, EMBEDDING_DIM, check_required_env
from db.connection import get_connection
from retrieval.chunking import build_all_chunks

_client = None
_BATCH_LIMIT = 96


def get_embedding_client() -> cohere.ClientV2:
    global _client
    if _client is None:
        check_required_env("COHERE_API_KEY")
        _client = cohere.ClientV2(api_key=COHERE_API_KEY)
    return _client


def embed_texts(texts: list, input_type: str = "search_document") -> list:
    """
    Calcule les embeddings pour une liste de textes via l'API Cohere.
    input_type doit être "search_document" pour indexer des chunks,
    ou "search_query" pour embedder une question posée par l'utilisateur.
    """
    if not texts:
        return []

    client = get_embedding_client()
    all_embeddings = []

    for i in range(0, len(texts), _BATCH_LIMIT):
        batch = texts[i:i + _BATCH_LIMIT]
        response = client.embed(
            model=EMBEDDING_MODEL_NAME,
            texts=batch,
            input_type=input_type,
            embedding_types=["float"],
            output_dimension=EMBEDDING_DIM,
        )
        all_embeddings.extend(response.embeddings.float)

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
    Pipeline complet : construit les chunks, calcule leurs embeddings via
    Cohere, et les stocke en base. Vide la table chunks avant de
    recommencer, pour éviter les doublons si on relance le script.

    batch_size est aligné sur la limite de l'API Cohere (96 textes max
    par appel) pour minimiser le nombre de requêtes.

    Une connexion séparée est ouverte pour chaque lot (plutôt qu'une
    connexion unique pour toute la boucle), pour éviter les coupures
    du pooler Neon sur les gros volumes / connexions lentes.
    """
    chunks = build_all_chunks()
    if not chunks:
        print("Aucun chunk à indexer. As-tu bien lancé l'ingestion NVD/KEV/ATT&CK ?")
        return 0

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE chunks")
            cur.execute("DROP INDEX IF EXISTS idx_chunks_embedding")
            cur.execute(f"ALTER TABLE chunks ALTER COLUMN embedding TYPE vector({EMBEDDING_DIM})")

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
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_chunks_embedding "
                "ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
            )
            print("Index ivfflat reconstruit après chargement des données.")

    print(f"{len(chunks)} chunks indexés avec succès.")
    return len(chunks)


if __name__ == "__main__":
    index_all_chunks()
