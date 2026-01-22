"""
Book recommendation ML model.
Uses collaborative filtering and content-based approaches.
"""
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from typing import List, Optional
import pickle
import os

from app.core.logging import get_logger

logger = get_logger(__name__)


class BookRecommendationModel:
    """ML model for book recommendations."""

    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
        self.content_matrix: Optional[np.ndarray] = None
        self.books_df: Optional[pd.DataFrame] = None
        self.user_item_matrix: Optional[pd.DataFrame] = None
        logger.info("Initialized BookRecommendationModel")

    def train_content_based(self, books: List[dict]) -> None:
        """
        Train content-based recommendation model.

        Args:
            books: List of book dictionaries with 'id', 'title', 'author', 'genre', 'summary'
        """
        try:
            if not books:
                logger.warning("No books provided for training")
                return

            self.books_df = pd.DataFrame(books)

            self.books_df['combined_features'] = (
                self.books_df['title'].fillna('') + ' ' +
                self.books_df['author'].fillna('') + ' ' +
                self.books_df['genre'].fillna('') + ' ' +
                self.books_df['summary'].fillna('')
            )

            self.content_matrix = self.tfidf_vectorizer.fit_transform(
                self.books_df['combined_features']
            ).toarray()

            logger.info(f"Trained content-based model with {len(books)} books")

        except Exception as e:
            logger.error(f"Error training content-based model: {str(e)}")
            raise

    def train_collaborative(self, reviews: List[dict]) -> None:
        """
        Train collaborative filtering model.

        Args:
            reviews: List of review dictionaries with 'user_id', 'book_id', 'rating'
        """
        try:
            if not reviews:
                logger.warning("No reviews provided for collaborative filtering")
                return

            reviews_df = pd.DataFrame(reviews)

            self.user_item_matrix = reviews_df.pivot_table(
                index='user_id',
                columns='book_id',
                values='rating',
                fill_value=0
            )

            logger.info(f"Trained collaborative filtering with {len(reviews)} reviews")

        except Exception as e:
            logger.error(f"Error training collaborative model: {str(e)}")
            raise

    def get_content_based_recommendations(
        self,
        book_id: int,
        n_recommendations: int = 5
    ) -> List[dict]:
        """
        Get content-based recommendations for a book.

        Args:
            book_id: ID of the book
            n_recommendations: Number of recommendations to return

        Returns:
            List of recommended books with scores
        """
        try:
            if self.books_df is None or self.content_matrix is None:
                logger.warning("Model not trained")
                return []

            book_idx = self.books_df[self.books_df['id'] == book_id].index
            if len(book_idx) == 0:
                logger.warning(f"Book ID {book_id} not found")
                return []

            book_idx = book_idx[0]

            similarity_scores = cosine_similarity(
                self.content_matrix[book_idx:book_idx+1],
                self.content_matrix
            )[0]

            similar_indices = similarity_scores.argsort()[-n_recommendations-1:-1][::-1]

            recommendations = []
            for idx in similar_indices:
                if idx != book_idx:
                    book = self.books_df.iloc[idx]
                    recommendations.append({
                        'id': int(book['id']),
                        'title': book['title'],
                        'author': book['author'],
                        'genre': book['genre'],
                        'score': float(similarity_scores[idx])
                    })

            logger.info(f"Generated {len(recommendations)} content-based recommendations for book {book_id}")
            return recommendations

        except Exception as e:
            logger.error(f"Error getting content-based recommendations: {str(e)}")
            return []

    def get_collaborative_recommendations(
        self,
        user_id: int,
        n_recommendations: int = 5
    ) -> List[dict]:
        """
        Get collaborative filtering recommendations for a user.

        Args:
            user_id: ID of the user
            n_recommendations: Number of recommendations to return

        Returns:
            List of recommended book IDs with scores
        """
        try:
            if self.user_item_matrix is None:
                logger.warning("Collaborative model not trained")
                return []

            if user_id not in self.user_item_matrix.index:
                logger.warning(f"User ID {user_id} not found in user-item matrix")
                return []

            user_ratings = self.user_item_matrix.loc[user_id]

            user_similarity = cosine_similarity(
                self.user_item_matrix
            )
            user_idx = self.user_item_matrix.index.get_loc(user_id)
            similar_users = user_similarity[user_idx].argsort()[-11:-1][::-1]

            recommendations = {}
            for similar_user_idx in similar_users:
                similar_user_id = self.user_item_matrix.index[similar_user_idx]
                similar_user_ratings = self.user_item_matrix.loc[similar_user_id]

                for book_id, rating in similar_user_ratings.items():
                    if rating > 0 and user_ratings[book_id] == 0:
                        if book_id not in recommendations:
                            recommendations[book_id] = []
                        recommendations[book_id].append(rating)

            book_scores = {
                book_id: np.mean(ratings)
                for book_id, ratings in recommendations.items()
            }

            sorted_recommendations = sorted(
                book_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:n_recommendations]

            result = [
                {'book_id': int(book_id), 'score': float(score)}
                for book_id, score in sorted_recommendations
            ]

            logger.info(f"Generated {len(result)} collaborative recommendations for user {user_id}")
            return result

        except Exception as e:
            logger.error(f"Error getting collaborative recommendations: {str(e)}")
            return []

    def get_hybrid_recommendations(
        self,
        user_id: int,
        book_id: Optional[int] = None,
        n_recommendations: int = 5
    ) -> List[dict]:
        """
        Get hybrid recommendations combining content-based and collaborative filtering.

        Args:
            user_id: ID of the user
            book_id: Optional book ID for content-based similarity
            n_recommendations: Number of recommendations to return

        Returns:
            List of recommended books
        """
        content_recs = []
        if book_id:
            content_recs = self.get_content_based_recommendations(book_id, n_recommendations)

        collab_recs = self.get_collaborative_recommendations(user_id, n_recommendations)

        all_recs = {}
        for rec in content_recs:
            all_recs[rec['id']] = rec
            all_recs[rec['id']]['combined_score'] = rec['score'] * 0.5

        for rec in collab_recs:
            bid = rec['book_id']
            if bid in all_recs:
                all_recs[bid]['combined_score'] += rec['score'] * 0.5
            else:
                all_recs[bid] = {
                    'id': bid,
                    'combined_score': rec['score'] * 0.5
                }

        sorted_recs = sorted(
            all_recs.values(),
            key=lambda x: x.get('combined_score', 0),
            reverse=True
        )[:n_recommendations]

        return sorted_recs

    def save_model(self, filepath: str) -> None:
        """Save model to disk."""
        try:
            model_data = {
                'tfidf_vectorizer': self.tfidf_vectorizer,
                'content_matrix': self.content_matrix,
                'books_df': self.books_df,
                'user_item_matrix': self.user_item_matrix
            }
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            logger.info(f"Model saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise

    def load_model(self, filepath: str) -> None:
        """Load model from disk."""
        try:
            if not os.path.exists(filepath):
                logger.warning(f"Model file not found: {filepath}")
                return

            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)

            self.tfidf_vectorizer = model_data['tfidf_vectorizer']
            self.content_matrix = model_data['content_matrix']
            self.books_df = model_data['books_df']
            self.user_item_matrix = model_data['user_item_matrix']

            logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise


recommendation_model = BookRecommendationModel()
