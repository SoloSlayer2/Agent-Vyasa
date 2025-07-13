import re
from typing import Dict, List

import wikipedia
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from utils.ContextCheckers import KeyWordExtractor, NameEntityRecognition


class WikiLoader:
    def __init__(self, search_term: str, lang: str = "en"):
        self.search_term = search_term
        wikipedia.set_lang(lang)

    def wikiSearch(self) -> str:
        try:
            page = wikipedia.page(self.search_term, auto_suggest=True)
            return page.content
        except wikipedia.exceptions.DisambiguationError as e:
            return f"DisambiguationError: '{self.search_term}' may refer to multiple pages: {e.options}"
        except wikipedia.exceptions.PageError:
            return "Page not found!"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"


def clean_text(text):
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Convert to lowercase
    text = text.lower()

    return text


class RetrieveData:
    def __init__(self, question: str):
        self.question = question
        self.embed_fn = OllamaEmbeddings(model="nomic-embed-text")

    def extract_meaning(self) -> str:
        """This function extracts the true meaning behind the question using Name Entity Recognition and Keyword Extraction Techniques"""
        ner_words = NameEntityRecognition(self.question).nerPipeline_and_Check()
        keywords = KeyWordExtractor(self.question).keywordExtractor()
        keyword_strings = [kw[0] for kw in keywords]
        search_term = (
            " ".join(ner_words + keyword_strings)
            if ner_words or keywords
            else self.question
        )
        return search_term

    def load_context_via_wiki(self, search_term: str) -> str:
        """This Function loads the context based on the given search_term"""
        raw_doc = WikiLoader(search_term).wikiSearch()
        if not raw_doc.strip():
            print("🤖 Bot: Couldn't find relevant content for your query.")
        return raw_doc

    def create_FAISS_index(self, docs: str) -> FAISS:
        """This function returns a FAISS indexer that can be later used for indexing"""
        cleaned_docs = clean_text(docs)
        chunks = RecursiveCharacterTextSplitter().split_text(cleaned_docs)
        indexer = FAISS.from_texts(chunks, embedding=self.embed_fn)
        return indexer

    def retrieve_docs(self, indexer: FAISS, top_k=3) -> Dict[str, List]:
        """Retrieve the top k documents that matches the context of the question"""
        results = indexer.similarity_search_with_score(query=self.question, k=top_k)
        docs = [doc for doc, _ in results]
        scores = [score for _, score in results]
        return {"docs": docs, "scores": scores}
