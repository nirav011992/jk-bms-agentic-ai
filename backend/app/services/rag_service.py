"""
RAG (Retrieval-Augmented Generation) service.
Handles document embeddings, vector search, and context retrieval.
"""
import numpy as np
import faiss
from typing import List, Optional
from sentence_transformers import SentenceTransformer

from app.core.logging import get_logger
from app.schemas.qa import DocumentExcerpt

logger = get_logger(__name__)


class RAGService:
    """Service for RAG-based document retrieval and Q&A."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG service with embedding model.

        Args:
            model_name: Name of the sentence transformer model
        """
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index: Optional[faiss.IndexFlatL2] = None
        self.document_chunks: List[dict] = []
        logger.info(f"Initialized RAG service with model: {model_name}")

    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            Numpy array of embeddings
        """
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            logger.info(f"Created embeddings for {len(texts)} texts")
            return embeddings
        except Exception as e:
            logger.error(f"Error creating embeddings: {str(e)}")
            raise

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks.

        Args:
            text: Input text
            chunk_size: Size of each chunk in characters
            overlap: Number of overlapping characters

        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap

        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks

    def build_index(self, documents: List[dict]) -> None:
        """
        Build FAISS index from documents.

        Args:
            documents: List of document dicts with 'id', 'filename', and 'content'
        """
        try:
            self.document_chunks = []
            all_chunks = []

            for doc in documents:
                chunks = self.chunk_text(doc['content'])
                for chunk in chunks:
                    self.document_chunks.append({
                        'document_id': doc['id'],
                        'filename': doc['filename'],
                        'content': chunk
                    })
                    all_chunks.append(chunk)

            if not all_chunks:
                logger.warning("No chunks to index")
                return

            embeddings = self.create_embeddings(all_chunks)

            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(embeddings.astype('float32'))

            logger.info(f"Built FAISS index with {len(all_chunks)} chunks from {len(documents)} documents")

        except Exception as e:
            logger.error(f"Error building index: {str(e)}")
            raise

    def search(self, query: str, k: int = 5) -> List[DocumentExcerpt]:
        """
        Search for relevant document chunks.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of DocumentExcerpt objects with relevance scores
        """
        try:
            if self.index is None or len(self.document_chunks) == 0:
                logger.warning("Index not built or empty")
                return []

            query_embedding = self.create_embeddings([query])
            distances, indices = self.index.search(query_embedding.astype('float32'), k)

            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.document_chunks):
                    chunk = self.document_chunks[idx]
                    relevance_score = 1.0 / (1.0 + distances[0][i])

                    results.append(DocumentExcerpt(
                        document_id=chunk['document_id'],
                        filename=chunk['filename'],
                        excerpt=chunk['content'],
                        relevance_score=float(relevance_score)
                    ))

            logger.info(f"Found {len(results)} relevant chunks for query: {query[:50]}...")
            return results

        except Exception as e:
            logger.error(f"Error searching index: {str(e)}")
            return []

    def get_context_for_question(self, query: str, k: int = 5) -> str:
        """
        Get combined context from top-k relevant documents.

        Args:
            query: Question/query
            k: Number of documents to retrieve

        Returns:
            Combined context string
        """
        excerpts = self.search(query, k)
        if not excerpts:
            return ""

        context_parts = [f"[From {exc.filename}]\n{exc.excerpt}" for exc in excerpts]
        return "\n\n".join(context_parts)


rag_service = RAGService()
