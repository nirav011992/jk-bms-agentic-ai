"""
Service for interacting with Llama3 model via OpenRouter.
Handles text generation, summarization, and review analysis.
"""
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class LlamaService:
    """Service for Llama3 AI model interactions."""

    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        self.model = settings.LLAMA_MODEL
        self.client = httpx.AsyncClient(timeout=60.0)

    async def close(self):
        """Close HTTP client connection."""
        await self.client.aclose()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_completion(
        self,
        prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """
        Generate text completion using Llama3.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)

        Returns:
            Generated text

        Raises:
            Exception: If API call fails
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error calling Llama API: {e.response.status_code} - {e.response.text}")
            raise Exception(f"Failed to generate completion: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating completion: {str(e)}")
            raise

    async def generate_book_summary(self, book_content: str, title: str, author: str) -> str:
        """
        Generate a summary for a book.

        Args:
            book_content: Full or partial book content
            title: Book title
            author: Book author

        Returns:
            Generated summary
        """
        prompt = f"""Provide a concise summary (3-5 sentences) of the following book:

Title: {title}
Author: {author}

Content:
{book_content[:3000]}

Summary:"""

        try:
            summary = await self.generate_completion(prompt, max_tokens=300, temperature=0.5)
            logger.info(f"Generated summary for book: {title}")
            return summary
        except Exception as e:
            logger.error(f"Failed to generate book summary: {str(e)}")
            return "Summary generation failed. Please try again later."

    async def generate_review_summary(self, reviews: list[dict]) -> str:
        """
        Generate an aggregated summary of multiple reviews.

        Args:
            reviews: List of review dictionaries with 'review_text' and 'rating'

        Returns:
            Aggregated review summary
        """
        if not reviews:
            return "No reviews available."

        reviews_text = "\n\n".join([
            f"Rating: {r['rating']}/5\nReview: {r['review_text']}"
            for r in reviews[:10]
        ])

        prompt = f"""Analyze the following book reviews and provide a comprehensive summary highlighting:
1. Common themes and opinions
2. Strengths mentioned by reviewers
3. Criticisms or weaknesses noted
4. Overall sentiment

Reviews:
{reviews_text}

Summary:"""

        try:
            summary = await self.generate_completion(prompt, max_tokens=400, temperature=0.5)
            logger.info(f"Generated review summary for {len(reviews)} reviews")
            return summary
        except Exception as e:
            logger.error(f"Failed to generate review summary: {str(e)}")
            return "Review summary generation failed."

    async def answer_question(self, question: str, context: str) -> str:
        """
        Answer a question based on provided context.

        Args:
            question: User question
            context: Relevant context from documents

        Returns:
            Generated answer
        """
        prompt = f"""Based on the following context, answer the question accurately and concisely.
If the answer cannot be found in the context, say so.

Context:
{context}

Question: {question}

Answer:"""

        try:
            answer = await self.generate_completion(prompt, max_tokens=400, temperature=0.3)
            logger.info(f"Generated answer for question: {question[:50]}...")
            return answer
        except Exception as e:
            logger.error(f"Failed to answer question: {str(e)}")
            return "Unable to generate answer. Please try again."


llama_service = LlamaService()
