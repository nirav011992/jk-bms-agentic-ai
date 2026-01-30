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

    # ------------------------------------------------------------------
    # Sentiment Analysis
    # ------------------------------------------------------------------

    async def analyze_sentiment(self, review_text: str, rating: float) -> float:
        """
        Analyze sentiment of a review and return a score from -1 to 1.

        Args:
            review_text: The review text to analyze
            rating: The numerical rating (1-5)

        Returns:
            float: Sentiment score from -1 (very negative) to 1 (very positive)
        """
        try:
            prompt = f"""
Analyze the sentiment of the following book review on a scale from -1 to 1:
- -1: Very negative sentiment
- 0: Neutral sentiment
- 1: Very positive sentiment

Review Rating: {rating}/5
Review Text: "{review_text}"

Respond with ONLY a number between -1 and 1 (e.g., 0.75, -0.3, 0.0).
Do not include any explanation, just the number.
"""

            response = await self.generate_completion(
                prompt=prompt,
                max_tokens=10,
                temperature=0.3,
            )

            # Parse the sentiment score
            sentiment_score = float(response.strip())

            # Ensure it's within bounds
            sentiment_score = max(-1.0, min(1.0, sentiment_score))

            logger.info(f"Analyzed sentiment: {sentiment_score} for rating {rating}")
            return sentiment_score

        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse sentiment score, using rating-based fallback: {str(e)}")
            # Fallback: convert rating to sentiment score
            return self._rating_to_sentiment(rating)
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return self._rating_to_sentiment(rating)

    def _rating_to_sentiment(self, rating: float) -> float:
        """
        Convert a 1-5 rating to a -1 to 1 sentiment score.

        Args:
            rating: Rating from 1-5

        Returns:
            float: Sentiment score from -1 to 1
        """
        # Map 1-5 scale to -1 to 1 scale
        # 1 -> -1, 2 -> -0.5, 3 -> 0, 4 -> 0.5, 5 -> 1
        return (rating - 3) / 2.0

    async def aggregate_review_sentiments(
        self,
        reviews: List[dict],
        book_title: str
    ) -> dict:
        """
        Aggregate sentiments from multiple reviews and provide analysis.

        Args:
            reviews: List of review dictionaries with rating, review_text, sentiment_score
            book_title: Title of the book being analyzed

        Returns:
            dict: Aggregated sentiment analysis with scores and summary
        """
        if not reviews:
            return {
                "average_sentiment": 0.0,
                "sentiment_distribution": {
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0
                },
                "total_reviews": 0,
                "summary": "No reviews available for this book."
            }

        # Calculate sentiment distribution
        sentiments = [r.get('sentiment_score', 0.0) for r in reviews]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0

        positive = sum(1 for s in sentiments if s > 0.3)
        neutral = sum(1 for s in sentiments if -0.3 <= s <= 0.3)
        negative = sum(1 for s in sentiments if s < -0.3)

        distribution = {
            "positive": positive,
            "neutral": neutral,
            "negative": negative
        }

        # Generate textual summary of sentiments
        try:
            reviews_summary = "\n\n".join(
                f"Rating: {r['rating']}/5 | Sentiment: {r.get('sentiment_score', 0.0):.2f}\nReview: {r['review_text'][:200]}"
                for r in reviews[:10]  # Limit to 10 most recent reviews
            )

            prompt = f"""
Based on the following sentiment analysis of book reviews for "{book_title}", provide a brief 2-3 sentence summary of the overall reader consensus.

Total Reviews: {len(reviews)}
Average Sentiment Score: {avg_sentiment:.2f} (range: -1 to 1)
Distribution: {positive} positive, {neutral} neutral, {negative} negative

Sample Reviews:
{reviews_summary}

Summarize what readers generally think about this book:
"""

            summary = await self.generate_completion(
                prompt=prompt,
                max_tokens=200,
                temperature=0.5,
            )

        except Exception as e:
            logger.error(f"Failed to generate sentiment summary: {str(e)}")
            summary = self._generate_fallback_summary(avg_sentiment, positive, neutral, negative)

        return {
            "average_sentiment": round(avg_sentiment, 2),
            "sentiment_distribution": distribution,
            "total_reviews": len(reviews),
            "summary": summary
        }

    def _generate_fallback_summary(
        self,
        avg_sentiment: float,
        positive: int,
        neutral: int,
        negative: int
    ) -> str:
        """Generate a simple fallback summary when LLM fails."""
        if avg_sentiment > 0.5:
            return f"Readers overwhelmingly enjoyed this book, with {positive} positive reviews highlighting its strengths."
        elif avg_sentiment > 0:
            return f"This book received mostly positive feedback from readers, with {positive} positive and {neutral} neutral reviews."
        elif avg_sentiment > -0.3:
            return f"Readers had mixed opinions about this book, with {positive} positive, {neutral} neutral, and {negative} negative reviews."
        else:
            return f"This book received mostly critical feedback, with {negative} negative reviews pointing out various concerns."


# Singleton instance
huggingface_service = HuggingFaceService()
