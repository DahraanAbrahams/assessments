import React from 'react';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';

/**
 * BookingsTable component
 * @param {Object[]} bookings - Array of booking objects
 * @param {Function} onRowClick - Function to call when a row is clicked (receives booking ID)
 */
const BookingsTable = ({ bookings, onRowClick }) => {
  return (
    <TableContainer component={Paper} sx={{ mt: 2 }}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Booking ID</TableCell>
            <TableCell>Tenant</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Date</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {bookings.map((booking) => (
            <TableRow
              key={booking.id}
              hover
              sx={{ cursor: 'pointer' }}
              onClick={() => onRowClick(booking.id)}
            >
              <TableCell>{booking.id}</TableCell>
              <TableCell>{booking.tenant?.name || booking.tenant?.id || '-'}</TableCell>
              <TableCell>{booking.status}</TableCell>
              <TableCell>{new Date(booking.created_at).toLocaleString()}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default BookingsTable; 