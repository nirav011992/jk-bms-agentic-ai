import React, { useState } from 'react';
import Layout from '../components/common/Layout';
import { apiService } from '../services/api';
import { QAResponse } from '../types';
import '../styles/QA.css';

interface QuestionHistory {
  id: number;
  question: string;
  response: QAResponse;
  timestamp: Date;
}

const QA: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState<QuestionHistory[]>([]);
  const [contextLimit, setContextLimit] = useState(5);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!question.trim()) {
      setError('Please enter a question');
      return;
    }

    try {
      setLoading(true);
      setError('');

      const response = await apiService.askQuestion(question.trim(), contextLimit);

      const newEntry: QuestionHistory = {
        id: Date.now(),
        question: question.trim(),
        response,
        timestamp: new Date()
      };

      setHistory([newEntry, ...history]);
      setQuestion('');
    } catch (err: any) {
      console.error('Error asking question:', err);
      setError(err.response?.data?.detail || 'Failed to get answer. Please make sure you have uploaded and ingested documents.');
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = () => {
    if (window.confirm('Are you sure you want to clear the question history?')) {
      setHistory([]);
    }
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Layout>
      <div className="qa-page">
        <div className="page-header">
          <div>
            <h1>AI-Powered Q&A</h1>
            <p className="page-subtitle">
              Ask questions about your uploaded documents using RAG (Retrieval-Augmented Generation)
            </p>
          </div>
          {history.length > 0 && (
            <button className="btn-secondary" onClick={handleClearHistory}>
              Clear History
            </button>
          )}
        </div>

        <div className="qa-interface">
          <form onSubmit={handleSubmit} className="question-form">
            {error && <div className="error-message">{error}</div>}

            <div className="question-input-group">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask a question about your documents..."
                rows={3}
                disabled={loading}
                className="question-input"
              />

              <div className="form-controls">
                <div className="context-control">
                  <label htmlFor="context-limit">
                    Context Documents: {contextLimit}
                  </label>
                  <input
                    type="range"
                    id="context-limit"
                    min="1"
                    max="10"
                    value={contextLimit}
                    onChange={(e) => setContextLimit(parseInt(e.target.value))}
                    disabled={loading}
                  />
                </div>

                <button
                  type="submit"
                  className="btn-primary"
                  disabled={loading || !question.trim()}
                >
                  {loading ? 'Searching...' : 'Ask Question'}
                </button>
              </div>
            </div>
          </form>

          {history.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">💬</div>
              <h3>No questions asked yet</h3>
              <p>Upload documents and start asking questions to get AI-powered answers</p>
            </div>
          ) : (
            <div className="qa-history">
              {history.map((entry) => (
                <div key={entry.id} className="qa-entry">
                  <div className="question-block">
                    <div className="question-header">
                      <span className="question-icon">Q</span>
                      <span className="timestamp">{formatTimestamp(entry.timestamp)}</span>
                    </div>
                    <p className="question-text">{entry.question}</p>
                  </div>

                  <div className="answer-block">
                    <div className="answer-header">
                      <span className="answer-icon">A</span>
                      {entry.response.confidence && (
                        <span className="confidence">
                          Confidence: {(entry.response.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                    <p className="answer-text">{entry.response.answer}</p>

                    {entry.response.relevant_documents && entry.response.relevant_documents.length > 0 && (
                      <div className="sources-section">
                        <h4>Sources:</h4>
                        <div className="sources-list">
                          {entry.response.relevant_documents.map((doc, idx) => (
                            <div key={idx} className="source-item">
                              <div className="source-header">
                                <span className="source-filename">{doc.filename}</span>
                                <span className="source-score">
                                  {(doc.relevance_score * 100).toFixed(0)}% relevant
                                </span>
                              </div>
                              <p className="source-excerpt">{doc.excerpt}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};

export default QA;
