"""
Service for interacting with Hugging Face Chat Completions API (OpenAI-compatible).
Handles chat, summarization, review analysis, and Q&A.
"""

import httpx
import asyncio
from typing import List, Dict
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class HuggingFaceService:
    """Service for Hugging Face Chat Completions API."""

    def __init__(self):
        self.api_key = settings.HUGGINGFACE_API_KEY
        self.model = settings.HUGGINGFACE_MODEL

        self.api_url = settings.HUGGINGFACE_API_URL

        self.client = httpx.AsyncClient(timeout=120.0)

        logger.info("HuggingFaceService initialized using chat completions API")

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()

    # ------------------------------------------------------------------
    # Core Chat Completion
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate a chat completion using Hugging Face OpenAI-compatible API.
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False,
            }

            response = await self.client.post(
                self.api_url,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Hugging Face HTTP error: "
                f"{e.response.status_code} - {e.response.text}"
            )

            if e.response.status_code == 401:
                raise Exception("Invalid Hugging Face API key.")
            elif e.response.status_code == 429:
                raise Exception("Rate limit exceeded.")
            else:
                raise Exception(f"Hugging Face API error: {e.response.text}")

        except Exception as e:
            logger.error(f"Chat completion failed: {str(e)}")
            raise

    # ------------------------------------------------------------------
    # Backward-Compatible Wrapper (Prompt → Chat)
    # ------------------------------------------------------------------

    async def generate_completion(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """
        Backward-compatible text completion wrapper.
        """
        messages = [{"role": "user", "content": prompt}]
        return await self.generate_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    # ------------------------------------------------------------------
    # Business Use Cases
    # ------------------------------------------------------------------

    async def generate_book_summary(
        self,
        book_content: str,
        title: str,
        author: str,
    ) -> str:
        prompt = f"""
Provide a concise summary (3–5 sentences) of the following book.

Title: {title}
Author: {author}

Content:
{book_content[:3000]}
"""
        return await self.generate_completion(
            prompt=prompt,
            max_tokens=300,
            temperature=0.5,
        )

    async def generate_chunked_summary(
        self,
        book_content: str,
        title: str,
        author: str,
    ) -> str:
        """
        Generate summary from large documents using chunking + parallel processing.
        
        Process:
        1. Split content into chunks (preserving boundaries)
        2. Generate summaries for each chunk in parallel
        3. Combine chunk summaries into final summary
        """
        from app.utils.document_processor import TextChunker

        chunks = TextChunker.chunk_text(book_content, chunk_size=3500, overlap=200)

        if not chunks:
            return "Unable to generate summary from empty content."

        if len(chunks) == 1:
            # Single chunk, use regular summary
            return await self.generate_book_summary(book_content, title, author)

        # Generate summaries for all chunks in parallel
        try:
            chunk_summaries = await asyncio.gather(
                *[
                    self._summarize_single_chunk(chunk, title, author, i + 1, len(chunks))
                    for i, chunk in enumerate(chunks)
                ]
            )

            # Filter out None values from failed chunks
            chunk_summaries = [s for s in chunk_summaries if s is not None]

            if not chunk_summaries:
                raise Exception("All chunks failed to summarize")

            # Combine chunk summaries
            combined_text = "\n\n".join(chunk_summaries)

            # Generate final summary from chunk summaries
            final_prompt = f"""
Provide a comprehensive yet concise final summary (5–7 sentences) based on the following chunk summaries of a book.

Title: {title}
Author: {author}
Number of chunks processed: {len(chunks)}
Successfully summarized chunks: {len(chunk_summaries)}

Chunk Summaries:
{combined_text}

Create a cohesive final summary that captures the main themes and key points across all chunks.
"""
            final_summary = await self.generate_completion(
                prompt=final_prompt,
                max_tokens=400,
                temperature=0.5,
            )

            logger.info(f"Generated chunked summary for {title} from {len(chunks)} chunks")
            return final_summary

        except Exception as e:
            logger.error(f"Chunked summary generation failed: {str(e)}")
            raise

    async def _summarize_single_chunk(
        self,
        chunk: str,
        title: str,
        author: str,
        chunk_num: int,
        total_chunks: int,
    ) -> str:
        """Summarize a single chunk. Returns None if failed."""
        try:
            prompt = f"""
Summarize the following excerpt (chunk {chunk_num}/{total_chunks}) from a book.

Title: {title}
Author: {author}

Excerpt:
{chunk}

Provide a 2–3 sentence summary capturing the key points of this section.
"""
            return await self.generate_completion(
                prompt=prompt,
                max_tokens=150,
                temperature=0.5,
            )
        except Exception as e:
            logger.warning(f"Failed to summarize chunk {chunk_num}/{total_chunks}: {str(e)}")
            return None  # Skip this chunk on error

    async def generate_review_summary(self, reviews: List[dict]) -> str:
        if not reviews:
            return "No reviews available."

        reviews_text = "\n\n".join(
            f"Rating: {r['rating']}/5\nReview: {r['review_text']}"
            for r in reviews[:10]
        )

        prompt = f"""
Analyze the following book reviews and provide:
1. Common themes
2. Strengths
3. Weaknesses
4. Overall sentiment

Reviews:
{reviews_text}
"""

        return await self.generate_completion(
            prompt=prompt,
            max_tokens=400,
            temperature=0.5,
        )

    async def answer_question(self, question: str, context: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that answers questions "
                    "based strictly on the provided context."
                ),
            },
            {
                "role": "user",
                "content": f"""
Context:
{context}

Question:
{question}
""",
            },
        ]

        return await self.generate_chat_completion(
            messages=messages,
            max_tokens=400,
            temperature=0.3,
        )


# Singleton instance
huggingface_service = HuggingFaceService()
