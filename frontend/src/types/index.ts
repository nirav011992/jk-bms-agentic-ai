export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Book {
  id: number;
  title: string;
  author: string;
  genre: string;
  year_published: number;
  isbn?: string;
  description?: string;
  summary?: string;
  created_at: string;
  updated_at: string;
}

export interface Review {
  id: number;
  book_id: number;
  user_id: number;
  review_text: string;
  rating: number;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: number;
  owner_id: number;
  filename: string;
  ingestion_status: string;
  metadata?: any;
  created_at: string;
  updated_at: string;
}

export interface DocumentExcerpt {
  document_id: number;
  filename: string;
  excerpt: string;
  relevance_score: number;
}

export interface QAResponse {
  question: string;
  answer: string;
  relevant_documents: DocumentExcerpt[];
  confidence?: number;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

export interface Borrow {
  id: number;
  user_id: number;
  book_id: number;
  borrow_date: string;
  due_date: string;
  return_date?: string;
  status: 'active' | 'returned' | 'overdue';
  is_overdue: boolean;
  created_at: string;
  updated_at: string;
  book_title?: string;
  book_author?: string;
  user_email?: string;
  user_username?: string;
}

export interface BorrowHistory {
  total_borrows: number;
  active_borrows: number;
  returned_borrows: number;
  overdue_borrows: number;
  borrows: Borrow[];
}

export interface BookAvailability {
  book_id: number;
  is_available: boolean;
  active_borrows: number;
  total_borrows: number;
}
