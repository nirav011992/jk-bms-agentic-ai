import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Login from './Login';
import { AuthProvider } from '../context/AuthContext';
import { apiService } from '../services/api';

jest.mock('../services/api');

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  Link: ({ children, to }: any) => <a href={to}>{children}</a>,
}));

const renderLogin = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Login />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('Login Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('should render login form with all elements', () => {
    renderLogin();

    expect(screen.getByText('Book Management System')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Login' })).toBeInTheDocument();
    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
    expect(screen.getByText(/don't have an account\?/i)).toBeInTheDocument();
    expect(screen.getByText(/register here/i)).toBeInTheDocument();
  });

  it('should update username and password inputs', async () => {
    renderLogin();
    const user = userEvent.setup();

    const usernameInput = screen.getByLabelText('Username') as HTMLInputElement;
    const passwordInput = screen.getByLabelText('Password') as HTMLInputElement;

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');

    expect(usernameInput.value).toBe('testuser');
    expect(passwordInput.value).toBe('password123');
  });

  it('should successfully login and navigate to dashboard', async () => {
    const mockTokens = {
      access_token: 'mock-token',
      refresh_token: 'mock-refresh',
      token_type: 'bearer',
    };

    const mockUser = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      role: 'user' as const,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    (apiService.login as jest.Mock).mockResolvedValue(mockTokens);
    (apiService.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

    renderLogin();
    const user = userEvent.setup();

    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: /login/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(apiService.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('should display error message on login failure', async () => {
    const errorMessage = 'Invalid credentials';
    (apiService.login as jest.Mock).mockRejectedValue({
      response: { data: { detail: errorMessage } },
    });

    renderLogin();
    const user = userEvent.setup();

    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: /login/i });

    await user.type(usernameInput, 'wronguser');
    await user.type(passwordInput, 'wrongpass');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('should display generic error message when no detail provided', async () => {
    (apiService.login as jest.Mock).mockRejectedValue(new Error('Network error'));

    renderLogin();
    const user = userEvent.setup();

    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: /login/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Login failed. Please try again.')).toBeInTheDocument();
    });
  });

  it('should show loading state during login', async () => {
    (apiService.login as jest.Mock).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    renderLogin();
    const user = userEvent.setup();

    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: /login/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password');
    await user.click(submitButton);

    expect(screen.getByText('Logging in...')).toBeInTheDocument();
    expect(submitButton).toBeDisabled();
    expect(usernameInput).toBeDisabled();
    expect(passwordInput).toBeDisabled();
  });

  it('should clear error message when submitting again', async () => {
    (apiService.login as jest.Mock)
      .mockRejectedValueOnce({
        response: { data: { detail: 'Invalid credentials' } },
      })
      .mockResolvedValueOnce({
        access_token: 'token',
        refresh_token: 'refresh',
        token_type: 'bearer',
      });

    (apiService.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      role: 'user' as const,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });

    renderLogin();
    const user = userEvent.setup();

    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: /login/i });

    await user.type(usernameInput, 'wronguser');
    await user.type(passwordInput, 'wrongpass');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });

    await user.clear(usernameInput);
    await user.clear(passwordInput);
    await user.type(usernameInput, 'correctuser');
    await user.type(passwordInput, 'correctpass');
    await user.click(submitButton);

    await waitFor(() => {
      expect(screen.queryByText('Invalid credentials')).not.toBeInTheDocument();
    });
  });

  it('should require username and password fields', () => {
    renderLogin();

    const usernameInput = screen.getByLabelText('Username') as HTMLInputElement;
    const passwordInput = screen.getByLabelText('Password') as HTMLInputElement;

    expect(usernameInput).toBeRequired();
    expect(passwordInput).toBeRequired();
  });

  it('should have correct password input type', () => {
    renderLogin();

    const passwordInput = screen.getByLabelText('Password') as HTMLInputElement;
    expect(passwordInput.type).toBe('password');
  });

  it('should prevent default form submission', async () => {
    const mockTokens = {
      access_token: 'mock-token',
      refresh_token: 'mock-refresh',
      token_type: 'bearer',
    };

    (apiService.login as jest.Mock).mockResolvedValue(mockTokens);
    (apiService.getCurrentUser as jest.Mock).mockResolvedValue({
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      role: 'user' as const,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });

    renderLogin();
    const user = userEvent.setup();

    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: /login/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });
});
