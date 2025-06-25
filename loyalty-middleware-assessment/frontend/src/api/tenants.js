import axios from 'axios';

// Base URL for the backend API
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

/**
 * Fetch all tenants (for filter dropdowns).
 * @returns {Promise<Object[]>} List of tenants
 */
export async function fetchTenants() {
  try {
    // The tenants endpoint may require a special header for internal access
    const response = await axios.get(`${BASE_URL}/tenants/`, {
      headers: { 'X-Internal-Access': 'true' },
    });
    return response.data.data;
  } catch (error) {
    throw error;
  }
} 