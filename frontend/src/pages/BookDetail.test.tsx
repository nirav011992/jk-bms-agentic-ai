/**
 * Unit tests for BookDetail page (Phase 1)
 */
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter, Route, Routes } from 'react-router-dom';
import BookDetail from './BookDetail';
import { AuthProvider } from '../context/AuthContext';
import { apiService } from '../services/api';
import { Book, Review, BookAvailability, User } from '../types';

jest.mock('../services/api');

const mockUser: User = {
  id: 1,
  email: 'test@example.com',
  username: 'testuser',
  role: 'user',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockBook: Book = {
  id: 1,
  title: 'Test Book',
  author: 'Test Author',
  genre: 'Fiction',
  year_published: 2024,
  isbn: '1234567890',
  description: 'A test book description',
  summary: 'AI-generated summary of the test book',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockReviews: Review[] = [
  {
    id: 1,
    user_id: 1,
    book_id: 1,
    rating: 5,
    review_text: 'Great book!',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    user_id: 2,
    book_id: 1,
    rating: 4,
    review_text: 'Good read',
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
];

const mockAvailability: BookAvailability = {
  book_id: 1,
  is_available: true,
  total_borrows: 5,
  active_borrows: 3,
};

const mockSentimentAnalysis = {
  average_sentiment: 0.8,
  sentiment_distribution: {
    positive: 2,
    neutral: 0,
    negative: 0,
  },
  total_reviews: 2,
  summary: 'Overwhelmingly positive reviews for this book.',
};

const mockSimilarBooks: Book[] = [
  {
    id: 2,
    title: 'Similar Book',
    author: 'Another Author',
    genre: 'Fiction',
    year_published: 2023,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const renderBookDetail = () => {
  (apiService.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);
  jest.spyOn(Storage.prototype, 'getItem').mockReturnValue('mock-token');

  (apiService.getBook as jest.Mock).mockResolvedValue(mockBook);
  (apiService.getBookReviews as jest.Mock).mockResolvedValue(mockReviews);
  (apiService.checkBookAvailability as jest.Mock).mockResolvedValue(mockAvailability);
  (apiService.getBookSentimentAnalysis as jest.Mock).mockResolvedValue(mockSentimentAnalysis);
  (apiService.checkUserHasBorrowedBook as jest.Mock).mockResolvedValue(true);
  (apiService.getMyBorrows as jest.Mock).mockResolvedValue([]);
  (apiService.getRecommendations as jest.Mock).mockResolvedValue(mockSimilarBooks);

  return render(
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/books/:id" element={<BookDetail />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('BookDetail Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.history.pushState({}, '', '/books/1');
  });

  test('renders book details correctly', async () => {
    renderBookDetail();

    await waitFor(() => {
      expect(screen.getByText('Test Book')).toBeInTheDocument();
    });
    expect(screen.getByText(/Test Author/i)).toBeInTheDocument();
    expect(screen.getAllByText('Fiction')[0]).toBeInTheDocument();
  });

  test('displays book summary', async () => {
    renderBookDetail();

    await waitFor(() => {
      expect(screen.getAllByText(/AI-generated summary/i)[0]).toBeInTheDocument();
    });
    expect(screen.getByText(mockBook.summary!)).toBeInTheDocument();
  });

  test('displays reviews list', async () => {
    renderBookDetail();

    await waitFor(() => {
      expect(screen.getByText('Great book!')).toBeInTheDocument();
    });
    expect(screen.getByText('Good read')).toBeInTheDocument();
  });

  test('displays borrow button when book is available', async () => {
    renderBookDetail();

    await waitFor(() => {
      expect(screen.getByText(/Available/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Borrow Book/i)).toBeInTheDocument();
  });

  test('handles borrow action', async () => {
    (apiService.borrowBook as jest.Mock).mockResolvedValue({});
    renderBookDetail();

    await waitFor(() => {
      expect(screen.getByText(/Borrow Book/i)).toBeInTheDocument();
    });

    const borrowButton = screen.getByText(/Borrow Book/i);
    fireEvent.click(borrowButton);

    await waitFor(() => {
      expect(apiService.borrowBook).toHaveBeenCalledWith(1);
    });
  });

  test('displays sentiment analysis when reviews exist', async () => {
    renderBookDetail();

    await waitFor(() => {
      expect(screen.getByText(/Reader Sentiment Analysis/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Overwhelmingly positive/i)).toBeInTheDocument();
  });

  test('displays similar books section', async () => {
    renderBookDetail();

    await waitFor(() => {
      expect(screen.getByText(/Similar Books You Might Like/i)).toBeInTheDocument();
    });
    expect(screen.getByText('Similar Book')).toBeInTheDocument();
  });

  test('shows review form when user has borrowed the book', async () => {
    renderBookDetail();

    await waitFor(() => {
      expect(screen.getByText(/Write a Review/i)).toBeInTheDocument();
    });
  });




  test('displays average rating correctly', async () => {
    renderBookDetail();

    await waitFor(() => {
      // Average of 5 and 4 is 4.5
      expect(screen.getByText(/4\.5/)).toBeInTheDocument();
    });
  });


  test('handles loading state', async () => {
    renderBookDetail();

    expect(screen.getByText(/Loading book details/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText(/Loading book details/i)).not.toBeInTheDocument();
    });
  });


  test('star rating is interactive in review form', async () => {
    renderBookDetail();

    await waitFor(() => {
        expect(screen.getByText(/Write a Review/i)).toBeInTheDocument();
    });
    const writeReviewButton = screen.getByText(/Write a Review/i);
    fireEvent.click(writeReviewButton);


    // Stars should be clickable
    const stars = screen.getAllByText('★');
    expect(stars.length).toBeGreaterThan(0);
  });

  test('navigates to similar book on click', async () => {
    renderBookDetail();

    await waitFor(() => {
        expect(screen.getByText('Similar Book')).toBeInTheDocument();
    });
    const similarBookCard = screen.getByText('Similar Book');
    fireEvent.click(similarBookCard);
  });
});
