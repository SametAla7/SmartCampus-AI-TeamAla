import { Link, NavLink } from 'react-router-dom';

export default function Navbar({ onLogout, userName = 'Student' }) {
  return (
    <header className="navbar">
      <Link className="brand" to="/dashboard"><span className="brand-mark">✦</span>SmartCampus AI</Link>
      <div className="navbar-actions">
        <span className="user-label">{userName}</span>
        <button className="avatar" type="button" onClick={onLogout} title="Sign out">{userName.slice(0, 1).toUpperCase()}</button>
      </div>
    </header>
  );
}
