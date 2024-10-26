import React, { useState } from 'react';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import Typography from '@mui/material/Typography';
import { Box, Button, TextField, MenuItem } from '@mui/material';
import './App.css';

const CrisisCompass = () => {
  const [incidents, setIncidents] = useState([
    { id: 1, type: 'fire', title: 'Forest Fire', location: 'North Ridge Park', severity: 'high', timestamp: '2024-10-26 10:30 AM', description: 'Large forest fire spreading rapidly. Multiple teams required.', trustScore: 95 },
    { id: 2, type: 'medical', title: 'Multi-Vehicle Accident', location: 'Highway 101, Mile 45', severity: 'high', timestamp: '2024-10-26 10:45 AM', description: 'Multiple casualties reported. Emergency medical response needed.', trustScore: 90 },
    { id: 3, type: 'flood', title: 'Flash Flood Warning', location: 'Downtown Area', severity: 'medium', timestamp: '2024-10-26 11:00 AM', description: 'Rising water levels in downtown area. Evacuation may be necessary.', trustScore: 85 },
    { id: 4, type: 'chemical', title: 'Chemical Spill', location: 'Industrial Sector 4', severity: 'medium', timestamp: '2024-10-26 12:00 PM', description: 'Leak of hazardous materials reported. Nearby areas are at risk.', trustScore: 78 },
    { id: 5, type: 'storm', title: 'Severe Thunderstorm', location: 'Coastal Towns', severity: 'low', timestamp: '2024-10-26 01:15 PM', description: 'Heavy rain and high winds expected. Be cautious of flooding.', trustScore: 70 },
  ]);

  const [newIncident, setNewIncident] = useState({
    type: 'fire',
    title: '',
    location: '',
    timestamp: '',
    description: '',
  });

  const calculateSeverity = (incident) => {
    const { type, description } = incident;
    let score = 50;

    if (type === 'fire' || type === 'chemical' || type === 'flood') score += 20;
    else if (type === 'medical') score += 15;

    if (description.toLowerCase().includes('urgent') || description.toLowerCase().includes('hazard')) score += 10;
    if (description.toLowerCase().includes('evacuation') || description.toLowerCase().includes('high risk')) score += 15;

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

  return (
    <Box id="root">
      <Typography variant="h3" fontWeight="bold" className="logo">
        CrisisCompass
      </Typography>

      <Box className="card">
        <Typography variant="h6" fontWeight="bold">Report a New Incident</Typography>
        <TextField label="Title" name="title" value={newIncident.title} onChange={handleInputChange} fullWidth margin="normal" />
        <TextField label="Location" name="location" value={newIncident.location} onChange={handleInputChange} fullWidth margin="normal" />
        <TextField label="Timestamp" name="timestamp" value={newIncident.timestamp} onChange={handleInputChange} fullWidth margin="normal" placeholder="YYYY-MM-DD HH:MM AM/PM" />
        <TextField label="Description" name="description" value={newIncident.description} onChange={handleInputChange} fullWidth margin="normal" multiline rows={3} />
        <TextField label="Type" name="type" value={newIncident.type} onChange={handleInputChange} select fullWidth margin="normal">
          <MenuItem value="fire">Fire</MenuItem>
          <MenuItem value="medical">Medical</MenuItem>
          <MenuItem value="flood">Flood</MenuItem>
          <MenuItem value="chemical">Chemical</MenuItem>
          <MenuItem value="storm">Storm</MenuItem>
        </TextField>
        <Button variant="contained" onClick={addNewIncident}>Submit Incident</Button>
      </Box>

      <Box className="active-incidents">
        <Typography variant="h6" fontWeight="bold">Active Incidents</Typography>
        {incidents.map((incident) => (
          <Card key={incident.id} className={`incident-card status-${incident.severity}`}>
            <CardContent>
              <Typography variant="body1" fontWeight="bold">{incident.title}</Typography>
              <Typography variant="body2" color="text.secondary">{incident.location}</Typography>
              <Typography variant="body2" color="text.secondary">{incident.description}</Typography>
              <Typography variant="caption" color="text.secondary">Severity: {incident.severity}</Typography>
              <Typography variant="caption" color="text.secondary">Trust Score: {incident.trustScore}%</Typography>
            </CardContent>
          </Card>
        ))}
      </Box>
    </Box>
  );
};

export default CrisisCompass;
