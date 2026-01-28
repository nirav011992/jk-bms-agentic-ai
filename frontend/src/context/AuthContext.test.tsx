import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from './AuthContext';
import { apiService } from '../services/api';
import { User } from '../types';

jest.mock('../services/api');

const mockUser: User = {
  id: 1,
  email: 'test@example.com',
  username: 'testuser',
  full_name: 'Test User',
  role: 'user',
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const mockAdminUser: User = {
  ...mockUser,
  id: 2,
  username: 'adminuser',
  role: 'admin',
};

const mockTokens = {
  access_token: 'mock-access-token',
  refresh_token: 'mock-refresh-token',
  token_type: 'bearer',
};

describe('AuthContext', () => {
  let getItemSpy: jest.SpyInstance;
  let setItemSpy: jest.SpyInstance;
  let removeItemSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();
    getItemSpy = jest.spyOn(Storage.prototype, 'getItem').mockReturnValue(null);
    setItemSpy = jest.spyOn(Storage.prototype, 'setItem').mockImplementation();
    removeItemSpy = jest.spyOn(Storage.prototype, 'removeItem').mockImplementation();
  });

  afterEach(() => {
    getItemSpy.mockRestore();
    setItemSpy.mockRestore();
    removeItemSpy.mockRestore();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <AuthProvider>{children}</AuthProvider>
  );

  describe('useAuth hook', () => {
    it('should throw error when used outside AuthProvider', () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation();

      expect(() => {
        renderHook(() => useAuth());
      }).toThrow('useAuth must be used within an AuthProvider');

      consoleError.mockRestore();
    });
  });

  describe('Initial state', () => {
    it('should initialize with null user initially', async () => {
      getItemSpy.mockReturnValue(null);
      (apiService.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
      expect(result.current.isAdmin).toBe(false);
    });

    it('should load user from localStorage token on mount', async () => {
      getItemSpy.mockReturnValue('mock-token');
      (apiService.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(apiService.getCurrentUser).toHaveBeenCalled();
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should handle failed user load and clear tokens', async () => {
      getItemSpy.mockReturnValue('invalid-token');
      (apiService.getCurrentUser as jest.Mock).mockRejectedValue(new Error('Unauthorized'));

      const consoleError = jest.spyOn(console, 'error').mockImplementation();
      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(removeItemSpy).toHaveBeenCalledWith('access_token');
      expect(removeItemSpy).toHaveBeenCalledWith('refresh_token');
      expect(result.current.user).toBeNull();

      consoleError.mockRestore();
    });

    it('should not load user if no token exists', async () => {
      getItemSpy.mockReturnValue(null);
      (apiService.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(apiService.getCurrentUser).not.toHaveBeenCalled();
      expect(result.current.user).toBeNull();
    });
  });

  describe('login', () => {
    it('should successfully login user', async () => {
      (apiService.login as jest.Mock).mockResolvedValue(mockTokens);
      (apiService.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await act(async () => {
        await result.current.login({ username: 'testuser', password: 'password' });
      });

      expect(apiService.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password',
      });
      expect(setItemSpy).toHaveBeenCalledWith('access_token', mockTokens.access_token);
      expect(setItemSpy).toHaveBeenCalledWith('refresh_token', mockTokens.refresh_token);
      expect(apiService.getCurrentUser).toHaveBeenCalled();
      expect(result.current.user).toEqual(mockUser);
      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should throw error on failed login', async () => {
      const error = new Error('Invalid credentials');
      (apiService.login as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await expect(async () => {
        await act(async () => {
          await result.current.login({ username: 'testuser', password: 'wrong' });
        });
      }).rejects.toThrow('Invalid credentials');

      expect(result.current.user).toBeNull();
    });
  });

  describe('register', () => {
    it('should successfully register user', async () => {
      (apiService.register as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      const registerData = {
        email: 'test@example.com',
        username: 'testuser',
        password: 'Password123',
        full_name: 'Test User',
      };

      await act(async () => {
        await result.current.register(registerData);
      });

      expect(apiService.register).toHaveBeenCalledWith(registerData);
      expect(result.current.user).toEqual(mockUser);
    });

    it('should throw error on failed registration', async () => {
      const error = new Error('Username already exists');
      (apiService.register as jest.Mock).mockRejectedValue(error);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await expect(async () => {
        await act(async () => {
          await result.current.register({
            email: 'test@example.com',
            username: 'testuser',
            password: 'Password123',
          });
        });
      }).rejects.toThrow('Username already exists');
    });
  });

  describe('logout', () => {
    it('should clear tokens and user on logout', async () => {
      (apiService.login as jest.Mock).mockResolvedValue(mockTokens);
      (apiService.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await act(async () => {
        await result.current.login({ username: 'testuser', password: 'password' });
      });

      expect(result.current.user).toEqual(mockUser);

      act(() => {
        result.current.logout();
      });

      expect(removeItemSpy).toHaveBeenCalledWith('access_token');
      expect(removeItemSpy).toHaveBeenCalledWith('refresh_token');
      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('isAuthenticated', () => {
    it('should return true when user is logged in', async () => {
      (apiService.login as jest.Mock).mockResolvedValue(mockTokens);
      (apiService.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await act(async () => {
        await result.current.login({ username: 'testuser', password: 'password' });
      });

      expect(result.current.isAuthenticated).toBe(true);
    });

    it('should return false when user is not logged in', async () => {
      getItemSpy.mockReturnValue(null);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('isAdmin', () => {
    it('should return true for admin user', async () => {
      (apiService.login as jest.Mock).mockResolvedValue(mockTokens);
      (apiService.getCurrentUser as jest.Mock).mockResolvedValue(mockAdminUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await act(async () => {
        await result.current.login({ username: 'adminuser', password: 'password' });
      });

      expect(result.current.isAdmin).toBe(true);
    });

    it('should return false for regular user', async () => {
      (apiService.login as jest.Mock).mockResolvedValue(mockTokens);
      (apiService.getCurrentUser as jest.Mock).mockResolvedValue(mockUser);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      await act(async () => {
        await result.current.login({ username: 'testuser', password: 'password' });
      });

      expect(result.current.isAdmin).toBe(false);
    });

    it('should return false when no user is logged in', async () => {
      getItemSpy.mockReturnValue(null);

      const { result } = renderHook(() => useAuth(), { wrapper });

      await waitFor(() => {
        expect(result.current.loading).toBe(false);
      });

      expect(result.current.isAdmin).toBe(false);
    });
  });
});
