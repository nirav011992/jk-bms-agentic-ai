import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Layout from '../components/common/Layout';
import { apiService } from '../services/api';
import { User } from '../types';
import '../styles/UserManagement.css';

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { isAdmin } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAdmin) {
      navigate('/dashboard');
      return;
    }
    loadUsers();
  }, [isAdmin, navigate]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await apiService.getUsers();
      setUsers(response);
    } catch (err: any) {
      console.error('Error loading users:', err);
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleStatus = async (userId: number, currentStatus: boolean) => {
    try {
      await apiService.updateUser(userId, { is_active: !currentStatus });
      await loadUsers();
    } catch (err: any) {
      console.error('Error updating user status:', err);
      setError('Failed to update user status');
    }
  };

  const handleToggleRole = async (userId: number, currentRole: string) => {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';

    if (!window.confirm(`Are you sure you want to change this user's role to ${newRole}?`)) {
      return;
    }

    try {
      await apiService.updateUser(userId, { role: newRole });
      await loadUsers();
    } catch (err: any) {
      console.error('Error updating user role:', err);
      setError('Failed to update user role');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (!isAdmin) {
    return null;
  }

  if (loading) {
    return (
      <Layout>
        <div className="loading">Loading users...</div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="user-management-page">
        <div className="page-header">
          <div>
            <h1>User Management</h1>
            <p className="page-subtitle">Manage user accounts and permissions</p>
          </div>
        </div>

        {error && <div className="error-banner">{error}</div>}

        <div className="users-section">
          {users.length === 0 ? (
            <div className="empty-state">
              <p>No users found</p>
            </div>
          ) : (
            <div className="users-table-wrapper">
              <table className="users-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Full Name</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.id}>
                      <td>{user.id}</td>
                      <td className="username-cell">{user.username}</td>
                      <td>{user.email}</td>
                      <td>{user.full_name || '-'}</td>
                      <td>
                        <span className={`role-badge role-${user.role}`}>
                          {user.role}
                        </span>
                      </td>
                      <td>
                        <span className={`status-badge status-${user.is_active ? 'active' : 'inactive'}`}>
                          {user.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>{formatDate(user.created_at)}</td>
                      <td>
                        <div className="action-buttons">
                          <button
                            className="btn-small btn-role"
                            onClick={() => handleToggleRole(user.id, user.role)}
                            title={`Change role to ${user.role === 'admin' ? 'user' : 'admin'}`}
                          >
                            {user.role === 'admin' ? 'Make User' : 'Make Admin'}
                          </button>
                          <button
                            className={`btn-small ${user.is_active ? 'btn-deactivate' : 'btn-activate'}`}
                            onClick={() => handleToggleStatus(user.id, user.is_active)}
                            title={user.is_active ? 'Deactivate user' : 'Activate user'}
                          >
                            {user.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="stats-section">
          <div className="stat-card">
            <h3>Total Users</h3>
            <p className="stat-value">{users.length}</p>
          </div>
          <div className="stat-card">
            <h3>Active Users</h3>
            <p className="stat-value">{users.filter(u => u.is_active).length}</p>
          </div>
          <div className="stat-card">
            <h3>Admins</h3>
            <p className="stat-value">{users.filter(u => u.role === 'admin').length}</p>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default UserManagement;
