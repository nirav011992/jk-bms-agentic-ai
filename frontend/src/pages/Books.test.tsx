import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Books from './Books';
import { AuthProvider } from '../context/AuthContext';
import { apiService } from '../services/api';
import { Book, User } from '../types';

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

const mockAdminUser: User = { ...mockUser, role: 'admin' };

const mockBooks: Book[] = [
  {
    id: 1,
    title: 'Test Book 1',
    author: 'Author One',
    genre: 'Fiction',
    year_published: 2020,
    isbn: '1234567890',
    description: 'A test book',
    summary: 'Test summary',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    title: 'Test Book 2',
    author: 'Author Two',
    genre: 'Science',
    year_published: 2021,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
];

const renderBooks = (user: User = mockUser) => {
  (apiService.getCurrentUser as jest.Mock).mockResolvedValue(user);
  (apiService.getMyBorrows as jest.Mock).mockResolvedValue([]);
  jest.spyOn(Storage.prototype, 'getItem').mockReturnValue('mock-token');

  return render(
    <BrowserRouter>
      <AuthProvider>
        <Books />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('Books Component', () => {
  let confirmSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    confirmSpy = jest.spyOn(window, 'confirm').mockReturnValue(false);
  });

  afterEach(() => {
    confirmSpy.mockRestore();
  });

  describe('Initial render and loading', () => {
    it('should show loading state initially', () => {
      (apiService.getBooks as jest.Mock).mockImplementation(
        () => new Promise(() => {})
      );

      renderBooks();

      expect(screen.getByText('Loading books...')).toBeInTheDocument();
    });

    it('should load and display books', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks();

      await waitFor(() => {
        expect(screen.getByText('Test Book 1')).toBeInTheDocument();
      });

      expect(screen.getByText('Test Book 2')).toBeInTheDocument();
      expect(screen.getByText('by Author One')).toBeInTheDocument();
      expect(screen.getByText('by Author Two')).toBeInTheDocument();
    });

    it('should display error message on load failure', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      (apiService.getBooks as jest.Mock).mockRejectedValue(new Error('Failed to load'));

      renderBooks();

      await waitFor(() => {
        expect(screen.getByText('Failed to load books')).toBeInTheDocument();
      });

      consoleError.mockRestore();
    });

    it('should show empty state when no books exist', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue([]);

      renderBooks();

      await waitFor(() => {
        expect(screen.getByText('No books found')).toBeInTheDocument();
      });
    });
  });

  describe('Search and filter functionality', () => {
    it('should filter books by title', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks();
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByText('Test Book 1')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search by title or author/i);
      await user.type(searchInput, 'Book 1');

      expect(screen.getByText('Test Book 1')).toBeInTheDocument();
      expect(screen.queryByText('Test Book 2')).not.toBeInTheDocument();
    });

    it('should filter books by author', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks();
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByText('Test Book 1')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search by title or author/i);
      await user.type(searchInput, 'Author Two');

      expect(screen.queryByText('Test Book 1')).not.toBeInTheDocument();
      expect(screen.getByText('Test Book 2')).toBeInTheDocument();
    });

    it('should filter books by genre', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks();
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByText('Test Book 1')).toBeInTheDocument();
      });

      const genreSelect = screen.getByRole('combobox');
      await user.selectOptions(genreSelect, 'Fiction');

      expect(screen.getByText('Test Book 1')).toBeInTheDocument();
      expect(screen.queryByText('Test Book 2')).not.toBeInTheDocument();
    });

    it('should show all books when filters are cleared', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks();
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByText('Test Book 1')).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search by title or author/i);
      await user.type(searchInput, 'Book 1');

      expect(screen.getByText('Test Book 1')).toBeInTheDocument();
      expect(screen.queryByText('Test Book 2')).not.toBeInTheDocument();

      await user.clear(searchInput);

      expect(screen.getByText('Test Book 1')).toBeInTheDocument();
      expect(screen.getByText('Test Book 2')).toBeInTheDocument();
    });
  });

  describe('Admin functionality', () => {
    it('should show Add Book button for admin users', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks(mockAdminUser);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add book/i })).toBeInTheDocument();
      });
    });

    it('should not show Add Book button for regular users', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks(mockUser);

      await waitFor(() => {
        expect(screen.getByText('Test Book 1')).toBeInTheDocument();
      });

      expect(screen.queryByRole('button', { name: /add book/i })).not.toBeInTheDocument();
    });

    it('should show Edit and Delete buttons for admin users', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks(mockAdminUser);

      await waitFor(() => {
        expect(screen.getAllByText('Edit')).toHaveLength(2);
      });

      expect(screen.getAllByText('Delete')).toHaveLength(2);
    });

    it('should not show Edit and Delete buttons for regular users', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks(mockUser);

      await waitFor(() => {
        expect(screen.getByText('Test Book 1')).toBeInTheDocument();
      });

      expect(screen.queryByText('Edit')).not.toBeInTheDocument();
      expect(screen.queryByText('Delete')).not.toBeInTheDocument();
    });
  });

  describe('Add book modal', () => {
    it('should open add book modal when Add Book button is clicked', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks(mockAdminUser);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add book/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /add book/i }));

      expect(screen.getByText('Add New Book')).toBeInTheDocument();
      expect(screen.getByLabelText(/title \*/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/author \*/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/genre \*/i)).toBeInTheDocument();
    });

    it('should close modal when Cancel button is clicked', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks(mockAdminUser);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add book/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /add book/i }));
      expect(screen.getByText('Add New Book')).toBeInTheDocument();

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      await waitFor(() => {
        expect(screen.queryByText('Add New Book')).not.toBeInTheDocument();
      });
    });

    it('should create a new book successfully', async () => {
      const newBook: Book = {
        id: 3,
        title: 'New Book',
        author: 'New Author',
        genre: 'Mystery',
        year_published: 2024,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      (apiService.getBooks as jest.Mock)
        .mockResolvedValueOnce(mockBooks)
        .mockResolvedValueOnce([...mockBooks, newBook]);
      (apiService.createBook as jest.Mock).mockResolvedValue(newBook);

      renderBooks(mockAdminUser);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getAllByRole('button', { name: /add book/i })[0]).toBeInTheDocument();
      });

      await user.click(screen.getAllByRole('button', { name: /add book/i })[0]);

      await user.type(screen.getByLabelText(/title \*/i), 'New Book');
      await user.type(screen.getByLabelText(/author \*/i), 'New Author');
      await user.type(screen.getByLabelText(/genre \*/i), 'Mystery');
      await user.clear(screen.getByLabelText(/year \*/i));
      await user.type(screen.getByLabelText(/year \*/i), '2024');

      const submitButtons = screen.getAllByRole('button', { name: /add book/i });
      await user.click(submitButtons[submitButtons.length - 1]);

      await waitFor(() => {
        expect(apiService.createBook).toHaveBeenCalledWith({
          title: 'New Book',
          author: 'New Author',
          genre: 'Mystery',
          year_published: 2024,
          isbn: undefined,
          description: undefined,
        });
      });
    });

    it('should validate required fields', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks(mockAdminUser);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add book/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /add book/i }));
      const addButton = screen.getAllByRole('button', { name: /add book/i })[1];
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('Title is required')).toBeInTheDocument();
      });
    });

    it('should validate year range', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks(mockAdminUser);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /add book/i })).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /add book/i }));

      await user.type(screen.getByLabelText(/title \*/i), 'Test');
      await user.type(screen.getByLabelText(/author \*/i), 'Test');
      await user.type(screen.getByLabelText(/genre \*/i), 'Test');
      await user.clear(screen.getByLabelText(/year \*/i));
      await user.type(screen.getByLabelText(/year \*/i), '500');

      const addButton = screen.getAllByRole('button', { name: /add book/i })[1];
      await user.click(addButton);

      await waitFor(() => {
        expect(screen.getByText('Please enter a valid publication year')).toBeInTheDocument();
      });
    });
  });

  describe('Edit book functionality', () => {
    it('should open edit modal with book data', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks(mockAdminUser);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getAllByText('Edit')).toHaveLength(2);
      });

      await user.click(screen.getAllByText('Edit')[0]);

      expect(screen.getByText('Edit Book')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Test Book 1')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Author One')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Fiction')).toBeInTheDocument();
    });

    it('should update book successfully', async () => {
      const updatedBook = { ...mockBooks[0], title: 'Updated Title' };

      (apiService.getBooks as jest.Mock)
        .mockResolvedValueOnce(mockBooks)
        .mockResolvedValueOnce([updatedBook, mockBooks[1]]);
      (apiService.updateBook as jest.Mock).mockResolvedValue(updatedBook);

      renderBooks(mockAdminUser);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getAllByText('Edit')).toHaveLength(2);
      });

      await user.click(screen.getAllByText('Edit')[0]);

      const titleInput = screen.getByDisplayValue('Test Book 1');
      await user.clear(titleInput);
      await user.type(titleInput, 'Updated Title');

      await user.click(screen.getByRole('button', { name: /update book/i }));

      await waitFor(() => {
        expect(apiService.updateBook).toHaveBeenCalledWith(1, expect.objectContaining({
          title: 'Updated Title',
        }));
      });
    });

    it('should handle update error', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);
      (apiService.updateBook as jest.Mock).mockRejectedValue({
        response: { data: { detail: 'Update failed' } },
      });

      renderBooks(mockAdminUser);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getAllByText('Edit')).toHaveLength(2);
      });

      await user.click(screen.getAllByText('Edit')[0]);
      await user.click(screen.getByRole('button', { name: /update book/i }));

      await waitFor(() => {
        expect(screen.getByText('Update failed')).toBeInTheDocument();
      });

      consoleError.mockRestore();
    });
  });

  describe('Delete book functionality', () => {
    it('should delete book after confirmation', async () => {
      confirmSpy.mockReturnValue(true);
      (apiService.getBooks as jest.Mock)
        .mockResolvedValueOnce(mockBooks)
        .mockResolvedValueOnce([mockBooks[1]]);
      (apiService.deleteBook as jest.Mock).mockResolvedValue(undefined);

      renderBooks(mockAdminUser);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getAllByText('Delete')).toHaveLength(2);
      });

      await user.click(screen.getAllByText('Delete')[0]);

      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete this book?');

      await waitFor(() => {
        expect(apiService.deleteBook).toHaveBeenCalledWith(1);
      });
    });

    it('should not delete book if confirmation is cancelled', async () => {
      confirmSpy.mockReturnValue(false);
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks(mockAdminUser);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getAllByText('Delete')).toHaveLength(2);
      });

      await user.click(screen.getAllByText('Delete')[0]);

      expect(apiService.deleteBook).not.toHaveBeenCalled();
    });

    it('should handle delete error', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      confirmSpy.mockReturnValue(true);
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);
      (apiService.deleteBook as jest.Mock).mockRejectedValue(new Error('Delete failed'));

      renderBooks(mockAdminUser);
      const user = userEvent.setup();

      await waitFor(() => {
        expect(screen.getAllByText('Delete')).toHaveLength(2);
      });

      await user.click(screen.getAllByText('Delete')[0]);

      await waitFor(() => {
        expect(screen.getByText('Failed to delete book')).toBeInTheDocument();
      });

      consoleError.mockRestore();
    });
  });

  describe('Book display', () => {
    it('should display book details correctly', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue(mockBooks);

      renderBooks();

      await waitFor(() => {
        expect(screen.getByText('Test Book 1')).toBeInTheDocument();
      });

      expect(screen.getByText('by Author One')).toBeInTheDocument();
      expect(screen.getByText(/Fiction • 2020/i)).toBeInTheDocument();
      expect(screen.getByText(/ISBN: 1234567890/i)).toBeInTheDocument();
      expect(screen.getByText('A test book')).toBeInTheDocument();
      expect(screen.getByText('Test summary')).toBeInTheDocument();
    });

    it('should handle books without optional fields', async () => {
      (apiService.getBooks as jest.Mock).mockResolvedValue([mockBooks[1]]);

      renderBooks();

      await waitFor(() => {
        expect(screen.getByText('Test Book 2')).toBeInTheDocument();
      });

      expect(screen.queryByText(/ISBN:/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/AI Summary:/i)).not.toBeInTheDocument();
    });
  });
});
