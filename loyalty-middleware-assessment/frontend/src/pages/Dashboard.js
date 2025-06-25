import React, { useEffect, useState } from 'react';
import { Container, Typography, CircularProgress, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { fetchBookings } from '../api/bookings';
import { fetchTenants } from '../api/tenants';
import BookingsTable from '../components/BookingsTable';
import FilterBar from '../components/FilterBar';

const Dashboard = () => {
  const [bookings, setBookings] = useState([]);
  const [tenants, setTenants] = useState([]);
  const [filters, setFilters] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  // Fetch tenants for filter dropdown (only safe fields used)
  useEffect(() => {
    fetchTenants()
      .then(setTenants)
      .catch(() => setTenants([]));
  }, []);

  // Fetch bookings whenever filters change
  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchBookings(filters)
      .then(setBookings)
      .catch((err) => setError(err.message || 'Failed to load bookings'))
      .finally(() => setLoading(false));
  }, [filters]);

  // Handle filter changes
  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  // Reset filters
  const handleResetFilters = () => {
    setFilters({});
  };

  // Handle row click to navigate to booking details
  const handleRowClick = (id) => {
    navigate(`/bookings/${id}`);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>
        Admin Dashboard
      </Typography>
      <FilterBar
        tenants={tenants}
        filters={filters}
        onChange={handleFilterChange}
        onReset={handleResetFilters}
      />
      {loading ? (
        <CircularProgress sx={{ mt: 4 }} />
      ) : error ? (
        <Alert severity="error" sx={{ mt: 4 }}>{error}</Alert>
      ) : (
        <BookingsTable bookings={bookings} onRowClick={handleRowClick} />
      )}
    </Container>
  );
};

export default Dashboard; 