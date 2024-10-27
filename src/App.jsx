// CrisisCompass.jsx

import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, TextField, MenuItem } from '@mui/material';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import axios from 'axios'; // Import axios for HTTP requests
import './App.css';

const CrisisCompass = () => {
  const [incidents, setIncidents] = useState([]);
  const [newIncident, setNewIncident] = useState({
    type: 'fire',
    title: '',
    location: '',
    timestamp: '',
    description: '',
  });
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

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
    general: '⚠️',
  };

  // Fetch existing incidents from the backend when the component mounts
  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const response = await axios.get('http://localhost:5000/get-incidents');
        setIncidents(response.data);
      } catch (err) {
        console.error('Error fetching incidents:', err);
      }
    };

    fetchIncidents();
  }, []);

  const scrapeUrl = async () => {
    if (!url) {
      setError("Please enter a URL");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const response = await axios.post('http://localhost:5000/scrape', { url });

      if (response.data.error) {
        throw new Error(response.data.error);
      }

      const incidentData = response.data;

      setIncidents(prev => [...prev, incidentData]);
      setUrl('');
    } catch (err) {
      console.error('Error scraping URL:', err);
      setError(err.response?.data?.error || 'Failed to scrape URL');
    } finally {
      setLoading(false);
    }
  };

  const addNewIncident = () => {
    if (!newIncident.title || !newIncident.location || !newIncident.timestamp || !newIncident.description) {
      setError("All fields are required.");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      // Since there's no backend endpoint for adding incidents manually, we add it locally
      const { points, severity, trustScore } = calculateSeverity(newIncident);
      const incidentWithId = {
        ...newIncident,
        id: incidents.length + 1,
        severity,
        points,
        trustScore,
      };
      setIncidents(prev => [...prev, incidentWithId]);
      setNewIncident({
        type: 'fire',
        title: '',
        location: '',
        timestamp: '',
        description: '',
      });
    } catch (err) {
      console.error('Error adding incident:', err);
      setError("Failed to add incident. Please try again.");
    } finally {
      setLoading(false);
    }
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
    <Box id="root" className="p-8">
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

      <Typography variant="h4" className="heading" mt={4}>
        Incident Report Dashboard
      </Typography>

      {/* URL Scraping Section */}
      <Box className="card" mt={4} p={4} bgcolor="white" borderRadius="8px" boxShadow={3}>
        <Typography variant="h6" fontWeight="bold" mb={2}>Scrape Incident from URL</Typography>
        <Box display="flex" gap={2} mb={2}>
          <TextField
            type="url"
            label="Enter URL to scrape"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            fullWidth
          />
          <Button 
            variant="contained" 
            color="primary" 
            onClick={scrapeUrl} 
            disabled={loading}
          >
            {loading ? 'Scraping...' : 'Scrape'}
          </Button>
        </Box>
        {error && (
          <Typography color="error" variant="body2">
            {error}
          </Typography>
        )}
      </Box>

      {/* Form for Adding New Incidents */}
      <Box className="card" mt={4} p={4} bgcolor="white" borderRadius="8px" boxShadow={3}>
        <Typography variant="h6" fontWeight="bold" mb={2}>Report a New Incident</Typography>
        <TextField 
          label="Title" 
          name="title" 
          value={newIncident.title} 
          onChange={handleInputChange} 
          fullWidth 
          margin="normal" 
        />
        <TextField 
          label="Location" 
          name="location" 
          value={newIncident.location} 
          onChange={handleInputChange} 
          fullWidth 
          margin="normal" 
        />
        <TextField 
          label="Timestamp" 
          name="timestamp" 
          value={newIncident.timestamp} 
          onChange={handleInputChange} 
          fullWidth 
          margin="normal" 
          placeholder="YYYY-MM-DD HH:MM AM/PM" 
        />
        <TextField 
          label="Description" 
          name="description" 
          value={newIncident.description} 
          onChange={handleInputChange} 
          fullWidth 
          margin="normal" 
          multiline 
          rows={3} 
        />
        <TextField 
          label="Type" 
          name="type" 
          value={newIncident.type} 
          onChange={handleInputChange} 
          select 
          fullWidth 
          margin="normal"
        >
          <MenuItem value="fire">Fire</MenuItem>
          <MenuItem value="medical">Medical</MenuItem>
          <MenuItem value="flood">Flood</MenuItem>
          <MenuItem value="chemical">Chemical</MenuItem>
          <MenuItem value="storm">Storm</MenuItem>
        </TextField>
        <Button 
          variant="contained" 
          color="secondary" 
          onClick={addNewIncident}
          disabled={loading}
        >
          {loading ? 'Adding...' : 'Submit Incident'}
        </Button>
        {error && (
          <Typography color="error" variant="body2" mt={2}>
            {error}
          </Typography>
        )}
      </Box>

      {/* Display Active Incidents */}
      <Box className="active-incidents" mt={4}>
        <Typography variant="h6" fontWeight="bold" mb={2}>Active Incidents</Typography>
        {incidents
          .sort((a, b) => b.points - a.points) // Sort by points descending
          .map((incident) => (
            <Card key={incident.id} className={`incident-card status-${incident.severity}`} sx={{ mb: 2 }}>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                  <Box>
                    <Typography variant="body1" fontWeight="bold">
                      <span className="icon" style={{ marginRight: '8px' }}>{incidentIcons[incident.type]}</span> {incident.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">{incident.location}</Typography>
                    <Typography variant="body2" color="text.secondary" mt={1}>{incident.description}</Typography>
                    <Typography variant="caption" color="text.secondary" mt={1}>{incident.timestamp}</Typography>
                    {incident.keywords && incident.keywords.length > 0 && (
                      <Box mt={1} display="flex" gap={1} flexWrap="wrap">
                        {incident.keywords.map((keyword, index) => (
                          <Typography key={index} variant="caption" component="span" className="keyword-badge">
                            {keyword}
                          </Typography>
                        ))}
                      </Box>
                    )}
                  </Box>
                  <Box textAlign="right">
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        px: 2, 
                        py: 0.5, 
                        borderRadius: '8px', 
                        color: 'white', 
                        backgroundColor: 
                          incident.severity === 'high' ? '#e57373' : 
                          incident.severity === 'medium' ? '#ffb74d' : 
                          '#81c784' 
                      }}
                    >
                      {incident.severity.toUpperCase()} - {incident.points} pts
                    </Typography>
                    <Typography variant="caption" color="text.secondary" mt={1} display="block">
                      Trust Score: {incident.trustScore}%
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          ))}
      </Box>
    </Box>
  );
};

export default CrisisCompass;
