import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home, HelpCircle, Zap, GitBranch, Network, FlaskConical,
  CheckCircle2, BarChart3, Layers, Compass, Play,
} from 'lucide-react';

type Item = { to: string; label: string; icon: React.ReactNode };
type Group = { label: string; items: Item[] };

/** Navigation mirrors the research narrative: story → interactive → evidence → engineering. */
const GROUPS: Group[] = [
  {
    label: 'The Story',
    items: [
      { to: '/', label: 'Home', icon: <Home size={17} /> },
      { to: '/problem', label: 'Problem', icon: <HelpCircle size={17} /> },
      { to: '/motivation', label: 'Motivation', icon: <Zap size={17} /> },
      { to: '/isl', label: 'ISL Overview', icon: <GitBranch size={17} /> },
      { to: '/workflow', label: 'Algorithm Workflow', icon: <Layers size={17} /> },
    ],
  },
  {
    label: 'See It Work',
    items: [
      { to: '/graph', label: 'Graph Viewer', icon: <Network size={17} /> },
      { to: '/demo', label: 'Demo Mode', icon: <Play size={17} /> },
    ],
  },
  {
    label: 'Evidence',
    items: [
      { to: '/experiments', label: 'Experiments', icon: <FlaskConical size={17} /> },
      { to: '/validation', label: 'Validation', icon: <CheckCircle2 size={17} /> },
      { to: '/results', label: 'Results', icon: <BarChart3 size={17} /> },
    ],
  },
  {
    label: 'Engineering',
    items: [
      { to: '/architecture', label: 'Architecture', icon: <Layers size={17} /> },
      { to: '/future', label: 'Future Scope', icon: <Compass size={17} /> },
    ],
  },
];

const Sidebar: React.FC<{ open: boolean; onNavigate: () => void }> = ({ open, onNavigate }) => (
  <aside className={`sidebar${open ? ' open' : ''}`}>
    <div className="sidebar-brand">
      <div className="logo">ISL</div>
      <div>
        <h1>ISL</h1>
        <span>Incremental Significance-Leiden</span>
      </div>
    </div>

    {GROUPS.map((g) => (
      <div key={g.label}>
        <div className="nav-group-label">{g.label}</div>
        {g.items.map((it) => (
          <NavLink
            key={it.to}
            to={it.to}
            end={it.to === '/'}
            className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            onClick={onNavigate}
          >
            {it.icon}
            {it.label}
          </NavLink>
        ))}
      </div>
    ))}
  </aside>
);

export default Sidebar;
