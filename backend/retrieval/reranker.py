"""
Reranking des résultats de la recherche hybride via l'API Cohere Rerank
(rerank-v3.5), gratuite jusqu'à 1000 requêtes/mois.

Différence avec les embeddings classiques : le reranker évalue la paire
(requête, document) ensemble, ce qui est plus précis mais plus lent — d'où
son usage seulement sur les ~20 meilleurs résultats du retrieval, pas sur
toute la base.

Choix d'une API plutôt qu'un modèle local : évite de charger un modèle
volumineux (~1.1 Go) en mémoire, ce qui serait incompatible avec les
limites de RAM des plateformes d'hébergement gratuites (ex: 512 Mo sur
Render free tier).
"""

import sys
import os
import cohere

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COHERE_API_KEY, RERANKER_MODEL_NAME, check_required_env

_client = None


def get_client() -> cohere.Client:
    global _client
    if _client is None:
        check_required_env("COHERE_API_KEY")
        _client = cohere.Client(api_key=COHERE_API_KEY)
    return _client


def rerank(query: str, candidates: list, top_n: int = 5) -> list:
    """
    Réordonne les candidats selon leur pertinence réelle par rapport à la requête.

    candidates : liste de dicts avec au moins une clé "content"
    """
    if not candidates:
        return []

    client = get_client()
    documents = [c["content"] for c in candidates]

    response = client.rerank(
        model=RERANKER_MODEL_NAME,
        query=query,
        documents=documents,
        top_n=min(top_n, len(documents)),
    )

    ranked = []
    for result in response.results:
        candidate = candidates[result.index]
        candidate["rerank_score"] = float(result.relevance_score)
        ranked.append(candidate)

    return ranked


if __name__ == "__main__":
    from retrieval.hybrid_search import hybrid_search

    query = "remote code execution vulnerability actively exploited"
    candidates = hybrid_search(query, top_k=20)
    top_results = rerank(query, candidates, top_n=5)

    for r in top_results:
        print(f"[{r['rerank_score']:.4f}] {r['source_type']} {r['source_id']}")
