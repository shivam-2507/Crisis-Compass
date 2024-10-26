import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, TextField, MenuItem } from '@mui/material';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import './App.css';

const CrisisCompass = () => {
  const [incidents, setIncidents] = useState([
    { id: 1, type: 'fire', title: 'Forest Fire', location: 'North Ridge Park', severity: 'high', points: 85, timestamp: '2024-10-26 10:30 AM', description: 'Large forest fire spreading rapidly. Multiple teams required.', trustScore: 95 },
    { id: 2, type: 'medical', title: 'Multi-Vehicle Accident', location: 'Highway 101, Mile 45', severity: 'high', points: 75, timestamp: '2024-10-26 10:45 AM', description: 'Multiple casualties reported. Emergency medical response needed.', trustScore: 90 },
    { id: 3, type: 'flood', title: 'Flash Flood Warning', location: 'Downtown Area', severity: 'medium', points: 65, timestamp: '2024-10-26 11:00 AM', description: 'Rising water levels in downtown area. Evacuation may be necessary.', trustScore: 85 },
    { id: 4, type: 'chemical', title: 'Chemical Spill', location: 'Industrial Sector 4', severity: 'medium', points: 70, timestamp: '2024-10-26 12:00 PM', description: 'Leak of hazardous materials reported. Nearby areas are at risk.', trustScore: 78 },
    { id: 5, type: 'storm', title: 'Severe Thunderstorm', location: 'Coastal Towns', severity: 'low', points: 55, timestamp: '2024-10-26 01:15 PM', description: 'Heavy rain and high winds expected. Be cautious of flooding.', trustScore: 70 },
  ]);

  const [newIncident, setNewIncident] = useState({
    type: 'fire',
    title: '',
    location: '',
    timestamp: '',
    description: '',
  });

  const typePoints = {
    fire: 20,
    medical: 15,
    flood: 18,
    chemical: 20,
    storm: 10,
  };

  const incidentIcons = {
    fire: '🔥',
    medical: '🚑',
    flood: '🌊',
    chemical: '☢️',
    storm: '🌩️',
  };

  const calculateSeverity = (incident) => {
    const { type, description } = incident;
    let score = typePoints[type] || 10;
    let trustScore = 50;

    const urgencyKeywords = ['urgent', 'hazard', 'critical', 'immediate', 'life-threatening', 'emergency'];
    const riskKeywords = ['evacuation', 'high risk', 'danger', 'severe', 'major incident', 'disaster', 'rescue needed'];

    urgencyKeywords.forEach((keyword) => {
      if (description.toLowerCase().includes(keyword)) score += 20;
    });

    riskKeywords.forEach((keyword) => {
      if (description.toLowerCase().includes(keyword)) score += 15;
    });

    if (description.toLowerCase().includes('confirmed') || description.toLowerCase().includes('verified')) {
      trustScore += 25;
    } else if (description.toLowerCase().includes('reported') || description.toLowerCase().includes('estimated')) {
      trustScore += 15;
    } else if (description.toLowerCase().includes('unconfirmed') || description.toLowerCase().includes('possible') || description.toLowerCase().includes('potential')) {
      trustScore -= 15;
    }

    return {
      points: score,
      severity: score > 90 ? 'high' : score > 65 ? 'medium' : 'low',
      trustScore,
    };
  };

  const addNewIncident = () => {
    const { points, severity, trustScore } = calculateSeverity(newIncident);
    const incidentWithId = {
      ...newIncident,
      id: incidents.length + 1,
      severity,
      points,
      trustScore,
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

  useEffect(() => {
    const cursor = document.createElement("div");
    cursor.id = "glow-cursor";
    document.body.appendChild(cursor);

    const moveCursor = (e) => {
      cursor.style.left = `${e.clientX}px`;
      cursor.style.top = `${e.clientY}px`;
    };

    window.addEventListener("mousemove", moveCursor);
    return () => {
      window.removeEventListener("mousemove", moveCursor);
      cursor.remove();
    };
  }, []);

  return (
    <Box id="root">
      {/* Header */}
      <Box id="header" display="flex" justifyContent="space-between" alignItems="center" width="100%">
        <Typography variant="h3" fontWeight="bold" className="logo">
          CrisisCompass
        </Typography>
        <Box className="menu">
          <Button color="inherit">Home</Button>
          <Button color="inherit">Incidents</Button>
          <Button color="inherit">Reports</Button>
          <Button color="inherit">Settings</Button>
        </Box>
      </Box>

      <Typography variant="h4" className="heading">
        Incident Report Dashboard
      </Typography>

      {/* Form for Adding New Incidents */}
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

      {/* Display Active Incidents */}
      <Box className="active-incidents">
        <Typography variant="h6" fontWeight="bold">Active Incidents</Typography>
        {incidents
          .sort((a, b) => b.points - a.points)
          .map((incident) => (
            <Card key={incident.id} className={`incident-card status-${incident.severity}`}>
              <CardContent>
                <Typography variant="body1" fontWeight="bold">
                  <span className="icon">{incidentIcons[incident.type]}</span> {incident.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">{incident.location}</Typography>
                <Typography variant="body2" color="text.secondary">{incident.description}</Typography>
                <Typography variant="caption" color="text.secondary">{incident.timestamp}</Typography>
                <Typography variant="caption" style={{ float: 'right', padding: '0.2rem 0.6rem', borderRadius: '8px', color: 'white', backgroundColor: incident.severity === 'high' ? '#e57373' : incident.severity === 'medium' ? '#ffb74d' : '#81c784' }}>
                  {incident.severity.toUpperCase()} - {incident.points} pts
                </Typography>
                <Typography variant="caption" color="text.secondary" style={{ display: 'block', marginTop: '8px' }}>Trust Score: {incident.trustScore}%</Typography>
              </CardContent>
            </Card>
          ))}
      </Box>
    </Box>
  );
};

export default CrisisCompass;
