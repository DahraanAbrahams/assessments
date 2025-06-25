import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import BookingDetails from './pages/BookingDetails';

function App() {
  return (
    <Router>
      {/* Main application routes */}
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/bookings/:id" element={<BookingDetails />} />
      </Routes>
    </Router>
  );
}

export default App; 