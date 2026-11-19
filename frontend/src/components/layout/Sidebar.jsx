import { NavLink } from 'react-router-dom';

const links = [
  ['Dashboard', '/dashboard'],
  ['Conversations', '/conversations'],
  ['Orientation', '/orientation'],
  ['Pre-registration', '/preinscription'],
  ['QCM', '/qcm'],
  ['Application dossier', '/dossier'],
  ['Academic review', '/responsable-academique'],
  ['Interviews', '/responsable-entretien'],
  ['Direction', '/direction'],
  ['Administration', '/administration'],
];

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <p className="sidebar-label">WORKSPACE</p>
      <nav aria-label="Main navigation">
        {links.map(([label, path]) => <NavLink key={path} to={path} className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{label}</NavLink>)}
      </nav>
      <p className="sidebar-foot">North American Private University</p>
    </aside>
  );
}
