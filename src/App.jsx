import { useState, useEffect, useCallback, useMemo, useRef } from "react"
import { api } from "./api"
import { ReportsPanel } from "./components/ReportsPanel"
import { SettingsPanel } from "./components/SettingsPanel"
import {
  loadSettings,
  saveSettings,
  inQuietHours,
  severityMeetsFloor,
} from "./settingsStorage"
import "./App.css"
import {
  Home,
  AlertTriangle,
  FileText,
  Settings,
  MapPin,
  RefreshCw,
  Shield,
  AlertCircle,
  ExternalLink,
  Menu,
  X,
  Compass,
  Info,
  Lock,
} from "lucide-react"

const SORT_OPTIONS = [
  { id: "points", label: "Points" },
  { id: "severity", label: "Severity" },
  { id: "trust", label: "Trust" },
  { id: "time", label: "Newest" },
]

const SEVERITY_OPTIONS = [
  { id: "high", label: "High" },
  { id: "medium", label: "Medium" },
  { id: "low", label: "Low" },
]

function parseIncidentTime(ts) {
  if (ts == null || ts === "") return 0
  const s = String(ts).trim()
  const parsed = Date.parse(s)
  if (!Number.isNaN(parsed)) return parsed
  const iso = s.match(/^(\d{4})-(\d{2})-(\d{2})/)
  if (iso) {
    const t = new Date(Number(iso[1]), Number(iso[2]) - 1, Number(iso[3])).getTime()
    return Number.isNaN(t) ? 0 : t
  }
  return 0
}

function severityA11yLabel(severity) {
  const s = (severity || "low").toLowerCase()
  if (s === "high") return "High severity"
  if (s === "medium") return "Medium severity"
  return "Low severity"
}

// eslint-disable-next-line react/prop-types
function SeverityIcon({ severity }) {
  const s = (severity || "low").toLowerCase()
  const label = severityA11yLabel(severity)
  if (s === "high") {
    return <AlertTriangle className="severity-icon" aria-hidden="true" title={label} />
  }
  if (s === "medium") {
    return <AlertCircle className="severity-icon" aria-hidden="true" title={label} />
  }
  return <Shield className="severity-icon" aria-hidden="true" title={label} />
}

