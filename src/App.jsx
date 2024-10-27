import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, TextField } from '@mui/material';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import axios from 'axios';
import './App.css';

const CrisisCompass = () => {
  const [incidents, setIncidents] = useState([]);
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showLabel, setShowLabel] = useState(true);

  const incidentIcons = {
    fire: '🔥',
    medical: '🚑',
    flood: '🌊',
    chemical: '☢️',
    storm: '🌩️',
    general: '⚠️',
  };

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

  return (
    <Box id="root" sx={{ backgroundColor: "#ffffff", color: "#333333", minHeight: "100vh", padding: "2rem" }}>
      {/* Black Top Bar */}
      <Box
        id="header"
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        width="100%"
        mb={4}
        sx={{
          backgroundColor: "black",
          padding: "1rem",
          borderRadius: "8px"
        }}
      >
        <Typography variant="h3" fontWeight="bold" sx={{ color: "#ffffff" }}>
          CrisisCompass
        </Typography>
        
        {/* Thinner, Rounder, Centered Search Bar */}
        <TextField
          type="url"
          label={showLabel ? "Enter Incident URL or Search" : ""}
          variant="outlined"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onFocus={() => setShowLabel(false)}
          onBlur={() => setShowLabel(true)}
          sx={{
            backgroundColor: "#f0f0f0",
            borderRadius: "16px",
            width: "25%",
            height: "50px",
            marginRight: "16px",
            boxShadow: "none",
            '.MuiOutlinedInput-root': {
              '& fieldset': {
                border: 'none',
              },
            },
          }}
          InputProps={{
            style: {
              padding: "0px 0px",
              fontSize: "0.875rem",
              lineHeight: "1.5",
            },
          }}
        />

        <Button
          variant="contained"
          color="primary"
          onClick={scrapeUrl}
          disabled={loading}
          sx={{ backgroundColor: "#4A90E2", borderRadius: "8px", height: "36px", fontSize: "0.875rem" }}
        >
          {loading ? 'Loading...' : 'Rank'}
        </Button>

        {/* Navbar Buttons without Sub-options */}
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button color="inherit" sx={{ color: "#ffffff" }}>Home</Button>
          <Button color="inherit" sx={{ color: "#ffffff" }}>Incidents</Button>
          <Button color="inherit" sx={{ color: "#ffffff" }}>Reports</Button>
          <Button color="inherit" sx={{ color: "#ffffff" }}>Settings</Button>
        </Box>
      </Box>

      {/* Display Active Incidents */}
      <Box className="active-incidents" mt={4}>
        <Typography variant="h4" fontWeight="bold" mb={2} sx={{ color: "#ffffff" }}>Active Incidents</Typography>
        {incidents
          .sort((a, b) => b.points - a.points)
          .map((incident) => (
            <Card key={incident.id} className={`incident-card status-${incident.severity}`} sx={{ mb: 2, backgroundColor: "#f9f9f9", borderRadius: "8px" }}>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                  <Box>
                    {/* Remove extra space around title */}
                    <Typography variant="body1" fontWeight="bold" sx={{ margin: 0, padding: 0, display: 'flex', alignItems: 'center' }}> 
                      <span style={{ marginRight: '8px' }}>{incidentIcons[incident.type]}</span>{incident.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" fontWeight={"bold"}> 
                        {"Place: " + incident.location.toUpperCase()}</Typography>
                    <Typography variant="body2" color="text.secondary" mt={1}>{incident.description}</Typography>
                    <Typography variant="caption" color="text.secondary" mt={1}>{incident.timestamp}</Typography>
                  </Box>
                  <Box textAlign="right">
                    {/* Fixed Badge Layout */}
                    <Typography
                      variant="caption"
                      sx={{
                        display: 'inline-block',
                        px: 2,
                        py: 0.5,
                        borderRadius: '8px',
                        color: 'white',
                        backgroundColor:
                          incident.severity === 'high' ? '#e57373' :
                          incident.severity === 'medium' ? '#ffb74d' :
                          '#81c784',
                        whiteSpace: 'nowrap',
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
