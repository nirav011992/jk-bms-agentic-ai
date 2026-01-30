import axios, { AxiosInstance, AxiosError } from 'axios';
import { AuthTokens, LoginCredentials, RegisterData, User, Book, Review, Document, QAResponse, Borrow, BorrowHistory, BookAvailability } from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    this.api.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async register(data: RegisterData): Promise<User> {
    const response = await this.api.post('/api/v1/auth/register', data);
    return response.data;
  }

  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    const response = await this.api.post('/api/v1/auth/login', credentials);
    return response.data;
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get('/api/v1/users/me');
    return response.data;
  }

  // Book endpoints
  async getBooks(params?: { skip?: number; limit?: number; genre?: string; author?: string }): Promise<Book[]> {
    const response = await this.api.get('/api/v1/books/', { params });
    return response.data;
  }

  async getBook(id: number): Promise<Book> {
    const response = await this.api.get(`/api/v1/books/${id}`);
    return response.data;
  }

  async createBook(data: Partial<Book>): Promise<Book> {
    const response = await this.api.post('/api/v1/books/', data);
    return response.data;
  }

  async updateBook(id: number, data: Partial<Book>): Promise<Book> {
    const response = await this.api.put(`/api/v1/books/${id}`, data);
    return response.data;
  }

  async deleteBook(id: number): Promise<void> {
    await this.api.delete(`/api/v1/books/${id}`);
  }

  async getBookSentimentAnalysis(bookId: number): Promise<any> {
    const response = await this.api.get(`/api/v1/books/${bookId}/analysis`);
    return response.data;
  }

  // not used currently
  async generateSummary(title: string, author: string, content: string): Promise<{ summary: string }> {
    const response = await this.api.post('/api/v1/books/generate-summary', null, {
      params: { title, author, content }
    });
    return response.data;
  }

  async uploadPdf(file: File, title: string, author: string): Promise<{ content: string; summary: string; extracted_chars: number }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.api.post('/api/v1/books/upload-pdf', formData, {
      params: { title, author },
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Review endpoints
  async getBookReviews(bookId: number): Promise<Review[]> {
    const response = await this.api.get(`/api/v1/reviews/book/${bookId}`);
    return response.data;
  }

  async createReview(data: { book_id: number; review_text: string; rating: number }): Promise<Review> {
    const response = await this.api.post('/api/v1/reviews/', data);
    return response.data;
  }

  // Document endpoints
  async getDocuments(): Promise<Document[]> {
    const response = await this.api.get('/api/v1/documents/');
    return response.data;
  }

  async uploadDocument(file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.api.post('/api/v1/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async ingestDocuments(): Promise<{ message: string; count: number }> {
    const response = await this.api.post('/api/v1/documents/ingest');
    return response.data;
  }

  async ingestDocument(id: number): Promise<Document> {
    const response = await this.api.post(`/api/v1/documents/${id}/ingest`);
    return response.data;
  }

  async deleteDocument(id: number): Promise<void> {
    await this.api.delete(`/api/v1/documents/${id}`);
  }

  // Q&A endpoints
  async askQuestion(question: string, contextLimit?: number): Promise<QAResponse> {
    const response = await this.api.post('/api/v1/qa/ask', {
      question,
      context_limit: contextLimit || 5,
    });
    return response.data;
  }

  // Recommendation endpoints
  async getRecommendations(bookId?: number, limit?: number): Promise<Book[]> {
    const response = await this.api.get('/api/v1/recommendations/', {
      params: { book_id: bookId, limit: limit || 5 },
    });
    return response.data;
  }

  async trainRecommendationModel(): Promise<{ message: string }> {
    const response = await this.api.post('/api/v1/recommendations/train');
    return response.data;
  }

  // User management endpoints (admin only)
  async getUsers(): Promise<User[]> {
    const response = await this.api.get('/api/v1/users/');
    return response.data;
  }

  async updateUser(id: number, data: Partial<User>): Promise<User> {
    const response = await this.api.put(`/api/v1/users/${id}`, data);
    return response.data;
  }

  // Borrow endpoints
  async borrowBook(bookId: number, loanPeriodDays: number = 14): Promise<Borrow> {
    const response = await this.api.post(`/api/v1/borrows/${bookId}/borrow`, {
      book_id: bookId,
      loan_period_days: loanPeriodDays,
    });
    return response.data;
  }

  async returnBook(bookId: number): Promise<Borrow> {
    const response = await this.api.post(`/api/v1/borrows/${bookId}/return`);
    return response.data;
  }

  async getMyBorrows(params?: { skip?: number; limit?: number; status_filter?: string }): Promise<Borrow[]> {
    const response = await this.api.get('/api/v1/borrows/', { params });
    return response.data;
  }

  async getBorrowHistory(): Promise<BorrowHistory> {
    const response = await this.api.get('/api/v1/borrows/history');
    return response.data;
  }

  async getAllBorrows(params?: { skip?: number; limit?: number; status_filter?: string }): Promise<Borrow[]> {
    const response = await this.api.get('/api/v1/borrows/all', { params });
    return response.data;
  }

  async getOverdueBorrows(params?: { skip?: number; limit?: number }): Promise<Borrow[]> {
    const response = await this.api.get('/api/v1/borrows/overdue', { params });
    return response.data;
  }

  async checkBookAvailability(bookId: number): Promise<BookAvailability> {
    const response = await this.api.get(`/api/v1/borrows/book/${bookId}/availability`);
    return response.data;
  }

  async checkUserHasBorrowedBook(userId: number, bookId: number): Promise<boolean> {
    const response = await this.api.get(`/api/v1/borrows/user/${userId}/has-borrowed/${bookId}`);
    return response.data;
  }
}

export const apiService = new ApiService();
