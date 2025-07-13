from Memory.context_cache import ContextCache
from redis import Redis
from Schemas.schemas import State
from utils.Retrieval import RetrieveData


class Tathya:
    def __init__(self, r: Redis):
        self.r = r
        self.cc = ContextCache(r=self.r)

    def tathya_provider(self, state: State) -> State:
        # Get search term from query
        rd = RetrieveData(question=state["query"])
        search_term = rd.extract_meaning()

        # Check Redis cache
        context = self.cc.retrieve_context(search_term=search_term)
        if not context.strip():
            print("No Context found in cache!! Fetching context...")

            raw_doc = rd.load_context_via_wiki(search_term)
            if raw_doc == "Page not found!":
                while True:
                    print("No Tathya found on the question...")
                    choice=input("Do you want to retrieve the context manually? (Y/N)")
                    if choice.lower().strip() == 'y':
                        search_term = input(
                        "Give the topic you wanna know about -> "
                        )
                        raw_doc = rd.load_context_via_wiki(search_term)
                        if not raw_doc == "Page not found!":
                            break
                    else:
                        return state

            self.cc.cache_docs(raw_docs=raw_doc)
            # context = self.cc.retrieve_context(search_term=search_term)
            context = raw_doc

        # Retrieve final context with similarity
        indexer = rd.create_FAISS_index(docs=context)
        retrieve_info = rd.retrieve_docs(indexer=indexer)

        docs = retrieve_info["docs"]
        scores = retrieve_info["scores"]

        satya_tathya = "\n".join(
            [doc.page_content for doc, score in zip(docs, scores) if score < 0.9]
        )

        state["context"] = satya_tathya if satya_tathya else None
        return state
