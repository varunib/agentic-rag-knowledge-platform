from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("all-MiniLM-L6-v2")


def embed(texts):

    if isinstance(texts, str):
        texts = [texts]

    return embedder.encode(texts).tolist()