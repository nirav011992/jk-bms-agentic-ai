import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import '../../styles/Layout.css';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { isAuthenticated, isAdmin, logout, user } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (!isAuthenticated) {
    return <>{children}</>;
  }

  return (
    <div className="layout">
      <nav className="navbar">
        <div className="nav-brand">
          <Link to="/dashboard">Book Manager</Link>
        </div>
        <ul className="nav-menu">
          <li><Link to="/dashboard">Dashboard</Link></li>
          <li><Link to="/books">Books</Link></li>
          {!isAdmin && <li><Link to="/borrow-history">My Borrows</Link></li>}
          <li><Link to="/documents">Documents</Link></li>
          <li><Link to="/qa">Q&A</Link></li>
          {isAdmin && <li><Link to="/users">Users</Link></li>}
        </ul>
        <div className="nav-actions">
          <span className="user-info">
            {user?.username || 'User'} {isAdmin && <span className="badge">Admin</span>}
          </span>
          <button onClick={handleLogout} className="btn-logout">
            Logout
          </button>
        </div>
      </nav>
      <main className="main-content">{children}</main>
    </div>
  );
};

export default Layout;
