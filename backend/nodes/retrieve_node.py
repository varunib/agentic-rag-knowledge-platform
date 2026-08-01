from services.retrieval_service import retrieve
from rag import build_context_with_citations


async def retrieve_node(state):

    docs, metas, ids, scores = await retrieve(
        state["question"],
        state["session_id"],
    )

    context, citations = build_context_with_citations(
        {
            "documents": [docs],
            "metadatas": [metas],
            "ids": [ids],
        },
        scores,
    )

    state["context"] = context
    state["citations"] = citations

    return state