function App() {
  const [navView, setNavView] = useState("incidents")
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [location, setLocation] = useState(null)
  const [locationError, setLocationError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [incidents, setIncidents] = useState([])
  const [isLocationDetecting, setIsLocationDetecting] = useState(true)
  const [scrapeHint, setScrapeHint] = useState("")
  const [sortBy, setSortBy] = useState("points")
  const [severityFilters, setSeverityFilters] = useState([])
  const [typeFilters, setTypeFilters] = useState([])
  const [lastUpdated, setLastUpdated] = useState(null)
  const [settings, setSettings] = useState(() => loadSettings())

  useEffect(() => {
    saveSettings(settings)
  }, [settings])

  useEffect(() => {
    document.documentElement.style.fontSize = `${settings.fontScale}%`
  }, [settings.fontScale])

  useEffect(() => {
    if (settings.reducedMotion) document.documentElement.classList.add("reduce-motion")
    else document.documentElement.classList.remove("reduce-motion")
  }, [settings.reducedMotion])

  const goTo = useCallback((view) => {
    setNavView(view)
    setMobileNavOpen(false)
  }, [])

  useEffect(() => {
    if (!mobileNavOpen) return
    const onKey = (e) => {
      if (e.key === "Escape") setMobileNavOpen(false)
    }
    window.addEventListener("keydown", onKey)
    const prev = document.body.style.overflow
    document.body.style.overflow = "hidden"
    return () => {
      window.removeEventListener("keydown", onKey)
      document.body.style.overflow = prev
    }
  }, [mobileNavOpen])

  const incidentIcons = {
    fire: "🔥",
    medical: "🚑",
    flood: "🌊",
    chemical: "☢️",
    storm: "⛈️",
    general: "⚠️",
    default: "⚠️",
  }

  const fetchIncidents = useCallback(async () => {
    try {
      const response = await api.get("/get-incidents")
      setIncidents(response.data)
      setError(null)
      setLastUpdated(new Date())
    } catch (err) {
      console.error("Error fetching incidents:", err)
      setError("Failed to load incidents")
    }
  }, [])

  const fetchLocalIncidents = useCallback(
    async (lat, lng) => {
      setLoading(true)
      setScrapeHint("")
      try {
        const response = await api.post("/get-local-incidents", {
          latitude: lat,
          longitude: lng,
        })
        const rows = response.data
        setIncidents(Array.isArray(rows) ? rows : [])
        setError(null)
        setLastUpdated(new Date())

        if (Array.isArray(rows) && rows.length === 0) {
          try {
            const dbg = await api.get("/debug/logs")
            setScrapeHint(dbg.data?.last_scrape?.hint || "")
          } catch {
            setScrapeHint("")
          }
        } else {
          setScrapeHint("")
        }
      } catch (err) {
        console.error("Error fetching local incidents:", err)
        setError("Failed to load local incidents")
        setScrapeHint("")
        try {
          await fetchIncidents()
          setError(null)
        } catch {
          /* fetchIncidents already set error */
        }
      } finally {
        setLoading(false)
      }
    },
    [fetchIncidents]
  )

  const runGeolocationFlow = useCallback(
    async (forceFresh = false) => {
      if (!navigator.geolocation) {
        setLocationError("This browser does not support geolocation.")
        setIsLocationDetecting(false)
        setLocation(null)
        await fetchIncidents()
        return
      }
      setIsLocationDetecting(true)
      setLocationError(null)
      try {
        const position = await new Promise((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: true,
            timeout: forceFresh ? 120000 : 90000,
            maximumAge: forceFresh ? 0 : 300000,
          })
        })
        const { latitude, longitude } = position.coords
        setLocation({ latitude, longitude })
        setLocationError(null)
        await fetchLocalIncidents(latitude, longitude)
      } catch (err) {
        console.error("Error detecting location:", err)
        setLocation(null)
        setLocationError(
          "Location not available yet. Allow location for this site (address bar lock icon), then tap “Try location again”—no full page reload needed—or use the general feed."
        )
        await fetchIncidents()
      } finally {
        setIsLocationDetecting(false)
      }
    },
    [fetchLocalIncidents, fetchIncidents]
  )

  const runGeolocationFlowRef = useRef(runGeolocationFlow)
  useEffect(() => {
    runGeolocationFlowRef.current = runGeolocationFlow
  }, [runGeolocationFlow])

  useEffect(() => {
    runGeolocationFlow(false)
  }, [runGeolocationFlow])

  useEffect(() => {
    if (!navigator.permissions?.query) return undefined
    let perm = null
    let handler = null
    const p = navigator.permissions.query({ name: "geolocation" })
    p.then((permissionStatus) => {
      perm = permissionStatus
      handler = () => {
        if (permissionStatus.state === "granted") {
          runGeolocationFlowRef.current(true)
        }
      }
      permissionStatus.addEventListener("change", handler)
    }).catch(() => {
      /* Safari / older browsers */
    })
    return () => {
      if (perm && handler) perm.removeEventListener("change", handler)
    }
  }, [])

  const refreshIncidents = async () => {
    if (location) {
      await fetchLocalIncidents(location.latitude, location.longitude)
    } else {
      setLoading(true)
      try {
        await fetchIncidents()
      } finally {
        setLoading(false)
      }
    }
  }

  const switchToGeneralFeed = async () => {
    setLocation(null)
    setLocationError(null)
    setLoading(true)
    try {
      await fetchIncidents()
    } finally {
      setLoading(false)
    }
  }

  const typesInData = useMemo(() => {
    const s = new Set()
    incidents.forEach((i) => s.add((i.type || "general").toLowerCase()))
    return [...s].sort()
  }, [incidents])

  const filteredSorted = useMemo(() => {
    let rows = [...incidents]
    rows = rows.filter((i) => {
      const sev = (i.severity || "low").toLowerCase()
      if (severityFilters.length && !severityFilters.includes(sev)) return false
      const ty = (i.type || "general").toLowerCase()
      if (typeFilters.length && !typeFilters.includes(ty)) return false
      if (!severityMeetsFloor(i.severity, settings.severityFloor)) return false
      return true
    })
    const sevOrder = { high: 3, medium: 2, low: 1 }
    rows.sort((a, b) => {
      if (sortBy === "points") return (b.points || 0) - (a.points || 0)
      if (sortBy === "trust") return (b.trustScore || 0) - (a.trustScore || 0)
      const sb = sevOrder[(b.severity || "low").toLowerCase()] || 0
      const sa = sevOrder[(a.severity || "low").toLowerCase()] || 0
      if (sortBy === "severity") {
        if (sb !== sa) return sb - sa
        return (b.points || 0) - (a.points || 0)
      }
      if (sortBy === "time") {
        const tb = parseIncidentTime(b.timestamp)
        const ta = parseIncidentTime(a.timestamp)
        if (tb !== ta) return tb - ta
        return (b.points || 0) - (a.points || 0)
      }
      return 0
    })
    return rows
  }, [incidents, severityFilters, typeFilters, sortBy, settings.severityFloor])

  const clearFilters = () => {
    setSeverityFilters([])
    setTypeFilters([])
  }

  const toggleSeverity = (id) => {
    setSeverityFilters((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  const toggleType = (id) => {
    setTypeFilters((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  const incidentsPanel = (
    <>
      <div className="dashboard-header">
        <div className="location-info">
          {isLocationDetecting ? (
            <div className="location-detecting">
              <RefreshCw className="icon spinning" aria-hidden="true" />
              <span>Detecting your location...</span>
            </div>
          ) : location ? (
            <div className="location-detected">
              <MapPin className="icon" aria-hidden="true" />
              <span>Monitoring incidents near you</span>
              <button
                type="button"
                onClick={refreshIncidents}
                className="refresh-button"
                disabled={loading}
              >
                <RefreshCw className={`icon ${loading ? "spinning" : ""}`} aria-hidden="true" />
                Refresh
              </button>
            </div>
          ) : (
            <div className="location-error">
              <MapPin className="icon" aria-hidden="true" />
              <span>{locationError || "Location not available"}</span>
              <div className="location-error-actions">
                <button
                  type="button"
                  onClick={() => runGeolocationFlow(true)}
                  className="refresh-button"
                  disabled={loading || isLocationDetecting}
                >
                  <RefreshCw className={`icon ${isLocationDetecting ? "spinning" : ""}`} aria-hidden="true" />
                  Try location again
                </button>
                <button
                  type="button"
                  onClick={() => refreshIncidents()}
                  className="refresh-button refresh-button-secondary"
                  disabled={loading}
                >
                  Load general incidents
                </button>
              </div>
            </div>
          )}
        </div>
        {lastUpdated && (
          <p className="last-updated" role="status">
            Last updated{" "}
            <time dateTime={lastUpdated.toISOString()}>{lastUpdated.toLocaleString()}</time>
          </p>
        )}
        {settings.channelInApp &&
          inQuietHours(new Date(), settings.quietStart, settings.quietEnd) && (
          <div className="quiet-hours-banner" role="status">
            <p>
              Quiet hours ({settings.quietStart}–{settings.quietEnd}): in-app notices are muted; check the
              board for updates.
            </p>
          </div>
        )}
        {error && (
          <div className="error-banner" role="alert">
            <p className="error-banner-text">{error}</p>
            <div className="error-banner-actions">
              <button type="button" className="refresh-button" onClick={() => refreshIncidents()} disabled={loading}>
                <RefreshCw className={`icon ${loading ? "spinning" : ""}`} aria-hidden="true" />
                Retry
              </button>
              {location != null && (
                <button
                  type="button"
                  className="refresh-button refresh-button-secondary"
                  onClick={() => switchToGeneralFeed()}
                  disabled={loading}
                >
                  Use general feed
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="incidents-container">
        <div className="incidents-head">
          <h2 className="incidents-title">
            {location ? "Local incidents" : "Recent incidents"}
            {loading && <span className="loading-indicator">Loading…</span>}
          </h2>
          {incidents.length > 0 && !loading && (
            <p className="incidents-count" role="status">
              Showing {filteredSorted.length} of {incidents.length}
            </p>
          )}
        </div>

        {incidents.length > 0 && (
          <div className="incidents-toolbar" role="region" aria-label="Filter and sort">
            <div className="toolbar-section">
              <span className="toolbar-label" id="sort-label">
                Sort
              </span>
              <div className="toolbar-pills" role="group" aria-labelledby="sort-label">
                {SORT_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    className={`toolbar-pill${sortBy === opt.id ? " toolbar-pill-active" : ""}`}
                    onClick={() => setSortBy(opt.id)}
                    aria-pressed={sortBy === opt.id}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
            <div className="toolbar-section">
              <span className="toolbar-label" id="severity-filter-label">
                Severity
              </span>
              <div className="toolbar-pills" role="group" aria-labelledby="severity-filter-label">
                {SEVERITY_OPTIONS.map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    className={`toolbar-pill toolbar-pill-filter${severityFilters.includes(opt.id) ? " toolbar-pill-active" : ""}`}
                    onClick={() => toggleSeverity(opt.id)}
                    aria-pressed={severityFilters.includes(opt.id)}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
            {typesInData.length > 0 && (
              <div className="toolbar-section toolbar-section-wrap">
                <span className="toolbar-label" id="type-filter-label">
                  Type
                </span>
                <div className="toolbar-pills" role="group" aria-labelledby="type-filter-label">
                  {typesInData.map((tid) => (
                    <button
                      key={tid}
                      type="button"
                      className={`toolbar-pill toolbar-pill-filter${typeFilters.includes(tid) ? " toolbar-pill-active" : ""}`}
                      onClick={() => toggleType(tid)}
                      aria-pressed={typeFilters.includes(tid)}
                    >
                      {tid}
                    </button>
                  ))}
                </div>
              </div>
            )}
            {(severityFilters.length > 0 || typeFilters.length > 0) && (
              <button type="button" className="ghost-button" onClick={clearFilters}>
                Clear filters
              </button>
            )}
          </div>
        )}

        {incidents.length === 0 && !loading ? (
          <div className="no-incidents">
            <p>
              {location
                ? "No local incidents found from live feeds. The area may be quiet, or feeds may have failed or filtered everything out."
                : "No incidents found. Monitoring for new reports..."}
            </p>
            {location && scrapeHint && (
              <p className="no-incidents-hint" role="status">
                <strong>Why empty:</strong> {scrapeHint}
              </p>
            )}
            {location && (
              <p className="no-incidents-dev">
                For <strong>demo placeholder cards</strong> when feeds are empty, set environment variable{" "}
                <code className="sample-code">CRISIS_COMPASS_DEV_SAMPLES=1</code> on the API process and
                restart <code className="sample-code">npm run dev</code>.
              </p>
            )}
            {!location && locationError && (
              <div className="no-incidents-actions">
                <p className="no-incidents-hint">
                  Location is optional. You can still follow the general incident list, or allow location for
                  regional feeds.
                </p>
                <button type="button" className="primary-link-button" onClick={() => refreshIncidents()} disabled={loading}>
                  Refresh list
                </button>
              </div>
            )}
          </div>
        ) : filteredSorted.length === 0 && !loading ? (
          <div className="no-incidents no-incidents-filtered">
            <p>No incidents match your filters.</p>
            <button type="button" className="ghost-button ghost-button-prominent" onClick={clearFilters}>
              Clear filters
            </button>
          </div>
        ) : (
          <div className="incidents-list">
            {filteredSorted.map((incident, index) => {
              const iconType = (incident.type || "general").toLowerCase()
              const severityClass = `incident-card severity-${incident.severity}`
              const sevLabel = severityA11yLabel(incident.severity)
              const rawUrl = (incident.url || "").trim()
              const safeUrl =
                rawUrl && (rawUrl.startsWith("http://") || rawUrl.startsWith("https://"))
                  ? rawUrl
                  : null
              const sourceName = incident.source || "Unknown source"
              const delay = Math.min(index * 0.05, 0.45)

              return (
                <article
                  key={`${incident.id}-${incident.title}`}
                  className={severityClass}
                  aria-label={`${sevLabel}: ${incident.title}`}
                  style={{ animationDelay: `${delay}s` }}
                >
                  {incident.is_sample && (
                    <div className="sample-banner" role="status">
                      Dev / sample row — not from live RSS. Enable server-side samples with{" "}
                      <code className="sample-code">CRISIS_COMPASS_DEV_SAMPLES=1</code> when feeds are
                      empty.
                    </div>
                  )}
                  <div className="incident-content">
                    <div className="incident-info">
                      <div className="incident-header">
                        <span className="incident-icon" aria-hidden="true">
                          {incidentIcons[iconType] || incidentIcons.default}
                        </span>
                        <h3 className="incident-title">{incident.title}</h3>
                      </div>
                      <p className="incident-source">
                        <span className="source-label">Source:</span>{" "}
                        {safeUrl ? (
                          <a
                            href={safeUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="source-link"
                          >
                            {sourceName}
                            <ExternalLink className="source-link-icon" aria-hidden="true" />
                          </a>
                        ) : (
                          <span>{sourceName}</span>
                        )}
                      </p>
                      <p className="incident-location">Place: {incident.location}</p>
                      <p className="incident-description">{incident.description}</p>
                      <p className="incident-timestamp">{incident.timestamp}</p>
                    </div>

                    <div className="incident-metrics">
                      <span className={`incident-severity severity-badge-${incident.severity}`}>
                        <SeverityIcon severity={incident.severity} />
                        <span className="severity-text">
                          {(incident.severity || "low").toUpperCase()} — {incident.points} pts
                        </span>
                      </span>
                      <p className="incident-trust">Trust score: {incident.trustScore}%</p>
                    </div>
                  </div>
                </article>
              )
            })}
          </div>
        )}
      </div>
    </>
  )

  const navButtons = () => (
    <>
      <button
        type="button"
        className={`nav-button${navView === "home" ? " nav-button-active" : ""}`}
        onClick={() => goTo("home")}
      >
        <Home className="icon" aria-hidden="true" />
        Home
      </button>
      <button
        type="button"
        className={`nav-button${navView === "incidents" ? " nav-button-active" : ""}`}
        onClick={() => goTo("incidents")}
      >
        <AlertTriangle className="icon" aria-hidden="true" />
        Incidents
      </button>
      <button
        type="button"
        className={`nav-button${navView === "reports" ? " nav-button-active" : ""}`}
        onClick={() => goTo("reports")}
      >
        <FileText className="icon" aria-hidden="true" />
        Reports
      </button>
      <button
        type="button"
        className={`nav-button${navView === "settings" ? " nav-button-active" : ""}`}
        onClick={() => goTo("settings")}
      >
        <Settings className="icon" aria-hidden="true" />
        Settings
      </button>
    </>
  )

  return (
    <div className="app">
      <a href="#main-content" className="skip-link">
        Skip to content
      </a>

      <header className="header">
        <div className="container header-container">
          <h1 className="logo">
            <span className="logo-wrap">
              <span className="logo-mark" aria-hidden="true">
                <Compass className="logo-mark-icon" />
              </span>
              CrisisCompass
            </span>
          </h1>

          <nav className="nav" aria-label="Main navigation">
            {navButtons()}
          </nav>

          <button
            type="button"
            className="nav-toggle"
            aria-expanded={mobileNavOpen}
            aria-controls="mobile-nav-drawer"
            aria-label={mobileNavOpen ? "Close menu" : "Open menu"}
            onClick={() => setMobileNavOpen((o) => !o)}
          >
            {mobileNavOpen ? <X className="icon" aria-hidden="true" /> : <Menu className="icon" aria-hidden="true" />}
          </button>
        </div>
      </header>

      <div
        className={`mobile-nav-backdrop${mobileNavOpen ? " is-open" : ""}`}
        aria-hidden="true"
        onClick={() => setMobileNavOpen(false)}
      />

      <nav
        id="mobile-nav-drawer"
        className={`mobile-nav${mobileNavOpen ? " is-open" : ""}`}
        aria-label="Mobile navigation"
        aria-hidden={!mobileNavOpen}
      >
        {navButtons()}
      </nav>

      <main id="main-content" className="main container" tabIndex={-1}>
        {navView === "home" && (
          <section className="hero" aria-labelledby="home-heading">
            <p className="hero-eyebrow">Regional awareness</p>
            <h2 id="home-heading" className="hero-title">
              See what matters near you—ranked and sourced.
            </h2>
            <p className="hero-lead">
              CrisisCompass pulls nearby news feeds and scores items for severity on the{" "}
              <strong>server</strong>. Coordinates are used only to pick regional feeds; open{" "}
              <strong>Incidents</strong> for the live board.
            </p>
            <div className="hero-actions">
              <button type="button" className="primary-link-button" onClick={() => goTo("incidents")}>
                Open incident board
              </button>
            </div>
            <div className="hero-chips" role="list">
              <span className="hero-chip" role="listitem">
                Server-side ranking
              </span>
              <span className="hero-chip" role="listitem">
                Source-linked items
              </span>
              <span className="hero-chip" role="listitem">
                Location-aware feeds
              </span>
            </div>
            <p className="hero-footnote">
              <button type="button" className="inline-text-button" onClick={() => goTo("privacy")}>
                Privacy
              </button>
              {" · "}
              <button type="button" className="inline-text-button" onClick={() => goTo("about")}>
                About
              </button>
            </p>
          </section>
        )}

        {navView === "incidents" && incidentsPanel}

        {navView === "reports" && (
          <ReportsPanel
            includeLlm={settings.includeLlm}
            llmTone={settings.llmTone}
            llmLength={settings.llmLength}
          />
        )}

        {navView === "settings" && (
          <SettingsPanel settings={settings} onChange={setSettings} />
        )}

        {navView === "about" && (
          <section className="static-panel static-panel-wide" aria-labelledby="about-heading">
            <div className="static-panel-icon" aria-hidden="true">
              <Info className="static-panel-icon-svg" />
            </div>
            <h2 id="about-heading" className="static-panel-title">
              About CrisisCompass
            </h2>
            <p className="static-panel-text">
              CrisisCompass aggregates public news-style signals and ranks them with keyword and NLP heuristics
              on the server. It is a <strong>decision-support and awareness</strong> tool, not an official
              emergency channel. Always follow instructions from local authorities, 911, and verified civil
              alerts.
            </p>
            <p className="static-panel-text">
              Feeds and scrapers can fail, lag, or omit events. Trust scores and severity points are automated
              estimates—not human verification of every story.
            </p>
          </section>
        )}

        {navView === "privacy" && (
          <section className="static-panel static-panel-wide" aria-labelledby="privacy-heading">
            <div className="static-panel-icon" aria-hidden="true">
              <Lock className="static-panel-icon-svg" />
            </div>
            <h2 id="privacy-heading" className="static-panel-title">
              Privacy
            </h2>
            <p className="static-panel-text">
              When you allow browser location, <strong>latitude and longitude</strong> are sent to the
              CrisisCompass API to resolve a general area (e.g. city or region) and request relevant RSS and
              web sources. Coordinates are used for that request flow; we do not use them for advertising in
              this open-source demo.
            </p>
            <p className="static-panel-text">
              Incident titles, descriptions, and links come from <strong>third-party publishers</strong>.
              Opening a source link leaves this site and is subject to that publisher&apos;s policies.
            </p>
            <p className="static-panel-text">
              The API stores incident rows in <strong>SQLite</strong> on the server (for the dashboard and
              reports). Settings you change in this app are saved in <strong>localStorage</strong> in your
              browser.
            </p>
            <p className="static-panel-text">
              Deploying your own instance: configure HTTPS, restrict CORS with{" "}
              <code className="sample-code">CRISIS_COMPASS_CORS_ORIGINS</code>, and review logs and retention
              on your server.
            </p>
          </section>
        )}
      </main>

      <footer className="site-footer">
        <div className="container site-footer-inner">
          <span className="site-footer-brand">CrisisCompass</span>
          <div className="site-footer-right">
            <span className="site-footer-links" role="navigation" aria-label="Legal and about">
              <button type="button" className="footer-link" onClick={() => goTo("about")}>
                About
              </button>
              <span className="footer-dot" aria-hidden="true">
                ·
              </span>
              <button type="button" className="footer-link" onClick={() => goTo("privacy")}>
                Privacy
              </button>
            </span>
            <span className="site-footer-meta">
              Local feeds · severity signals · {new Date().getFullYear()}
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
