import React, { useState } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import { Box, Button, TextField, MenuItem } from '@mui/material';
import { styled } from '@mui/material/styles';

const IncidentCard = styled(Card)(({ theme, severity }) => ({
  borderLeft: `4px solid ${severity === 'high' ? theme.palette.error.main : severity === 'medium' ? theme.palette.warning.main : theme.palette.success.main}`,
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
  backgroundColor: severity === 'high' ? theme.palette.error.light : severity === 'medium' ? theme.palette.warning.light : theme.palette.success.light,
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
    }
  ]);

  const [newIncident, setNewIncident] = useState({
    type: 'fire',
    title: '',
    location: '',
    severity: 'low',
    timestamp: '',
    description: '',
    trustScore: 50,
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewIncident((prev) => ({ ...prev, [name]: value }));
  };

  const addNewIncident = () => {
    const incidentWithId = { ...newIncident, id: incidents.length + 1 };
    setIncidents((prev) => [...prev, incidentWithId]);
    setNewIncident({
      type: 'fire',
      title: '',
      location: '',
      severity: 'low',
      timestamp: '',
      description: '',
      trustScore: 50,
    });
  };

  const getIcon = (type) => {
    switch (type) {
      case 'fire':
        return <span role="img" aria-label="fire">🔥</span>;
      case 'flood':
        return <span role="img" aria-label="flood">💧</span>;
      case 'medical':
        return <span role="img" aria-label="medical">🚑</span>;
      default:
        return <span role="img" aria-label="alert">⚠️</span>;
    }
  };

  return (
    <Box maxWidth="md" mx="auto" p={4}>
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={4}>
        <Typography variant="h3" fontWeight="bold">CrisisCompass</Typography>
        <Box display="flex" alignItems="center" gap={1}>
          <span role="img" aria-label="live">📡</span>
          <Typography color="green" fontWeight="medium">Live Dashboard</Typography>
        </Box>
      </Box>

      {/* Form to add new incident */}
      <Box mb={4}>
        <Typography variant="h6" fontWeight="bold" mb={2}>Add New Incident</Typography>
        <Box display="flex" flexDirection="column" gap={2}>
          <TextField label="Title" name="title" value={newIncident.title} onChange={handleInputChange} />
          <TextField label="Location" name="location" value={newIncident.location} onChange={handleInputChange} />
          <TextField label="Timestamp" name="timestamp" value={newIncident.timestamp} onChange={handleInputChange} placeholder="YYYY-MM-DD HH:MM AM/PM" />
          <TextField label="Description" name="description" value={newIncident.description} onChange={handleInputChange} multiline rows={3} />
          <TextField
            label="Severity"
            name="severity"
            value={newIncident.severity}
            onChange={handleInputChange}
            select
          >
            <MenuItem value="low">Low</MenuItem>
            <MenuItem value="medium">Medium</MenuItem>
            <MenuItem value="high">High</MenuItem>
          </TextField>
          <Button variant="contained" color="primary" onClick={addNewIncident}>Add Incident</Button>
        </Box>
      </Box>

      {/* Active Incidents */}
      <Box display="flex" flexDirection="column" gap={2} mb={4}>
        <Typography variant="h6" fontWeight="bold">Active Incidents</Typography>
        {incidents.map((incident) => (
          <IncidentCard
            key={incident.id}
            severity={incident.severity}
            onClick={() => setSelectedIncident(incident)}
            sx={{
              borderColor: selectedIncident?.id === incident.id ? 'primary.main' : 'transparent',
            }}
          >
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
          </IncidentCard>
        ))}
      </Box>

      {/* Incident Details */}
      <Box>
        <Typography variant="h6" fontWeight="bold" mb={2}>Incident Details</Typography>
        {selectedIncident ? (
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={1} mb={2}>
                {getIcon(selectedIncident.type)}
                <Typography variant="h5" fontWeight="bold">{selectedIncident.title}</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">Location</Typography>
              <Typography variant="body1" mb={1}>{selectedIncident.location}</Typography>
              <Typography variant="body2" color="text.secondary">Time Reported</Typography>
              <Typography variant="body1" mb={1}>{selectedIncident.timestamp}</Typography>
              <Typography variant="body2" color="text.secondary">Description</Typography>
              <Typography variant="body1" mb={1}>{selectedIncident.description}</Typography>
              <Typography variant="body2" color="text.secondary">Trust Score</Typography>
              <Box display="flex" alignItems="center" gap={1}>
                <Box width="100%" height={8} bgcolor="grey.200" borderRadius={4}>
                <Box
                  width={`${selectedIncident.trustScore}%`}
                  height="100%"
                  bgcolor="green"
                  borderRadius={4}
                />
                </Box>
                <Typography variant="body2" fontWeight="bold">{selectedIncident.trustScore}%</Typography>
              </Box>
            </CardContent>
          </Card>
        ) : (
          <Card>
            <CardContent>
              <Typography variant="body2" color="text.secondary" align="center">
                Select an incident to view details
              </Typography>
            </CardContent>
          </Card>
        )}
      </Box>
    </Box>
  );
};

export default CrisisCompass;