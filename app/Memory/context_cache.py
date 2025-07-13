import faiss
from redis import Redis
from sentence_transformers import SentenceTransformer


class ContextCache:
    def __init__(self, r: Redis):
        self.r = r
        self.key = "context_list"
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def cache_docs(self, raw_docs: str):
        self.r.rpush(self.key, raw_docs)
        self.r.ltrim(self.key, -5, -1)

    def retrieve_context(self, search_term: str):
        context_list: list[str] = self.r.lrange(self.key, -5, -1)
        chunks = []
        for cont in context_list:
            words = cont.split()
            text = " ".join(words[:1000])
            chunks.append(text)

        if not chunks:
            return ""

        vectors = self.model.encode(chunks)
        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors)

        query_vector = self.model.encode([search_term])
        D, I = index.search(query_vector, 1)

        context = [
            context_list[i] for i, d in zip(I[0], D[0]) if i < len(chunks) and d < 1.2
        ]

        return context[0] if context else ""
