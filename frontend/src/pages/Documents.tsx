import React, { useEffect, useState } from 'react';
import Layout from '../components/common/Layout';
import { apiService } from '../services/api';
import { Document } from '../types';
import '../styles/Documents.css';

const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await apiService.getDocuments();
      setDocuments(data);
    } catch (err: any) {
      console.error('Error loading documents:', err);
      setError('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUploadError('');
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];

      // Validate file type
      const allowedTypes = ['text/plain', 'application/pdf', 'application/msword',
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];

      if (!allowedTypes.includes(file.type) && !file.name.endsWith('.txt') && !file.name.endsWith('.md')) {
        setUploadError('Please upload a text file (TXT, PDF, DOC, DOCX, or MD)');
        setSelectedFile(null);
        return;
      }

      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setUploadError('File size must be less than 10MB');
        setSelectedFile(null);
        return;
      }

      setSelectedFile(file);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile) {
      setUploadError('Please select a file to upload');
      return;
    }

    try {
      setUploading(true);
      setUploadError('');

      const reader = new FileReader();

      reader.onload = async (event) => {
        try {
          const content = event.target?.result as string;

          await apiService.uploadDocument({
            filename: selectedFile.name,
            file_content: content,
            doc_metadata: {
              size: selectedFile.size,
              type: selectedFile.type,
              uploadedAt: new Date().toISOString()
            }
          });

          await loadDocuments();
          setSelectedFile(null);

          // Reset file input
          const fileInput = document.getElementById('file-input') as HTMLInputElement;
          if (fileInput) fileInput.value = '';
        } catch (err: any) {
          console.error('Error uploading document:', err);
          setUploadError(err.response?.data?.detail || 'Failed to upload document');
        } finally {
          setUploading(false);
        }
      };

      reader.onerror = () => {
        setUploadError('Failed to read file');
        setUploading(false);
      };

      reader.readAsText(selectedFile);
    } catch (err: any) {
      console.error('Error during upload:', err);
      setUploadError('An error occurred during upload');
      setUploading(false);
    }
  };

  const handleDelete = async (documentId: number) => {
    if (!window.confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      await apiService.deleteDocument(documentId);
      await loadDocuments();
    } catch (err: any) {
      console.error('Error deleting document:', err);
      setError('Failed to delete document');
    }
  };

  const handleIngest = async (documentId: number) => {
    try {
      await apiService.ingestDocument(documentId);
      await loadDocuments();
    } catch (err: any) {
      console.error('Error ingesting document:', err);
      setError('Failed to ingest document');
    }
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'status-badge status-completed';
      case 'processing':
        return 'status-badge status-processing';
      case 'failed':
        return 'status-badge status-failed';
      default:
        return 'status-badge status-pending';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Layout>
        <div className="loading">Loading documents...</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="documents-page">
        <div className="page-header">
          <h1>Document Management</h1>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <div className="upload-section">
          <h2>Upload New Document</h2>
          <p className="upload-description">
            Upload text documents for RAG-based question answering. Supported formats: TXT, PDF, DOC, DOCX, MD (max 10MB)
          </p>

          <form onSubmit={handleUpload} className="upload-form">
            {uploadError && <div className="error-message">{uploadError}</div>}

            <div className="file-input-wrapper">
              <input
                type="file"
                id="file-input"
                onChange={handleFileSelect}
                accept=".txt,.pdf,.doc,.docx,.md"
                disabled={uploading}
              />
              {selectedFile && (
                <div className="selected-file">
                  <span>Selected: {selectedFile.name}</span>
                  <span className="file-size">
                    ({(selectedFile.size / 1024).toFixed(2)} KB)
                  </span>
                </div>
              )}
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={!selectedFile || uploading}
            >
              {uploading ? 'Uploading...' : 'Upload Document'}
            </button>
          </form>
        </div>

        <div className="documents-section">
          <h2>Your Documents</h2>

          {documents.length === 0 ? (
            <div className="empty-state">
              <p>No documents uploaded yet. Upload your first document to get started!</p>
            </div>
          ) : (
            <div className="documents-list">
              {documents.map((doc) => (
                <div key={doc.id} className="document-item">
                  <div className="document-info">
                    <h3>{doc.filename}</h3>
                    <div className="document-meta">
                      <span className={getStatusBadgeClass(doc.ingestion_status)}>
                        {doc.ingestion_status}
                      </span>
                      <span className="document-date">
                        Uploaded: {formatDate(doc.created_at)}
                      </span>
                    </div>
                  </div>

                  <div className="document-actions">
                    {doc.ingestion_status === 'pending' && (
                      <button
                        className="btn-ingest"
                        onClick={() => handleIngest(doc.id)}
                      >
                        Ingest
                      </button>
                    )}
                    <button
                      className="btn-delete"
                      onClick={() => handleDelete(doc.id)}
                    >
                      Delete
                    </button>
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

export default Documents;
