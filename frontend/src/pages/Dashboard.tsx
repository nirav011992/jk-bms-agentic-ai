import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from '../components/common/Layout';
import { apiService } from '../services/api';
import { Book } from '../types';
import '../styles/Dashboard.css';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({
    totalBooks: 0,
    totalDocuments: 0,
    recentBooks: [] as Book[]
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [books, documents] = await Promise.all([
        apiService.getBooks({ limit: 5 }),
        apiService.getDocuments().catch(() => [])
      ]);

      setStats({
        totalBooks: books.length,
        totalDocuments: documents.length,
        recentBooks: books.slice(0, 5)
      });
    } catch (err: any) {
      console.error('Error loading dashboard:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="loading">Loading dashboard...</div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="error-message">{error}</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="dashboard">
        <h1>Dashboard</h1>

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">📚</div>
            <div className="stat-content">
              <h3>Total Books</h3>
              <p className="stat-number">{stats.totalBooks}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📄</div>
            <div className="stat-content">
              <h3>Documents</h3>
              <p className="stat-number">{stats.totalDocuments}</p>
            </div>
          </div>

          <div className="stat-card clickable" onClick={() => navigate('/qa')}>
            <div className="stat-icon">💬</div>
            <div className="stat-content">
              <h3>Q&A System</h3>
              <p className="stat-text">Ask questions</p>
            </div>
          </div>
        </div>

        <div className="section">
          <div className="section-header">
            <h2>Recent Books</h2>
            <button className="btn-link" onClick={() => navigate('/books')}>
              View All →
            </button>
          </div>

          {stats.recentBooks.length === 0 ? (
            <div className="empty-state">
              <p>No books found. Add your first book!</p>
              <button className="btn-primary" onClick={() => navigate('/books')}>
                Go to Books
              </button>
            </div>
          ) : (
            <div className="books-list">
              {stats.recentBooks.map((book) => (
                <div key={book.id} className="book-card" onClick={() => navigate(`/books`)}>
                  <h3>{book.title}</h3>
                  <p className="book-author">by {book.author}</p>
                  <p className="book-genre">{book.genre} • {book.year_published}</p>
                  {book.summary && (
                    <p className="book-summary">{book.summary.substring(0, 150)}...</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="quick-actions">
          <h2>Quick Actions</h2>
          <div className="actions-grid">
            <button className="action-btn" onClick={() => navigate('/books')}>
              📖 Browse Books
            </button>
            <button className="action-btn" onClick={() => navigate('/documents')}>
              📁 Upload Document
            </button>
            <button className="action-btn" onClick={() => navigate('/qa')}>
              ❓ Ask Question
            </button>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Dashboard;
