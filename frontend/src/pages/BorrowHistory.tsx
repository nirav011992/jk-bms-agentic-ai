import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { BorrowHistory as BorrowHistoryType } from '../types';
import Layout from '../components/common/Layout';
import '../styles/BorrowHistory.css';

const BorrowHistory: React.FC = () => {
  const [history, setHistory] = useState<BorrowHistoryType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBorrowHistory();
  }, []);

  const fetchBorrowHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getBorrowHistory();
      setHistory(data);
    } catch (err: any) {
      console.error('Error fetching borrow history:', err);
      setError(err.response?.data?.detail || 'Failed to fetch borrow history');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'active':
        return 'status-badge status-active';
      case 'returned':
        return 'status-badge status-returned';
      case 'overdue':
        return 'status-badge status-overdue';
      default:
        return 'status-badge';
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="borrow-history-container">
          <p>Loading borrow history...</p>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="borrow-history-container">
          <div className="error-message">{error}</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="borrow-history-container">
        <div className="borrow-history-header">
          <h1>My Borrow History</h1>
        </div>

        {history && (
          <>
            <div className="borrow-stats">
              <div className="stat-card">
                <h3>{history.total_borrows}</h3>
                <p>Total Borrows</p>
              </div>
              <div className="stat-card">
                <h3>{history.active_borrows}</h3>
                <p>Currently Borrowed</p>
              </div>
              <div className="stat-card">
                <h3>{history.returned_borrows}</h3>
                <p>Returned</p>
              </div>
              <div className="stat-card overdue">
                <h3>{history.overdue_borrows}</h3>
                <p>Overdue</p>
              </div>
            </div>

            <div className="borrow-list">
              <h2>Borrow Transactions</h2>
              {history.borrows.length === 0 ? (
                <p className="empty-state">You haven't borrowed any books yet.</p>
              ) : (
                <div className="borrow-table-container">
                  <table className="borrow-table">
                    <thead>
                      <tr>
                        <th>Book</th>
                        <th>Author</th>
                        <th>Borrow Date</th>
                        <th>Due Date</th>
                        <th>Return Date</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.borrows.map((borrow) => (
                        <tr key={borrow.id} className={borrow.is_overdue ? 'overdue-row' : ''}>
                          <td className="book-title">{borrow.book_title || 'Unknown'}</td>
                          <td>{borrow.book_author || 'Unknown'}</td>
                          <td>{formatDate(borrow.borrow_date)}</td>
                          <td className={borrow.is_overdue ? 'overdue-date' : ''}>
                            {formatDate(borrow.due_date)}
                          </td>
                          <td>{borrow.return_date ? formatDate(borrow.return_date) : '-'}</td>
                          <td>
                            <span className={getStatusBadgeClass(borrow.status)}>
                              {borrow.is_overdue && borrow.status === 'active' ? 'OVERDUE' : borrow.status.toUpperCase()}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </Layout>
  );
};

export default BorrowHistory;
