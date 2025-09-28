"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import "./App.css"
import { Home, AlertTriangle, FileText, Settings, MapPin, RefreshCw } from "lucide-react"

function App() {
  const [location, setLocation] = useState(null)
  const [locationError, setLocationError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [incidents, setIncidents] = useState([])
  const [isLocationDetecting, setIsLocationDetecting] = useState(true)

  // Define emojis for incident types
  const incidentIcons = {
    fire: "🔥",
    medical: "🚑",
    flood: "🌊",
    chemical: "☢️",
    storm: "⛈️",
    general: "⚠️",
    default: "⚠️",
  }

  // Auto-detect location and fetch local incidents on component mount
  useEffect(() => {
    const detectLocationAndFetchIncidents = async () => {
      try {
        // Get user's location
        const position = await new Promise((resolve, reject) => {
          if (!navigator.geolocation) {
            reject(new Error('Geolocation is not supported by this browser'))
            return
          }
          
          navigator.geolocation.getCurrentPosition(
            resolve,
            reject,
            {
              enableHighAccuracy: true,
              timeout: 10000,
              maximumAge: 300000 // 5 minutes
            }
          )
        })

        const { latitude, longitude } = position.coords
        setLocation({ latitude, longitude })
        setIsLocationDetecting(false)

        // Fetch local incidents based on location
        await fetchLocalIncidents(latitude, longitude)
      } catch (err) {
        console.error("Error detecting location:", err)
        setLocationError("Unable to detect your location. Please enable location services.")
        setIsLocationDetecting(false)
        
        // Fallback: fetch general incidents
        await fetchIncidents()
      }
    }

    detectLocationAndFetchIncidents()
  }, [])

  // Fetch local incidents based on coordinates
  const fetchLocalIncidents = async (lat, lng) => {
    setLoading(true)
    try {
      const response = await axios.post("http://localhost:5000/get-local-incidents", {
        latitude: lat,
        longitude: lng
      })
      setIncidents(response.data)
    } catch (err) {
      console.error("Error fetching local incidents:", err)
      setError("Failed to load local incidents")
      // Fallback to general incidents
      await fetchIncidents()
    } finally {
      setLoading(false)
    }
  }

  // Fetch general incidents (fallback)
  const fetchIncidents = async () => {
    try {
      const response = await axios.get("http://localhost:5000/get-incidents")
      setIncidents(response.data)
    } catch (err) {
      console.error("Error fetching incidents:", err)
      setError("Failed to load incidents")
    }
  }

  // Refresh local incidents
  const refreshIncidents = async () => {
    if (location) {
      await fetchLocalIncidents(location.latitude, location.longitude)
    } else {
      await fetchIncidents()
    }
  }

  // Sort incidents by points (highest first)
  const sortedIncidents = [...incidents].sort((a, b) => b.points - a.points)

  return (
      <div className="app">
        {/* Header */}
        <header className="header">
          <div className="container header-container">
            <h1 className="logo">CrisisCompass</h1>

            <nav className="nav">
              <button className="nav-button">
                <Home className="icon" />
                Home
              </button>
              <button className="nav-button">
                <AlertTriangle className="icon" />
                Incidents
              </button>
              <button className="nav-button">
                <FileText className="icon" />
                Reports
              </button>
              <button className="nav-button">
                <Settings className="icon" />
                Settings
              </button>
            </nav>
          </div>
        </header>

        {/* Main content */}
        <main className="main container">
          {/* Location and Dashboard Header */}
          <div className="dashboard-header">
            <div className="location-info">
              {isLocationDetecting ? (
                <div className="location-detecting">
                  <RefreshCw className="icon spinning" />
                  <span>Detecting your location...</span>
                </div>
              ) : location ? (
                <div className="location-detected">
                  <MapPin className="icon" />
                  <span>Monitoring incidents near you</span>
                  <button onClick={refreshIncidents} className="refresh-button" disabled={loading}>
                    <RefreshCw className={`icon ${loading ? 'spinning' : ''}`} />
                    Refresh
                  </button>
                </div>
              ) : (
                <div className="location-error">
                  <MapPin className="icon" />
                  <span>{locationError || "Location not available"}</span>
                  <button onClick={refreshIncidents} className="refresh-button" disabled={loading}>
                    <RefreshCw className={`icon ${loading ? 'spinning' : ''}`} />
                    Load General Incidents
                  </button>
                </div>
              )}
            </div>
            {error && <p className="error-message">{error}</p>}
          </div>

          {/* Incident listings */}
          <div className="incidents-container">
            <h2 className="incidents-title">
              {location ? "Local Incidents" : "Recent Incidents"} {loading && <span className="loading-indicator">Loading...</span>}
            </h2>

            {incidents.length === 0 && !loading ? (
                <div className="no-incidents">
                  <p>{location ? "No local incidents found. The area appears to be safe." : "No incidents found. Monitoring for new reports..."}</p>
                </div>
            ) : (
                <div className="incidents-list">
                  {sortedIncidents.map((incident) => {
                    const iconType = (incident.type || "general").toLowerCase()
                    const severityClass = `incident-card severity-${incident.severity}`

                    return (
                        <div key={incident.id} className={severityClass}>
                          <div className="incident-content">
                            <div className="incident-info">
                              <div className="incident-header">
                                <span className="incident-icon">{incidentIcons[iconType] || incidentIcons.default}</span>
                                <h3 className="incident-title">{incident.title}</h3>
                              </div>
                              <p className="incident-location">PLACE: {incident.location.toUpperCase()}</p>
                              <p className="incident-description">{incident.description}</p>
                              <p className="incident-timestamp">{incident.timestamp}</p>
                            </div>

                            <div className="incident-metrics">
                        <span className={`incident-severity severity-badge-${incident.severity}`}>
                          {incident.severity.toUpperCase()} - {incident.points} pts
                        </span>
                              <p className="incident-trust">Trust Score: {incident.trustScore}%</p>
                            </div>
                          </div>
                        </div>
                    )
                  })}
                </div>
            )}
          </div>
        </main>
      </div>
  )
}

export default App

