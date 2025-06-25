import React from 'react';
import { Box, FormControl, InputLabel, Select, MenuItem, TextField, Button } from '@mui/material';

/**
 * FilterBar component for filtering bookings
 * @param {Object[]} tenants - Array of tenant objects for dropdown
 * @param {Object} filters - Current filter values
 * @param {Function} onChange - Called when a filter value changes
 * @param {Function} onReset - Called when the reset button is clicked
 */
const FilterBar = ({ tenants, filters, onChange, onReset }) => {
  return (
    <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
      <FormControl sx={{ minWidth: 150 }} size="small">
        <InputLabel>Tenant</InputLabel>
        <Select
          value={filters.tenant || ''}
          label="Tenant"
          onChange={e => onChange({ ...filters, tenant: e.target.value })}
        >
          <MenuItem value="">All</MenuItem>
          {tenants.map((tenant) => (
            <MenuItem key={tenant.slug} value={tenant.slug}>
              {tenant.name || tenant.slug}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <FormControl sx={{ minWidth: 150 }} size="small">
        <InputLabel>Status</InputLabel>
        <Select
          value={filters.status || ''}
          label="Status"
          onChange={e => onChange({ ...filters, status: e.target.value })}
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="confirmed">Confirmed</MenuItem>
          <MenuItem value="pending_approval">Pending Approval</MenuItem>
          <MenuItem value="cancelled">Cancelled</MenuItem>
        </Select>
      </FormControl>
      <TextField
        label="From Date"
        type="date"
        size="small"
        InputLabelProps={{ shrink: true }}
        value={filters.fromDate || ''}
        onChange={e => onChange({ ...filters, fromDate: e.target.value })}
      />
      <TextField
        label="To Date"
        type="date"
        size="small"
        InputLabelProps={{ shrink: true }}
        value={filters.toDate || ''}
        onChange={e => onChange({ ...filters, toDate: e.target.value })}
      />
      <Button variant="outlined" color="secondary" onClick={onReset} sx={{ alignSelf: 'center' }}>
        Reset
      </Button>
    </Box>
  );
};

export default FilterBar; 