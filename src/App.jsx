"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import "./App.css"
import { Home, AlertTriangle, FileText, Settings } from "lucide-react"

function App() {
  const [url, setUrl] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [incidents, setIncidents] = useState([])

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

  // Fetch initial incidents on component mount
  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const response = await axios.get("http://localhost:5000/get-incidents")
        setIncidents(response.data)
      } catch (err) {
        console.error("Error fetching incidents:", err)
        setError("Failed to load incidents")
      }
    }

    fetchIncidents()
  }, [])

  // Handle URL scraping
  const scrapeUrl = async () => {
    if (!url) {
      setError("Please enter a URL")
      return
    }
    setError(null)
    setLoading(true)
    try {
      const response = await axios.post("http://localhost:5000/scrape", { url })
      if (response.data.error) {
        throw new Error(response.data.error)
      }
      const incidentData = response.data
      setIncidents((prev) => [...prev, incidentData])
      setUrl("")
    } catch (err) {
      console.error("Error scraping URL:", err)
      setError(err.response?.data?.error || "Failed to scrape URL")
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    scrapeUrl()
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
          {/* Centered URL input box */}
          <div className="input-container">
            <div className="input-card">
              <h2 className="input-title">Crisis Incident Ranking</h2>
              <form onSubmit={handleSubmit} className="input-form">
                <div className="input-wrapper">
                  <input
                      type="url"
                      placeholder="Enter incident URL to analyze"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      className="url-input"
                  />
                  <button type="submit" className="submit-button" disabled={loading}>
                    {loading ? "..." : "→"}
                  </button>
                </div>
                {error && <p className="error-message">{error}</p>}
                <p className="helper-text">Enter a URL to an incident report to analyze and rank its severity</p>
              </form>
            </div>
          </div>

          {/* Incident listings */}
          <div className="incidents-container">
            <h2 className="incidents-title">
              Active Incidents {loading && <span className="loading-indicator">Loading...</span>}
            </h2>

            {incidents.length === 0 && !loading ? (
                <div className="no-incidents">
                  <p>No incidents found. Enter a URL above to analyze an incident.</p>
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

