import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Header from './components/Header';
import Footer from './components/Footer';
import ScrollToTop from './components/ScrollToTop';

import Home from './pages/Home';
import Destinations from './pages/Destinations';
import DestinationDetails from './pages/DestinationDetails';
import Recommend from './pages/Recommend';
import Recommendations from './pages/Recommendations';
import Login from './pages/Login';
import Register from './pages/Register';

import './styles/App.css';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <ScrollToTop />
        <div className="app-container">
          <Header />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/destinations" element={<Destinations />} />
            <Route path="/destinations/:id" element={<DestinationDetails />} />
            <Route path="/recommend" element={<Recommend />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          <Footer />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}
