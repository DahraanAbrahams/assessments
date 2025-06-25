import axios from 'axios';

// Base URL for the backend API
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Fetch all bookings with optional filters.
 * @param {Object} filters - Optional filters: tenant, status, fromDate, toDate
 * @returns {Promise<Object[]>} List of bookings
 */
export async function fetchBookings(filters = {}) {
  try {
    const params = {};
    if (filters.tenant) params.tenant = filters.tenant;
    if (filters.status) params.status = filters.status;
    if (filters.fromDate) params.from_date = filters.fromDate;
    if (filters.toDate) params.to_date = filters.toDate;

    const response = await axios.get(`${BASE_URL}/admin/bookings/`, { params });
    return response.data.data.bookings;
  } catch (error) {
    // Optionally, you can throw or handle errors here
    throw error;
  }
}

/**
 * Fetch booking details by ID.
 * @param {string|number} id - Booking ID
 * @returns {Promise<Object>} Booking details
 */
export async function fetchBookingDetails(id) {
  try {
    const response = await axios.get(`${BASE_URL}/admin/bookings/${id}/`);
    return response.data;
  } catch (error) {
    throw error;
  }
} 