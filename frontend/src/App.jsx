import React from 'react';
import Header from './components/Header';
import Home from './pages/Home';
import './styles/App.css';

export default function App() {
  return (
    <div className="app-container">
      <Header />
      <Home />
      <footer className="app-footer">
        <p>© 2026 YATRA360 — AI-Enabled Smart Tourism Prototype</p>
      </footer>
    </div>
  );
}
