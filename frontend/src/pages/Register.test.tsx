import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Register from './Register';
import { AuthProvider } from '../context/AuthContext';
import { apiService } from '../services/api';

jest.mock('../services/api');

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  Link: ({ children, to }: any) => <a href={to}>{children}</a>,
}));

const renderRegister = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Register />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('Register Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('should render registration form with all elements', () => {
    renderRegister();

    expect(screen.getByText('Book Management System')).toBeInTheDocument();
    expect(screen.getByText('Create Account')).toBeInTheDocument();
    expect(screen.getByLabelText(/^email \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^username \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText('Full Name')).toBeInTheDocument();
    expect(screen.getByLabelText(/^password \*/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^confirm password \*/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /register/i })).toBeInTheDocument();
    expect(screen.getByText(/already have an account\?/i)).toBeInTheDocument();
  });

  it('should update form inputs', async () => {
    renderRegister();
    const user = userEvent.setup();

    const emailInput = screen.getByLabelText(/^email \*/i) as HTMLInputElement;
    const usernameInput = screen.getByLabelText(/^username \*/i) as HTMLInputElement;
    const fullNameInput = screen.getByLabelText('Full Name') as HTMLInputElement;
    const passwordInput = screen.getByLabelText(/^password \*/i) as HTMLInputElement;
    const confirmPasswordInput = screen.getByLabelText(/^confirm password \*/i) as HTMLInputElement;

    await user.type(emailInput, 'test@example.com');
    await user.type(usernameInput, 'testuser');
    await user.type(fullNameInput, 'Test User');
    await user.type(passwordInput, 'Password123');
    await user.type(confirmPasswordInput, 'Password123');

    expect(emailInput.value).toBe('test@example.com');
    expect(usernameInput.value).toBe('testuser');
    expect(fullNameInput.value).toBe('Test User');
    expect(passwordInput.value).toBe('Password123');
    expect(confirmPasswordInput.value).toBe('Password123');
  });

  it('should successfully register and navigate to login', async () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      full_name: 'Test User',
      role: 'user' as const,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    (apiService.register as jest.Mock).mockResolvedValue(mockUser);

    renderRegister();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email \*/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^username \*/i), 'testuser');
    await user.type(screen.getByLabelText('Full Name'), 'Test User');
    await user.type(screen.getByLabelText(/^password \*/i), 'Password123');
    await user.type(screen.getByLabelText(/^confirm password \*/i), 'Password123');
    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(apiService.register).toHaveBeenCalledWith({
        email: 'test@example.com',
        username: 'testuser',
        password: 'Password123',
        full_name: 'Test User',
      });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login', {
        state: { message: 'Registration successful! Please login.' },
      });
    });
  });

  it('should validate required fields', async () => {
    renderRegister();
    const user = userEvent.setup();

    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText('All required fields must be filled')).toBeInTheDocument();
    });
  });

  it('should validate password length', async () => {
    renderRegister();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email \*/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^username \*/i), 'testuser');
    await user.type(screen.getByLabelText(/^password \*/i), 'Pass1');
    await user.type(screen.getByLabelText(/^confirm password \*/i), 'Pass1');
    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText('Password must be at least 8 characters long')).toBeInTheDocument();
    });
  });

  it('should validate password contains uppercase letter', async () => {
    renderRegister();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email \*/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^username \*/i), 'testuser');
    await user.type(screen.getByLabelText(/^password \*/i), 'password123');
    await user.type(screen.getByLabelText(/^confirm password \*/i), 'password123');
    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText('Password must contain at least one uppercase letter')).toBeInTheDocument();
    });
  });

  it('should validate password contains lowercase letter', async () => {
    renderRegister();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email \*/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^username \*/i), 'testuser');
    await user.type(screen.getByLabelText(/^password \*/i), 'PASSWORD123');
    await user.type(screen.getByLabelText(/^confirm password \*/i), 'PASSWORD123');
    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText('Password must contain at least one lowercase letter')).toBeInTheDocument();
    });
  });

  it('should validate password contains number', async () => {
    renderRegister();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email \*/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^username \*/i), 'testuser');
    await user.type(screen.getByLabelText(/^password \*/i), 'Password');
    await user.type(screen.getByLabelText(/^confirm password \*/i), 'Password');
    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText('Password must contain at least one number')).toBeInTheDocument();
    });
  });

  it('should validate passwords match', async () => {
    renderRegister();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email \*/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^username \*/i), 'testuser');
    await user.type(screen.getByLabelText(/^password \*/i), 'Password123');
    await user.type(screen.getByLabelText(/^confirm password \*/i), 'Password456');
    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    });
  });

  it('should display error message on registration failure', async () => {
    const errorMessage = 'Username already exists';
    (apiService.register as jest.Mock).mockRejectedValue({
      response: { data: { detail: errorMessage } },
    });

    renderRegister();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email \*/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^username \*/i), 'existinguser');
    await user.type(screen.getByLabelText(/^password \*/i), 'Password123');
    await user.type(screen.getByLabelText(/^confirm password \*/i), 'Password123');
    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('should display generic error message when no detail provided', async () => {
    (apiService.register as jest.Mock).mockRejectedValue(new Error('Network error'));

    renderRegister();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email \*/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^username \*/i), 'testuser');
    await user.type(screen.getByLabelText(/^password \*/i), 'Password123');
    await user.type(screen.getByLabelText(/^confirm password \*/i), 'Password123');
    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText('Registration failed. Please try again.')).toBeInTheDocument();
    });
  });

  it('should show loading state during registration', async () => {
    (apiService.register as jest.Mock).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    renderRegister();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email \*/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^username \*/i), 'testuser');
    await user.type(screen.getByLabelText(/^password \*/i), 'Password123');
    await user.type(screen.getByLabelText(/^confirm password \*/i), 'Password123');
    await user.click(screen.getByRole('button', { name: /register/i }));

    expect(screen.getByText('Creating Account...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /creating account\.\.\./i })).toBeDisabled();
  });

  it('should handle registration without optional full name', async () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      role: 'user' as const,
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    };

    (apiService.register as jest.Mock).mockResolvedValue(mockUser);

    renderRegister();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email \*/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^username \*/i), 'testuser');
    await user.type(screen.getByLabelText(/^password \*/i), 'Password123');
    await user.type(screen.getByLabelText(/^confirm password \*/i), 'Password123');
    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(apiService.register).toHaveBeenCalledWith({
        email: 'test@example.com',
        username: 'testuser',
        password: 'Password123',
        full_name: undefined,
      });
    });
  });

  it('should clear error on new submission', async () => {
    (apiService.register as jest.Mock)
      .mockRejectedValueOnce({
        response: { data: { detail: 'Error' } },
      })
      .mockResolvedValueOnce({
        id: 1,
        email: 'test@example.com',
        username: 'testuser',
        role: 'user' as const,
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      });

    renderRegister();
    const user = userEvent.setup();

    await user.type(screen.getByLabelText(/^email \*/i), 'test@example.com');
    await user.type(screen.getByLabelText(/^username \*/i), 'testuser');
    await user.type(screen.getByLabelText(/^password \*/i), 'Pass1');
    await user.type(screen.getByLabelText(/^confirm password \*/i), 'Pass1');
    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.getByText('Password must be at least 8 characters long')).toBeInTheDocument();
    });

    const passwordInput = screen.getByLabelText(/^password \*/i);
    const confirmPasswordInput = screen.getByLabelText(/^confirm password \*/i);
    await user.clear(passwordInput);
    await user.clear(confirmPasswordInput);
    await user.type(passwordInput, 'Password123');
    await user.type(confirmPasswordInput, 'Password123');
    await user.click(screen.getByRole('button', { name: /register/i }));

    await waitFor(() => {
      expect(screen.queryByText('Password must be at least 8 characters long')).not.toBeInTheDocument();
    });
  });

  it('should have correct input types', () => {
    renderRegister();

    const emailInput = screen.getByLabelText(/^email \*/i) as HTMLInputElement;
    const passwordInput = screen.getByLabelText(/^password \*/i) as HTMLInputElement;
    const confirmPasswordInput = screen.getByLabelText(/^confirm password \*/i) as HTMLInputElement;

    expect(emailInput.type).toBe('email');
    expect(passwordInput.type).toBe('password');
    expect(confirmPasswordInput.type).toBe('password');
  });

  it('should have required fields marked as required', () => {
    renderRegister();

    expect(screen.getByLabelText(/^email \*/i)).toBeRequired();
    expect(screen.getByLabelText(/^username \*/i)).toBeRequired();
    expect(screen.getByLabelText(/^password \*/i)).toBeRequired();
    expect(screen.getByLabelText(/^confirm password \*/i)).toBeRequired();
    expect(screen.getByLabelText('Full Name')).not.toBeRequired();
  });
});
