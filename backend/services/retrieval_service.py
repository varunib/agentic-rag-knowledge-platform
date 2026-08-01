from rag import retrieve_chunks
from rag import build_context_with_citations


async def retrieve(question, session_id, search_all=False):

    docs, metas, ids, scores = await retrieve_chunks(
        question=question,
        session_id=session_id,
        search_all=search_all,
    )

    context, citations = build_context_with_citations(
        {
            "documents": [docs],
            "metadatas": [metas],
            "ids": [ids],
        },
        scores,
    )

    return {
        "context": context,
        "citations": citations,
        "scores": scores,
        "documents": docs,
    }