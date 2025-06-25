import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Typography, Paper, Button, CircularProgress, Alert, Box, Divider } from '@mui/material';
import { fetchBookingDetails } from '../api/bookings';

const BookingDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchBookingDetails(id)
      .then(setBooking)
      .catch((err) => setError(err.message || 'Failed to load booking details'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
        <Button variant="outlined" sx={{ mt: 2 }} onClick={() => navigate(-1)}>
          Back to Dashboard
        </Button>
      </Container>
    );
  }

  if (!booking) {
    return null;
  }

  // Extract safe tenant info (e.g., name, id)
  const tenant = booking.tenant || {};

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Button variant="outlined" onClick={() => navigate('/')}>Back to Dashboard</Button>
      <Typography variant="h5" gutterBottom sx={{ mt: 2 }}>
        Booking Details
      </Typography>
      <Paper sx={{ p: 3 }}>
        <Box mb={2}>
          <Typography variant="subtitle1">Booking ID: {booking.id}</Typography>
          <Typography variant="subtitle1">Status: {booking.status}</Typography>
          <Typography variant="subtitle1">Created At: {new Date(booking.created_at).toLocaleString()}</Typography>
        </Box>
        <Divider sx={{ my: 2 }} />
        <Box mb={2}>
          <Typography variant="h6">Tenant</Typography>
          <Typography>Name: {tenant.name || tenant.id || '-'}</Typography>
        </Box>
        <Divider sx={{ my: 2 }} />
        <Box mb={2}>
          <Typography variant="h6">Flight</Typography>
          <Typography>Flight Number: {booking.flight?.flight_number || '-'}</Typography>
          <Typography>Departure: {booking.flight?.departure || '-'}</Typography>
          <Typography>Arrival: {booking.flight?.arrival || '-'}</Typography>
        </Box>
        <Divider sx={{ my: 2 }} />
        <Box mb={2}>
          <Typography variant="h6">Passengers</Typography>
          {booking.passengers && booking.passengers.length > 0 ? (
            booking.passengers.map((p, idx) => (
              <Typography key={idx}>{p.name || `${p.first_name} ${p.last_name}`}</Typography>
            ))
          ) : (
            <Typography>No passengers listed.</Typography>
          )}
        </Box>
        <Divider sx={{ my: 2 }} />
        <Box mb={2}>
          <Typography variant="h6">Payment</Typography>
          <Typography>Loyalty Amount: {booking.payment?.loyalty_amount || '-'}</Typography>
          <Typography>Loyalty Currency: {booking.payment?.loyalty_currency || '-'}</Typography>
          <Typography>USD Equivalent: {booking.payment?.usd_equivalent || '-'}</Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default BookingDetails; 