import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/common/Layout';
import { apiService } from '../services/api';
import { Book } from '../types';
import '../styles/Books.css';

interface BookFormData {
  title: string;
  author: string;
  genre: string;
  year_published: number;
  isbn?: string;
  description?: string;
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
    description: ''
  });
  const [formError, setFormError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { isAdmin } = useAuth();

  useEffect(() => {
    loadBooks();
  }, []);

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
      description: ''
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
      description: book.description || ''
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
        description: formData.description?.trim() || undefined
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
                  <h3>{book.title}</h3>
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
