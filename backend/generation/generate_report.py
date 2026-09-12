"""
Génération d'un rapport de Cyber Threat Intelligence sourcé, à partir des
chunks retrouvés et rerankés, via l'API Groq (gratuite).
"""

import sys
import os
from groq import Groq

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GROQ_API_KEY, GROQ_MODEL_NAME, check_required_env
from retrieval.hybrid_search import hybrid_search
from retrieval.reranker import rerank

SYSTEM_PROMPT = """Tu es un analyste en Cyber Threat Intelligence (CTI).
Tu réponds UNIQUEMENT à partir du contexte fourni ci-dessous.
Si le contexte ne contient pas l'information demandée, dis-le clairement
plutôt que d'inventer une réponse.
Cite systématiquement les identifiants (CVE-XXXX-XXXXX, T-XXXX) des sources
que tu utilises dans ta réponse.
Structure ta réponse : résumé, vulnérabilités concernées, techniques
d'attaque associées si pertinent, recommandations."""


def build_context(chunks: list) -> str:
    """Assemble les chunks rerankés en un contexte textuel pour le prompt."""
    parts = []
    for chunk in chunks:
        parts.append(f"[Source: {chunk['source_type']} {chunk['source_id']}]\n{chunk['content']}")
    return "\n\n---\n\n".join(parts)


def generate_cti_report(question: str, top_k_retrieval: int = 20, top_n_context: int = 5) -> dict:
    """
    Pipeline complet de génération : recherche hybride -> reranking -> LLM.
    Retourne le rapport généré ET les sources utilisées (pour traçabilité).
    """
    check_required_env("GROQ_API_KEY")

    candidates = hybrid_search(question, top_k=top_k_retrieval)
    top_chunks = rerank(question, candidates, top_n=top_n_context)

    if not top_chunks:
        return {
            "answer": "Aucune information pertinente trouvée dans la base pour cette question.",
            "sources": [],
        }

    context = build_context(top_chunks)

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Contexte :\n{context}\n\nQuestion : {question}"},
        ],
        temperature=0.2,
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "sources": [
            {"type": c["source_type"], "id": c["source_id"], "score": c["rerank_score"]}
            for c in top_chunks
        ],
    }


if __name__ == "__main__":
    question = "Quelles sont les vulnérabilités critiques activement exploitées récemment ?"
    result = generate_cti_report(question)

    print("=== RAPPORT CTI ===\n")
    print(result["answer"])
    print("\n=== SOURCES ===")
    for s in result["sources"]:
        print(f"- {s['type']} {s['id']} (score: {s['score']:.4f})")
