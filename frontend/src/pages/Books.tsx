import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/common/Layout';
import { apiService } from '../services/api';
import { Book, BookAvailability, Borrow } from '../types';
import '../styles/Books.css';

interface BookFormData {
  title: string;
  author: string;
  genre: string;
  year_published: number;
  isbn?: string;
  description?: string;
  content?: string;
  summary?: string;
}

const Books: React.FC = () => {
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingBook, setEditingBook] = useState<Book | null>(null);
  const [formData, setFormData] = useState<BookFormData>({
    title: '',
    author: '',
    genre: '',
    year_published: new Date().getFullYear(),
    isbn: '',
    description: '',
    content: '',
    summary: ''
  });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [uploadingPdf, setUploadingPdf] = useState(false);
  const [pdfDragActive, setPdfDragActive] = useState(false);
  const [bookAvailability, setBookAvailability] = useState<Map<number, BookAvailability>>(new Map());
  const [userBorrows, setUserBorrows] = useState<Borrow[]>([]);
  const [borrowingBookId, setBorrowingBookId] = useState<number | null>(null);

  const { isAdmin, user } = useAuth();

  useEffect(() => {
    loadBooks();
    loadUserBorrows();
  }, []);

  useEffect(() => {
    if (books.length > 0) {
      loadBooksAvailability();
    }
  }, [books]);

  const loadBooks = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await apiService.getBooks({});
      setBooks(data);
    } catch (err: any) {
      console.error('Error loading books:', err);
      setError('Failed to load books');
    } finally {
      setLoading(false);
    }
  };

  const loadUserBorrows = async () => {
    try {
      const borrows = await apiService.getMyBorrows({ status_filter: 'active' });
      setUserBorrows(borrows);
    } catch (err: any) {
      console.error('Error loading user borrows:', err);
    }
  };

  const loadBooksAvailability = async () => {
    try {
      const availabilityMap = new Map<number, BookAvailability>();
      await Promise.all(
        books.map(async (book) => {
          try {
            const availability = await apiService.checkBookAvailability(book.id);
            availabilityMap.set(book.id, availability);
          } catch (err) {
            console.error(`Error checking availability for book ${book.id}:`, err);
          }
        })
      );
      setBookAvailability(availabilityMap);
    } catch (err: any) {
      console.error('Error loading books availability:', err);
    }
  };

  const getUserActiveBorrow = (bookId: number): Borrow | undefined => {
    return userBorrows.find(b => b.book_id === bookId && b.status === 'active');
  };

  const handleBorrowBook = async (bookId: number) => {
    try {
      setBorrowingBookId(bookId);
      setError('');
      await apiService.borrowBook(bookId);
      await loadUserBorrows();
      await loadBooksAvailability();
      setError(''); // Clear any previous errors
    } catch (err: any) {
      console.error('Error borrowing book:', err);
      setError(err.response?.data?.detail || 'Failed to borrow book');
    } finally {
      setBorrowingBookId(null);
    }
  };

  const handleReturnBook = async (bookId: number) => {
    try {
      setBorrowingBookId(bookId);
      setError('');
      await apiService.returnBook(bookId);
      await loadUserBorrows();
      await loadBooksAvailability();
      setError(''); // Clear any previous errors
    } catch (err: any) {
      console.error('Error returning book:', err);
      setError(err.response?.data?.detail || 'Failed to return book');
    } finally {
      setBorrowingBookId(null);
    }
  };

  const genres = [...new Set(books.map(book => book.genre))].filter(Boolean);

  const filteredBooks = books.filter(book => {
    const matchesSearch = book.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         book.author.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesGenre = !selectedGenre || book.genre === selectedGenre;
    return matchesSearch && matchesGenre;
  });

  const resetForm = () => {
    setFormData({
      title: '',
      author: '',
      genre: '',
      year_published: new Date().getFullYear(),
      isbn: '',
      description: '',
      content: '',
      summary: ''
    });
    setFormError('');
    setEditingBook(null);
  };

  const handleAddClick = () => {
    resetForm();
    setShowAddModal(true);
  };

  const handleEditClick = (book: Book) => {
    setFormData({
      title: book.title,
      author: book.author,
      genre: book.genre,
      year_published: book.year_published,
      isbn: book.isbn || '',
      description: book.description || '',
      content: '',
      summary: book.summary || ''
    });
    setEditingBook(book);
    setShowAddModal(true);
  };

  const handleCloseModal = () => {
    setShowAddModal(false);
    resetForm();
  };

  const validateForm = (): boolean => {
    if (!formData.title.trim()) {
      setFormError('Title is required');
      return false;
    }
    if (!formData.author.trim()) {
      setFormError('Author is required');
      return false;
    }
    if (!formData.genre.trim()) {
      setFormError('Genre is required');
      return false;
    }
    if (formData.year_published < 1000 || formData.year_published > new Date().getFullYear() + 1) {
      setFormError('Please enter a valid publication year');
      return false;
    }
    return true;
  };

  const handlePdfDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setPdfDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };

  const handlePdfDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setPdfDragActive(false);

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handlePdfFileSelect(files[0]);
    }
  };

  const handlePdfFileSelect = async (file: File) => {
    if (file.type !== 'application/pdf') {
      setFormError('Please select a valid PDF file');
      return;
    }

    if (file.size > 50 * 1024 * 1024) { // 50MB limit
      setFormError('PDF file size must be less than 50MB');
      return;
    }

    if (!formData.title.trim() || !formData.author.trim()) {
      setFormError('Please fill in Title and Author before uploading a PDF');
      return;
    }

    try {
      setUploadingPdf(true);
      setFormError('');
      const result = await apiService.uploadPdf(file, formData.title.trim(), formData.author.trim());
      setFormData({
        ...formData,
        content: result.content,
        summary: result.summary
      });
      setFormError(`✓ PDF processed successfully! Extracted ${result.extracted_chars} characters.`);
    } catch (err: any) {
      console.error('Error uploading PDF:', err);
      setFormError(err.response?.data?.detail || 'Failed to upload and process PDF');
    } finally {
      setUploadingPdf(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError('');

    if (!validateForm()) {
      return;
    }

    try {
      setSubmitting(true);

      const bookData = {
        title: formData.title.trim(),
        author: formData.author.trim(),
        genre: formData.genre.trim(),
        year_published: formData.year_published,
        isbn: formData.isbn?.trim() || undefined,
        description: formData.description?.trim() || undefined,
        content: formData.content?.trim() || undefined,
        summary: formData.summary?.trim() || undefined
      };

      if (editingBook) {
        await apiService.updateBook(editingBook.id, bookData);
      } else {
        await apiService.createBook(bookData);
      }

      await loadBooks();
      handleCloseModal();
    } catch (err: any) {
      console.error('Error saving book:', err);
      setFormError(err.response?.data?.detail || 'Failed to save book');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (bookId: number) => {
    if (!window.confirm('Are you sure you want to delete this book?')) {
      return;
    }

    try {
      await apiService.deleteBook(bookId);
      await loadBooks();
    } catch (err: any) {
      console.error('Error deleting book:', err);
      setError('Failed to delete book');
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="loading">Loading books...</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="books-page">
        <div className="page-header">
          <h1>Books Library</h1>
          {isAdmin && (
            <button className="btn-primary" onClick={handleAddClick}>
              Add Book
            </button>
          )}
        </div>

        {error && <div className="error-banner">{error}</div>}

        <div className="filters-section">
          <input
            type="text"
            placeholder="Search by title or author..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />

          <select
            value={selectedGenre}
            onChange={(e) => setSelectedGenre(e.target.value)}
            className="genre-select"
          >
            <option value="">All Genres</option>
            {genres.map(genre => (
              <option key={genre} value={genre}>{genre}</option>
            ))}
          </select>
        </div>

        {filteredBooks.length === 0 ? (
          <div className="empty-state">
            <p>No books found</p>
            {isAdmin && !searchTerm && !selectedGenre && (
              <button className="btn-primary" onClick={handleAddClick}>
                Add Your First Book
              </button>
            )}
          </div>
        ) : (
          <div className="books-grid">
            {filteredBooks.map((book) => (
              <div key={book.id} className="book-item">
                <div className="book-info">
                  <h3>
                    <Link to={`/books/${book.id}`} className="book-title-link">
                      {book.title}
                    </Link>
                  </h3>
                  <p className="book-author">by {book.author}</p>
                  <p className="book-meta">{book.genre} • {book.year_published}</p>
                  {book.isbn && <p className="book-isbn">ISBN: {book.isbn}</p>}
                  {book.description && (
                    <p className="book-description">{book.description}</p>
                  )}
                  {book.summary && (
                    <div className="book-summary">
                      <strong>AI Summary:</strong>
                      <p>{book.summary}</p>
                    </div>
                  )}
                </div>

                {/* Borrow/Return Actions for regular users */}
                {!isAdmin && (
                  <div className="book-borrow-actions">
                    {(() => {
                      const activeBorrow = getUserActiveBorrow(book.id);
                      const availability = bookAvailability.get(book.id);
                      const isProcessing = borrowingBookId === book.id;

                      if (activeBorrow) {
                        // User has borrowed this book - show return button
                        return (
                          <div className="borrow-status-section">
                            <p className="borrowed-badge">You borrowed this book</p>
                            <p className="due-date">Due: {new Date(activeBorrow.due_date).toLocaleDateString()}</p>
                            <button
                              className="btn-return"
                              onClick={() => handleReturnBook(book.id)}
                              disabled={isProcessing}
                            >
                              {isProcessing ? 'Returning...' : 'Return Book'}
                            </button>
                          </div>
                        );
                      } else if (availability?.is_available) {
                        // Book is available - show borrow button
                        return (
                          <div className="borrow-status-section">
                            <p className="available-badge">Available</p>
                            <button
                              className="btn-borrow"
                              onClick={() => handleBorrowBook(book.id)}
                              disabled={isProcessing}
                            >
                              {isProcessing ? 'Borrowing...' : 'Borrow Book'}
                            </button>
                          </div>
                        );
                      } else if (availability) {
                        // Book is not available
                        return (
                          <div className="borrow-status-section">
                            <p className="unavailable-badge">Currently Borrowed</p>
                            <p className="borrow-info">{availability.active_borrows} active borrow(s)</p>
                          </div>
                        );
                      }
                      return null;
                    })()}
                  </div>
                )}

                {isAdmin && (
                  <div className="book-actions">
                    <button
                      className="btn-edit"
                      onClick={() => handleEditClick(book)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn-delete"
                      onClick={() => handleDelete(book.id)}
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {showAddModal && (
          <div className="modal-overlay" onClick={handleCloseModal}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2>{editingBook ? 'Edit Book' : 'Add New Book'}</h2>
                <button className="btn-close" onClick={handleCloseModal}>×</button>
              </div>

              <form onSubmit={handleSubmit}>
                {formError && <div className="error-message">{formError}</div>}

                <div className="form-group">
                  <label htmlFor="title">Title *</label>
                  <input
                    type="text"
                    id="title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="author">Author *</label>
                  <input
                    type="text"
                    id="author"
                    value={formData.author}
                    onChange={(e) => setFormData({ ...formData, author: e.target.value })}
                    required
                  />
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="genre">Genre *</label>
                    <input
                      type="text"
                      id="genre"
                      value={formData.genre}
                      onChange={(e) => setFormData({ ...formData, genre: e.target.value })}
                      required
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="year">Year *</label>
                    <input
                      type="number"
                      id="year"
                      value={formData.year_published}
                      onChange={(e) => setFormData({ ...formData, year_published: parseInt(e.target.value) })}
                      required
                      min="1000"
                      max={new Date().getFullYear() + 1}
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="isbn">ISBN</label>
                  <input
                    type="text"
                    id="isbn"
                    value={formData.isbn}
                    onChange={(e) => setFormData({ ...formData, isbn: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="description">Description</label>
                  <textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={4}
                  />
                </div>

                <div className="form-group">
                  <label>Or Upload PDF File</label>
                  <div
                    className={`pdf-upload-area ${pdfDragActive ? 'active' : ''}`}
                    onDragEnter={handlePdfDrag}
                    onDragLeave={handlePdfDrag}
                    onDragOver={handlePdfDrag}
                    onDrop={handlePdfDrop}
                  >
                    <input
                      type="file"
                      id="pdf-upload"
                      accept=".pdf"
                      onChange={(e) => e.target.files && handlePdfFileSelect(e.target.files[0])}
                      style={{ display: 'none' }}
                      disabled={uploadingPdf}
                    />
                    <label htmlFor="pdf-upload" className="pdf-upload-label">
                      <div className="pdf-upload-content">
                        <p className="pdf-upload-icon">📄</p>
                        <p className="pdf-upload-text">
                          {uploadingPdf ? 'Processing PDF...' : 'Drag and drop your PDF here or click to select'}
                        </p>
                        <p className="pdf-upload-hint">Max file size: 50MB</p>
                      </div>
                    </label>
                  </div>
                </div>

                {formData.summary && (
                  <div className="form-group">
                    <label htmlFor="summary">AI Generated Summary</label>
                    <textarea
                      id="summary"
                      value={formData.summary}
                      onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                      rows={4}
                      readOnly
                      style={{ backgroundColor: '#f5f5f5' }}
                    />
                  </div>
                )}

                <div className="modal-actions">
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={handleCloseModal}
                    disabled={submitting}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={submitting}
                  >
                    {submitting ? 'Saving...' : (editingBook ? 'Update Book' : 'Add Book')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default Books;
