import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Navbar from './components/layout/Navbar.jsx';
import Sidebar from './components/layout/Sidebar.jsx';
import Container from './components/layout/Container.jsx';
import './styles.css';

const pages = {
  '/dashboard': ['Dashboard', 'Your academic workspace at a glance.'],
  '/conversations': ['Conversations', 'Continue your conversation with the SmartCampus advisor.'],
  '/orientation': ['Orientation', 'Explore study paths that fit your profile.'],
  '/preinscription': ['Pre-registration', 'Start or continue your application.'],
  '/qcm': ['QCM', 'Complete your admission assessment.'],
  '/dossier': ['Application dossier', 'Review your application and required documents.'],
  '/responsable-academique': ['Academic review', 'Review candidates and academic decisions.'],
  '/responsable-entretien': ['Interviews', 'Manage candidate interviews and follow-ups.'],
  '/direction': ['Direction', 'Review admissions activity and reports.'],
  '/administration': ['Administration', 'Manage platform accounts and settings.'],
};

function Page({ title, description }) {
  return <section className="welcome-card"><span className="eyebrow">SMARTCAMPUS AI</span><h1>{title}</h1><p>{description}</p></section>;
}

function Login({ onLogin }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  return <main className="login-page"><form className="login-card" onSubmit={async (event) => { event.preventDefault(); setError(''); try { await onLogin(email, password); } catch (e) { setError(e.message || 'Sign in failed'); } }}>
    <span className="brand-mark">✦</span><p className="eyebrow">NAU SMARTCAMPUS AI</p><h1>Welcome back</h1><p className="muted">Sign in to continue to your campus workspace.</p>
    <label>Email<input type="email" required value={email} onChange={e => setEmail(e.target.value)} /></label><label>Password<input type="password" required value={password} onChange={e => setPassword(e.target.value)} /></label>
    {error && <p className="error">{error}</p>}<button className="primary" type="submit">Sign in</button>
  </form></main>;
}

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('access_token'));
  const [user, setUser] = useState(() => { try { return JSON.parse(localStorage.getItem('smartcampus_user') || 'null'); } catch { return null; } });
  const navigate = useNavigate();
  const location = useLocation();
  const login = async (email, mot_de_passe) => {
    const response = await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, mot_de_passe }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Invalid credentials');
    localStorage.setItem('access_token', data.access_token); localStorage.setItem('smartcampus_user', JSON.stringify(data.user));
    setToken(data.access_token); setUser(data.user); navigate('/dashboard');
  };
  const logout = () => { localStorage.removeItem('access_token'); localStorage.removeItem('smartcampus_user'); setToken(null); setUser(null); navigate('/login'); };
  useEffect(() => { if (token && location.pathname === '/login') navigate('/dashboard', { replace: true }); }, [token, location.pathname, navigate]);
  if (!token) return <Routes><Route path="/login" element={<Login onLogin={login} />} /><Route path="*" element={<Navigate to="/login" replace />} /></Routes>;
  return <div className="app-shell"><Navbar onLogout={logout} userName={user?.nom || 'Student'} /><div className="workspace"><Sidebar /><Container><Routes>{Object.entries(pages).map(([path, [title, description]]) => <Route key={path} path={path.slice(1)} element={<Page title={title} description={description} />} />)}<Route path="*" element={<Navigate to="/dashboard" replace />} /></Routes></Container></div></div>;
}

