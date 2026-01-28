import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import App from './App';
import { apiService } from './services/api';

jest.mock('./services/api');

jest.mock('./pages/Login', () => ({
  __esModule: true,
  default: () => <div>Login Page</div>,
}));

jest.mock('./pages/Register', () => ({
  __esModule: true,
  default: () => <div>Register Page</div>,
}));

jest.mock('./pages/Dashboard', () => ({
  __esModule: true,
  default: () => <div>Dashboard Page</div>,
}));

jest.mock('./pages/Books', () => ({
  __esModule: true,
  default: () => <div>Books Page</div>,
}));

jest.mock('./pages/Documents', () => ({
  __esModule: true,
  default: () => <div>Documents Page</div>,
}));

jest.mock('./pages/QA', () => ({
  __esModule: true,
  default: () => <div>QA Page</div>,
}));

jest.mock('./pages/UserManagement', () => ({
  __esModule: true,
  default: () => <div>User Management Page</div>,
}));

describe('App Component', () => {
  let getItemSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    getItemSpy = jest.spyOn(Storage.prototype, 'getItem');
  });

  afterEach(() => {
    getItemSpy.mockRestore();
  });

  describe('Authentication flows', () => {
    it('should show loading state initially when token exists', () => {
      getItemSpy.mockReturnValue('mock-token');
      (apiService.getCurrentUser as jest.Mock).mockImplementation(
        () => new Promise(() => {})
      );

      render(<App />);

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('should render login page when not authenticated', async () => {
      getItemSpy.mockReturnValue(null);

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText('Login Page')).toBeInTheDocument();
      });
    });

    it('should redirect to login on authentication error', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      getItemSpy.mockReturnValue('invalid-token');
      (apiService.getCurrentUser as jest.Mock).mockRejectedValue(new Error('Unauthorized'));

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText('Login Page')).toBeInTheDocument();
      });

      consoleError.mockRestore();
    });
  });
});
