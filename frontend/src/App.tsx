import React, { useState } from 'react';
import {
  BrowserRouter as Router, Routes, Route, useLocation, Link,
} from 'react-router-dom';
import { Moon, Sun, Menu } from 'lucide-react';
import Sidebar from './components/Sidebar';
import { useTheme } from './useTheme';

import Home from './pages/Home';
import Problem from './pages/Problem';
import Motivation from './pages/Motivation';
import ISLOverview from './pages/ISLOverview';
import Workflow from './pages/Workflow';
import GraphViewer from './pages/GraphViewer';
import DemoMode from './pages/DemoMode';
import Experiments from './pages/Experiments';
import Validation from './pages/Validation';
import Results from './pages/Results';
import Architecture from './pages/Architecture';
import Future from './pages/Future';

import './theme.css';

const TITLES: Record<string, string> = {
  '/': 'Home',
  '/problem': 'Problem Statement',
  '/motivation': 'Motivation',
  '/isl': 'ISL Overview',
  '/workflow': 'Algorithm Workflow',
  '/graph': 'Graph Viewer',
  '/demo': 'Demo Mode',
  '/experiments': 'Experiments',
  '/validation': 'Validation',
  '/results': 'Results',
  '/architecture': 'Architecture',
  '/future': 'Future Scope',
};

const Topbar: React.FC<{
  theme: string;
  onToggleTheme: () => void;
  onToggleNav: () => void;
}> = ({ theme, onToggleTheme, onToggleNav }) => {
  const { pathname } = useLocation();
  return (
    <div className="topbar">
      <div className="row" style={{ gap: 14 }}>
        <button className="btn icon ghost nav-toggle" onClick={onToggleNav} aria-label="Menu">
          <Menu size={18} />
        </button>
        <div className="crumbs">
          <Link to="/" style={{ color: 'inherit' }}>ISL</Link> &nbsp;/&nbsp;{' '}
          <b>{TITLES[pathname] ?? 'Page'}</b>
        </div>
      </div>
      <div className="row">
        <button className="btn icon ghost" onClick={onToggleTheme} aria-label="Toggle theme">
          {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
        </button>
      </div>
    </div>
  );
};

const ScrollTop: React.FC = () => {
  const { pathname } = useLocation();
  React.useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
};

const App: React.FC = () => {
  const [theme, toggleTheme] = useTheme();
  const [navOpen, setNavOpen] = useState(false);

  return (
    <Router>
      <ScrollTop />
      <div className="app-shell">
        <Sidebar open={navOpen} onNavigate={() => setNavOpen(false)} />
        <div className="main">
          <Topbar
            theme={theme}
            onToggleTheme={toggleTheme}
            onToggleNav={() => setNavOpen((o) => !o)}
          />
          <div className="content fade-in" key={theme}>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/problem" element={<Problem />} />
              <Route path="/motivation" element={<Motivation />} />
              <Route path="/isl" element={<ISLOverview />} />
              <Route path="/workflow" element={<Workflow />} />
              <Route path="/graph" element={<GraphViewer />} />
              <Route path="/demo" element={<DemoMode />} />
              <Route path="/experiments" element={<Experiments />} />
              <Route path="/validation" element={<Validation />} />
              <Route path="/results" element={<Results />} />
              <Route path="/architecture" element={<Architecture />} />
              <Route path="/future" element={<Future />} />
              <Route path="*" element={<Home />} />
            </Routes>
          </div>
        </div>
      </div>
    </Router>
  );
};

export default App;
