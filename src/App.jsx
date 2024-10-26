import React, { useState } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import { Box, Button, TextField, MenuItem } from '@mui/material';
import { styled } from '@mui/material/styles';
import './app.css';

const IncidentCard = styled(Card)(({ theme, severity }) => ({
  borderLeft: `4px solid ${
    severity === 'high'
      ? theme.palette.error.main
      : severity === 'medium'
      ? theme.palette.warning.main
      : theme.palette.success.main
  }`,
  borderRadius: 8,
  boxShadow: severity === 'high' ? '0 0 8px rgba(255, 0, 0, 0.3)' : '0 0 4px rgba(0, 0, 0, 0.1)',
  cursor: 'pointer',
  transition: 'all 0.3s ease',
  '&:hover': {
    boxShadow: '0 0 12px rgba(0, 0, 255, 0.3)',
  },
}));

const StatusBadge = styled(Box)(({ theme, severity }) => ({
  padding: '4px 8px',
  borderRadius: 8,
  color: '#000',
  backgroundColor:
    severity === 'high'
      ? theme.palette.error.light
      : severity === 'medium'
      ? theme.palette.warning.light
      : theme.palette.success.light,
  fontWeight: 'bold',
  fontSize: '0.75rem',
  display: 'inline-block',
}));

const CrisisCompass = () => {
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [incidents, setIncidents] = useState([
    {
      id: 1,
      type: 'fire',
      title: 'Forest Fire',
      location: 'North Ridge Park',
      severity: 'high',
      timestamp: '2024-10-26 10:30 AM',
      description: 'Large forest fire spreading rapidly. Multiple teams required.',
      trustScore: 95,
    },
    {
      id: 2,
      type: 'medical',
      title: 'Multi-Vehicle Accident',
      location: 'Highway 101, Mile 45',
      severity: 'high',
      timestamp: '2024-10-26 10:45 AM',
      description: 'Multiple casualties reported. Emergency medical response needed.',
      trustScore: 90,
    },
    {
      id: 3,
      type: 'flood',
      title: 'Flash Flood Warning',
      location: 'Downtown Area',
      severity: 'medium',
      timestamp: '2024-10-26 11:00 AM',
      description: 'Rising water levels in downtown area. Evacuation may be necessary.',
      trustScore: 85,
    },
    {
      id: 4,
      type: 'chemical',
      title: 'Chemical Spill',
      location: 'Industrial Sector 4',
      severity: 'medium',
      timestamp: '2024-10-26 12:00 PM',
      description: 'Leak of hazardous materials reported. Nearby areas are at risk.',
      trustScore: 78,
    },
    {
      id: 5,
      type: 'storm',
      title: 'Severe Thunderstorm',
      location: 'Coastal Towns',
      severity: 'low',
      timestamp: '2024-10-26 01:15 PM',
      description: 'Heavy rain and high winds expected. Be cautious of flooding.',
      trustScore: 70,
    },
  ]);

  const [newIncident, setNewIncident] = useState({
    type: 'fire',
    title: '',
    location: '',
    timestamp: '',
    description: '',
  });

  const calculateSeverity = (incident) => {
    const { type, title, location, description } = incident;
    let score = 50;

    // Increase score based on type
    if (type === 'fire' || type === 'chemical' || type === 'flood') score += 20;
    else if (type === 'medical') score += 15;
    
    // Increase based on description keywords
    if (description.toLowerCase().includes('urgent') || description.toLowerCase().includes('hazard')) score += 10;
    if (description.toLowerCase().includes('evacuation') || description.toLowerCase().includes('high risk')) score += 15;

    // Set severity based on score
    return score > 80 ? 'high' : score > 60 ? 'medium' : 'low';
  };

  const addNewIncident = () => {
    const severity = calculateSeverity(newIncident);
    const incidentWithId = {
      ...newIncident,
      id: incidents.length + 1,
      severity,
      trustScore: Math.floor(Math.random() * 20) + 60,
    };
    setIncidents((prev) => [...prev, incidentWithId]);
    setNewIncident({
      type: 'fire',
      title: '',
      location: '',
      timestamp: '',
      description: '',
    });
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewIncident((prev) => ({ ...prev, [name]: value }));
  };

  const getIcon = (type) => {
    switch (type) {
      case 'fire':
        return <span role="img" aria-label="fire">🔥</span>;
      case 'flood':
        return <span role="img" aria-label="flood">💧</span>;
      case 'medical':
        return <span role="img" aria-label="medical">🚑</span>;
      case 'chemical':
        return <span role="img" aria-label="chemical">☣️</span>;
      case 'storm':
        return <span role="img" aria-label="storm">🌩️</span>;
      default:
        return <span role="img" aria-label="alert">⚠️</span>;
    }
  };

  return (
    <Box id="root">
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={4}>
        <Typography variant="h3" fontWeight="bold" className="logo">
          CrisisCompass
        </Typography>
        <Box display="flex" alignItems="center" gap={1}>
          <span role="img" aria-label="live">📡</span>
          <Typography color="green" fontWeight="medium">
            Live Dashboard
          </Typography>
        </Box>
      </Box>

      {/* User Input Section */}
      <Box className="card" mb={4}>
        <Typography variant="h6" fontWeight="bold" mb={2}>
          Report a New Incident
        </Typography>
        <Box display="flex" flexDirection="column" gap={2}>
          <TextField label="Title" name="title" value={newIncident.title} onChange={handleInputChange} />
          <TextField label="Location" name="location" value={newIncident.location} onChange={handleInputChange} />
          <TextField label="Timestamp" name="timestamp" value={newIncident.timestamp} onChange={handleInputChange} placeholder="YYYY-MM-DD HH:MM AM/PM" />
          <TextField label="Description" name="description" value={newIncident.description} onChange={handleInputChange} multiline rows={3} />
          <TextField
            label="Type"
            name="type"
            value={newIncident.type}
            onChange={handleInputChange}
            select
          >
            <MenuItem value="fire">Fire</MenuItem>
            <MenuItem value="medical">Medical</MenuItem>
            <MenuItem value="flood">Flood</MenuItem>
            <MenuItem value="chemical">Chemical</MenuItem>
            <MenuItem value="storm">Storm</MenuItem>
          </TextField>
          <Button variant="contained" color="primary" onClick={addNewIncident}>
            Submit Incident
          </Button>
        </Box>
      </Box>

      {/* Active Incidents */}
      <Box display="flex" flexDirection="column" gap={2} mb={4}>
        <Typography variant="h6" fontWeight="bold">Active Incidents</Typography>
        {incidents.map((incident) => (
          <IncidentCard key={incident.id} severity={incident.severity} onClick={() => setSelectedIncident(incident)}>
            <CardContent sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box display="flex" alignItems="center" gap={2}>
                {getIcon(incident.type)}
                <Box>
                  <Typography variant="body1" fontWeight="bold">{incident.title}</Typography>
                  <Typography variant="body2" color="text.secondary">{incident.location}</Typography>
                </Box>
              </Box>
              <StatusBadge severity={incident.severity}>{incident.severity.toUpperCase()}</StatusBadge>
            </CardContent>
            <CardContent>
              <Typography variant="body2" color="text.secondary">{incident.description}</Typography>
              <Typography variant="caption" display="block" color="text.secondary">{incident.timestamp}</Typography>
              <Typography variant="caption" color="text.secondary" fontWeight="bold">Trust Score: {incident.trustScore}%</Typography>
            </CardContent>
          </IncidentCard>
        ))}
      </Box>

      {/* Incident Details - Display selected incident info if any */}
      {selectedIncident && (
        <Box className="card" mt={2}>
          <Typography variant="h6" fontWeight="bold" mb={2}>Incident Details</Typography>
          <Typography variant="body1" fontWeight="bold">{selectedIncident.title}</Typography>
          <Typography variant="body2" color="text.secondary">{selectedIncident.location}</Typography>
          <Typography variant="body2" mt={1}>{selectedIncident.description}</Typography>
          <Typography variant="caption" color="text.secondary" display="block">{selectedIncident.timestamp}</Typography>
          <Typography variant="caption" color="text.secondary" fontWeight="bold">Severity: {selectedIncident.severity.toUpperCase()}</Typography>
          <Typography variant="caption" color="text.secondary" fontWeight="bold">Trust Score: {selectedIncident.trustScore}%</Typography>
          <Button variant="outlined" color="secondary" onClick={() => setSelectedIncident(null)} mt={2}>Close</Button>
        </Box>
      )}
    </Box>
  );
};

export default CrisisCompass;