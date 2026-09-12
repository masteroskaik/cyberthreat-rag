"""
Génération d'embeddings avec sentence-transformers (modèle local, gratuit)
et stockage dans la table `chunks` (colonne vector de pgvector).
"""

import sys
import os
import json
from sentence_transformers import SentenceTransformer

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EMBEDDING_MODEL_NAME
from db.connection import get_connection
from retrieval.chunking import build_all_chunks

_model = None


def get_embedding_model() -> SentenceTransformer:
    """Charge le modèle d'embedding une seule fois (mise en cache globale)."""
    global _model
    if _model is None:
        print(f"Chargement du modèle d'embedding {EMBEDDING_MODEL_NAME}...")
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def embed_texts(texts: list) -> list:
    """Calcule les embeddings pour une liste de textes."""
    model = get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    return embeddings.tolist()


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


def index_all_chunks(batch_size: int = 32) -> int:
    """
    Pipeline complet : construit les chunks, calcule leurs embeddings,
    et les stocke en base. Vide la table chunks avant de recommencer,
    pour éviter les doublons si on relance le script.

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

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c["content"] for c in batch]
        embeddings = embed_texts(texts)

        with get_connection() as conn:
            for chunk, embedding in zip(batch, embeddings):
                save_chunk_with_embedding(conn, chunk, embedding)

        print(f"Indexé {min(i + batch_size, len(chunks))}/{len(chunks)} chunks.")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("REINDEX INDEX idx_chunks_embedding")
            print("Index ivfflat reconstruit après chargement des données.")

    print(f"{len(chunks)} chunks indexés avec succès.")
    return len(chunks)


if __name__ == "__main__":
    index_all_chunks()
