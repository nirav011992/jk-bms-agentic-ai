import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/common/Layout';
import { apiService } from '../services/api';
import { Book, Review, BookAvailability, Borrow } from '../types';
import '../styles/BookDetail.css';

const BookDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [book, setBook] = useState<Book | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [availability, setAvailability] = useState<BookAvailability | null>(null);
  const [userHasBorrowed, setUserHasBorrowed] = useState(false);
  const [sentimentAnalysis, setSentimentAnalysis] = useState<any>(null);
  const [similarBooks, setSimilarBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Review form state
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [reviewText, setReviewText] = useState('');
  const [rating, setRating] = useState(5);
  const [submittingReview, setSubmittingReview] = useState(false);
  const [reviewError, setReviewError] = useState('');

  // Borrow state
  const [userActiveBorrow, setUserActiveBorrow] = useState<Borrow | null>(null);
  const [borrowing, setBorrowing] = useState(false);

  useEffect(() => {
    if (id) {
      loadBookData();
    }
  }, [id]);

  const loadBookData = async () => {
    if (!id) return;

    try {
      setLoading(true);
      setError('');

      const bookId = parseInt(id);

      // Load book, reviews, and availability in parallel
      const [bookData, reviewsData, availabilityData] = await Promise.all([
        apiService.getBook(bookId),
        apiService.getBookReviews(bookId),
        apiService.checkBookAvailability(bookId),
      ]);

      setBook(bookData);
      setReviews(reviewsData);
      setAvailability(availabilityData);

      // Load sentiment analysis if there are reviews
      if (reviewsData.length > 0) {
        try {
          const sentimentData = await apiService.getBookSentimentAnalysis(bookId);
          setSentimentAnalysis(sentimentData);
        } catch (err) {
          console.error('Error loading sentiment analysis:', err);
          // Continue without sentiment analysis
        }
      }

      // Check if user has borrowed this book
      if (user) {
        const hasBorrowed = await apiService.checkUserHasBorrowedBook(user.id, bookId);
        setUserHasBorrowed(hasBorrowed);

        // Check if user has active borrow
        const borrows = await apiService.getMyBorrows({ status_filter: 'active' });
        const activeBorrow = borrows.find(b => b.book_id === bookId);
        setUserActiveBorrow(activeBorrow || null);
      }

      // Load similar books recommendations
      try {
        const similar = await apiService.getRecommendations(bookId, 6);
        setSimilarBooks(similar);
      } catch (err) {
        console.error('Error loading similar books:', err);
        // Continue without similar books
      }
    } catch (err: any) {
      console.error('Error loading book data:', err);
      setError(err.response?.data?.detail || 'Failed to load book details');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !reviewText.trim()) return;

    try {
      setSubmittingReview(true);
      setReviewError('');

      await apiService.createReview({
        book_id: parseInt(id),
        review_text: reviewText.trim(),
        rating: rating,
      });

      // Reload reviews
      const reviewsData = await apiService.getBookReviews(parseInt(id));
      setReviews(reviewsData);

      // Reload sentiment analysis
      try {
        const sentimentData = await apiService.getBookSentimentAnalysis(parseInt(id));
        setSentimentAnalysis(sentimentData);
      } catch (err) {
        console.error('Error reloading sentiment analysis:', err);
      }

      // Reset form
      setReviewText('');
      setRating(5);
      setShowReviewForm(false);
    } catch (err: any) {
      console.error('Error submitting review:', err);
      setReviewError(err.response?.data?.detail || 'Failed to submit review');
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleBorrow = async () => {
    if (!id) return;

    try {
      setBorrowing(true);
      setError('');
      await apiService.borrowBook(parseInt(id));
      await loadBookData(); // Reload all data
    } catch (err: any) {
      console.error('Error borrowing book:', err);
      setError(err.response?.data?.detail || 'Failed to borrow book');
    } finally {
      setBorrowing(false);
    }
  };

  const handleReturn = async () => {
    if (!id) return;

    try {
      setBorrowing(true);
      setError('');
      await apiService.returnBook(parseInt(id));
      await loadBookData(); // Reload all data
    } catch (err: any) {
      console.error('Error returning book:', err);
      setError(err.response?.data?.detail || 'Failed to return book');
    } finally {
      setBorrowing(false);
    }
  };

  const renderStars = (ratingValue: number, interactive: boolean = false) => {
    return (
      <div className={`star-rating ${interactive ? 'interactive' : ''}`}>
        {[1, 2, 3, 4, 5].map((star) => (
          <span
            key={star}
            className={`star ${star <= ratingValue ? 'filled' : ''}`}
            onClick={() => interactive && setRating(star)}
          >
            ★
          </span>
        ))}
      </div>
    );
  };

  const averageRating = reviews.length > 0
    ? (reviews.reduce((sum, r) => sum + r.rating, 0) / reviews.length).toFixed(1)
    : 'N/A';

  if (loading) {
    return (
      <Layout>
        <div className="book-detail-container">
          <p>Loading book details...</p>
        </div>
      </Layout>
    );
  }

  if (error && !book) {
    return (
      <Layout>
        <div className="book-detail-container">
          <div className="error-message">{error}</div>
          <button className="btn-secondary" onClick={() => navigate('/books')}>
            Back to Books
          </button>
        </div>
      </Layout>
    );
  }

  if (!book) {
    return (
      <Layout>
        <div className="book-detail-container">
          <p>Book not found</p>
          <button className="btn-secondary" onClick={() => navigate('/books')}>
            Back to Books
          </button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="book-detail-container">
        <button className="btn-back" onClick={() => navigate('/books')}>
          ← Back to Books
        </button>

        {error && <div className="error-message">{error}</div>}

        <div className="book-detail-header">
          <div className="book-detail-info">
            <h1>{book.title}</h1>
            <p className="book-author">by {book.author}</p>
            <div className="book-meta-info">
              <span className="badge">{book.genre}</span>
              <span>{book.year_published}</span>
              {book.isbn && <span className="isbn">ISBN: {book.isbn}</span>}
            </div>

            {/* Availability and Borrow Actions */}
            {availability && (
              <div className="availability-section">
                {userActiveBorrow ? (
                  <>
                    <span className="status-badge borrowed">You borrowed this book</span>
                    <p className="due-date">
                      Due: {new Date(userActiveBorrow.due_date).toLocaleDateString()}
                    </p>
                    <button
                      className="btn-return"
                      onClick={handleReturn}
                      disabled={borrowing}
                    >
                      {borrowing ? 'Returning...' : 'Return Book'}
                    </button>
                  </>
                ) : availability.is_available ? (
                  <>
                    <span className="status-badge available">Available</span>
                    <button
                      className="btn-borrow"
                      onClick={handleBorrow}
                      disabled={borrowing}
                    >
                      {borrowing ? 'Borrowing...' : 'Borrow Book'}
                    </button>
                  </>
                ) : (
                  <span className="status-badge unavailable">Currently Borrowed</span>
                )}
              </div>
            )}

            {/* Reviews Summary */}
            <div className="reviews-summary">
              <div className="rating-display">
                {renderStars(parseFloat(averageRating))}
                <span className="rating-text">
                  {averageRating} ({reviews.length} {reviews.length === 1 ? 'review' : 'reviews'})
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Book Description */}
        {book.description && (
          <div className="book-section">
            <h2>Description</h2>
            <p>{book.description}</p>
          </div>
        )}

        {/* AI Summary */}
        {book.summary && (
          <div className="book-section summary-section">
            <h2>AI-Generated Summary</h2>
            <p>{book.summary}</p>
          </div>
        )}

        {/* Sentiment Analysis Section */}
        {sentimentAnalysis && sentimentAnalysis.total_reviews > 0 && (
          <div className="book-section sentiment-section">
            <h2>Reader Sentiment Analysis</h2>

            <div className="sentiment-overview">
              <div className="sentiment-score-display">
                <div className="sentiment-score-circle" data-sentiment={
                  sentimentAnalysis.average_sentiment > 0.3 ? 'positive' :
                  sentimentAnalysis.average_sentiment < -0.3 ? 'negative' : 'neutral'
                }>
                  <span className="sentiment-score-value">
                    {(sentimentAnalysis.average_sentiment * 100).toFixed(0)}
                  </span>
                  <span className="sentiment-score-label">Score</span>
                </div>
                <div className="sentiment-description">
                  <h3>
                    {sentimentAnalysis.average_sentiment > 0.5 ? 'Very Positive' :
                     sentimentAnalysis.average_sentiment > 0.3 ? 'Positive' :
                     sentimentAnalysis.average_sentiment > -0.3 ? 'Mixed' :
                     sentimentAnalysis.average_sentiment > -0.5 ? 'Negative' : 'Very Negative'}
                  </h3>
                  <p>Based on {sentimentAnalysis.total_reviews} reader reviews</p>
                </div>
              </div>

              <div className="sentiment-distribution">
                <h4>Sentiment Distribution</h4>
                <div className="sentiment-bars">
                  <div className="sentiment-bar-item">
                    <span className="sentiment-bar-label">Positive</span>
                    <div className="sentiment-bar-container">
                      <div
                        className="sentiment-bar positive"
                        style={{
                          width: `${(sentimentAnalysis.sentiment_distribution.positive / sentimentAnalysis.total_reviews * 100)}%`
                        }}
                      />
                    </div>
                    <span className="sentiment-bar-count">{sentimentAnalysis.sentiment_distribution.positive}</span>
                  </div>
                  <div className="sentiment-bar-item">
                    <span className="sentiment-bar-label">Neutral</span>
                    <div className="sentiment-bar-container">
                      <div
                        className="sentiment-bar neutral"
                        style={{
                          width: `${(sentimentAnalysis.sentiment_distribution.neutral / sentimentAnalysis.total_reviews * 100)}%`
                        }}
                      />
                    </div>
                    <span className="sentiment-bar-count">{sentimentAnalysis.sentiment_distribution.neutral}</span>
                  </div>
                  <div className="sentiment-bar-item">
                    <span className="sentiment-bar-label">Negative</span>
                    <div className="sentiment-bar-container">
                      <div
                        className="sentiment-bar negative"
                        style={{
                          width: `${(sentimentAnalysis.sentiment_distribution.negative / sentimentAnalysis.total_reviews * 100)}%`
                        }}
                      />
                    </div>
                    <span className="sentiment-bar-count">{sentimentAnalysis.sentiment_distribution.negative}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="sentiment-summary">
              <h4>AI-Generated Consensus</h4>
              <p>{sentimentAnalysis.summary}</p>
            </div>
          </div>
        )}

        {/* Similar Books Section */}
        {similarBooks.length > 0 && (
          <div className="book-section similar-books-section">
            <div className="section-header">
              <h2>📖 Similar Books You Might Like</h2>
            </div>

            <div className="similar-books-grid">
              {similarBooks.map((similarBook) => (
                <div
                  key={similarBook.id}
                  className="similar-book-card"
                  onClick={() => navigate(`/books/${similarBook.id}`)}
                >
                  <div className="similar-book-header">
                    <h3>{similarBook.title}</h3>
                  </div>
                  <p className="book-author">by {similarBook.author}</p>
                  <div className="similar-book-meta">
                    <span className="meta-badge">{similarBook.genre}</span>
                    <span className="meta-year">{similarBook.year_published}</span>
                  </div>
                  {similarBook.summary && (
                    <p className="similar-book-summary">
                      {similarBook.summary.substring(0, 100)}...
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Reviews Section */}
        <div className="book-section reviews-section">
          <div className="reviews-header">
            <h2>Reviews</h2>
            {userHasBorrowed && !showReviewForm && (
              <button className="btn-primary" onClick={() => setShowReviewForm(true)}>
                Write a Review
              </button>
            )}
          </div>

          {!userHasBorrowed && (
            <p className="info-message">
              You must borrow this book before you can write a review.
            </p>
          )}

          {/* Review Form */}
          {showReviewForm && (
            <div className="review-form-container">
              <h3>Write Your Review</h3>
              <form onSubmit={handleSubmitReview}>
                {reviewError && <div className="error-message">{reviewError}</div>}

                <div className="form-group">
                  <label>Your Rating</label>
                  {renderStars(rating, true)}
                </div>

                <div className="form-group">
                  <label htmlFor="review-text">Your Review</label>
                  <textarea
                    id="review-text"
                    value={reviewText}
                    onChange={(e) => setReviewText(e.target.value)}
                    placeholder="Share your thoughts about this book..."
                    rows={6}
                    required
                  />
                </div>

                <div className="form-actions">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => {
                      setShowReviewForm(false);
                      setReviewError('');
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={submittingReview || !reviewText.trim()}
                  >
                    {submittingReview ? 'Submitting...' : 'Submit Review'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Reviews List */}
          <div className="reviews-list">
            {reviews.length === 0 ? (
              <p className="empty-state">No reviews yet. Be the first to review this book!</p>
            ) : (
              reviews.map((review) => (
                <div key={review.id} className="review-card">
                  <div className="review-header">
                    <div>
                      {renderStars(review.rating)}
                      <p className="review-date">
                        {new Date(review.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <p className="review-text">{review.review_text}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default BookDetail;
