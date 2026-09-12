"""
Recherche hybride : combine la recherche vectorielle (similarité cosinus via
pgvector) et la recherche full-text (mots-clés via tsvector PostgreSQL),
fusionnées par Reciprocal Rank Fusion (RRF).

RRF est une méthode simple et robuste, codée ici "from scratch" plutôt que
via une librairie, pour bien montrer la logique de fusion.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.connection import get_connection
from retrieval.embeddings import embed_texts


def vector_search(conn, query_embedding: list, top_k: int = 20) -> list:
    """Recherche par similarité cosinus (distance <=> de pgvector)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, source_type, source_id, content,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM chunks
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, top_k),
        )
        return cur.fetchall()


def keyword_search(conn, query_text: str, top_k: int = 20) -> list:
    """Recherche full-text PostgreSQL (ts_rank)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, source_type, source_id, content,
                   ts_rank(content_tsv, plainto_tsquery('english', %s)) AS rank
            FROM chunks
            WHERE content_tsv @@ plainto_tsquery('english', %s)
            ORDER BY rank DESC
            LIMIT %s
            """,
            (query_text, query_text, top_k),
        )
        return cur.fetchall()


def reciprocal_rank_fusion(vector_results: list, keyword_results: list, k: int = 60) -> list:
    """
    Fusionne deux classements avec la formule RRF :
        score(doc) = somme( 1 / (k + rang(doc)) ) sur chaque classement où il apparaît

    k=60 est la valeur classique recommandée dans la littérature RRF.
    """
    scores = {}
    content_by_id = {}

    for rank, row in enumerate(vector_results):
        chunk_id = row[0]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
        content_by_id[chunk_id] = row

    for rank, row in enumerate(keyword_results):
        chunk_id = row[0]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
        content_by_id[chunk_id] = row

    ranked_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

    return [
        {
            "id": cid,
            "source_type": content_by_id[cid][1],
            "source_id": content_by_id[cid][2],
            "content": content_by_id[cid][3],
            "fusion_score": scores[cid],
        }
        for cid in ranked_ids
    ]


def hybrid_search(query: str, top_k: int = 20) -> list:
    """Point d'entrée principal : recherche hybride vectorielle + mots-clés."""
    query_embedding = embed_texts([query])[0]

    with get_connection() as conn:
        vector_results = vector_search(conn, query_embedding, top_k=top_k)
        keyword_results = keyword_search(conn, query, top_k=top_k)

    return reciprocal_rank_fusion(vector_results, keyword_results)


if __name__ == "__main__":
    results = hybrid_search("remote code execution vulnerability actively exploited", top_k=10)
    for r in results[:5]:
        print(f"[{r['fusion_score']:.4f}] {r['source_type']} {r['source_id']}")
