import { useCallback, useEffect, useMemo, useState } from "react"
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
} from "recharts"
import { RefreshCw, Download, Printer, FileText } from "lucide-react"
import { api, getApiBase } from "../api"

/* eslint-disable react/prop-types */
export function ReportsPanel({ includeLlm, llmTone, llmLength }) {
  const [preset, setPreset] = useState(24)
  const [customHours, setCustomHours] = useState("48")
  const [compare, setCompare] = useState(false)
  const [compareHours, setCompareHours] = useState(168)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [payload, setPayload] = useState(null)

  const resolvedHours = useMemo(() => {
    if (preset === "custom") {
      const n = parseFloat(customHours)
      return Number.isFinite(n) && n > 0 ? Math.min(n, 8760) : 24
    }
    return preset
  }, [preset, customHours])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const body = {
        hours: resolvedHours,
        compare_hours: compare ? compareHours : null,
        include_llm: includeLlm,
        tone: llmTone,
        length: llmLength,
      }
      const res = await api.post("/report/insights", body)
      setPayload(res.data)
    } catch (e) {
      console.error(e)
      setError("Could not load report. Is the API running?")
      setPayload(null)
    } finally {
      setLoading(false)
    }
  }, [resolvedHours, compare, compareHours, includeLlm, llmTone, llmLength])

  useEffect(() => {
    load()
  }, [load])

  const summary = payload?.summary
  const primary = summary?.primary
  const cmp = summary?.compare
  const insights = payload?.insights
  const seriesTime = primary?.series_severity_time || []
  const byType = primary?.series_by_type || []
  const topSources = primary?.top_sources || []
  const trustDist = primary?.trust_distribution || []

  const exportCsvUrl = `${getApiBase()}/report/export.csv?hours=${encodeURIComponent(String(resolvedHours))}`
  const printUrl = `${getApiBase()}/report/print.html?hours=${encodeURIComponent(String(resolvedHours))}`

  const llmNotice = payload?.llm_notice
  const llmError = payload?.llm_error

  return (
    <section className="reports-panel" aria-labelledby="reports-heading">
      <div className="reports-header">
        <h2 id="reports-heading" className="static-panel-title">
          Reports
        </h2>
        <p className="static-panel-text reports-lead">
          Charts and totals are computed on the server from stored incidents. Optional AI summary and entity
          graph use OpenAI via LangChain when <code className="sample-code">OPENAI_API_KEY</code> is set.
        </p>
      </div>

      <div className="reports-toolbar" role="region" aria-label="Report options">
        <div className="reports-toolbar-row">
          <span className="toolbar-label">Window</span>
          <div className="toolbar-pills" role="group">
            {[24, 168].map((h) => (
              <button
                key={h}
                type="button"
                className={`toolbar-pill${preset === h ? " toolbar-pill-active" : ""}`}
                onClick={() => setPreset(h)}
              >
                {h === 24 ? "24 h" : "7 d"}
              </button>
            ))}
            <button
              type="button"
              className={`toolbar-pill${preset === "custom" ? " toolbar-pill-active" : ""}`}
              onClick={() => setPreset("custom")}
            >
              Custom
            </button>
          </div>
          {preset === "custom" && (
            <label className="reports-custom-hours">
              Hours
              <input
                type="number"
                min="1"
                max="8760"
                step="1"
                value={customHours}
                onChange={(e) => setCustomHours(e.target.value)}
                className="settings-input reports-number"
              />
            </label>
          )}
        </div>
        <div className="reports-toolbar-row">
          <label className="settings-check">
            <input type="checkbox" checked={compare} onChange={(e) => setCompare(e.target.checked)} />
            Compare to previous period
          </label>
          {compare && (
            <label className="reports-compare-select">
              Previous span (hours)
              <select
                className="settings-select"
                value={compareHours}
                onChange={(e) => setCompareHours(Number(e.target.value))}
              >
                <option value={24}>24</option>
                <option value={72}>72</option>
                <option value={168}>168 (7d)</option>
              </select>
            </label>
          )}
        </div>
        <div className="reports-toolbar-actions">
          <button type="button" className="refresh-button" onClick={load} disabled={loading}>
            <RefreshCw className={`icon ${loading ? "spinning" : ""}`} aria-hidden="true" />
            Refresh
          </button>
          <a className="refresh-button reports-link-button" href={exportCsvUrl} download>
            <Download className="icon" aria-hidden="true" />
            CSV
          </a>
          <button
            type="button"
            className="refresh-button"
            onClick={() => window.open(printUrl, "_blank", "noopener,noreferrer")}
          >
            <Printer className="icon" aria-hidden="true" />
            Printable
          </button>
        </div>
      </div>

      {error && (
        <div className="error-banner" role="alert">
          <p className="error-banner-text">{error}</p>
        </div>
      )}

      {loading && !primary && <p className="reports-loading">Loading report…</p>}

      {primary && (
        <>
          <div className="reports-meta muted-card" role="status">
            <p>
              <strong>Window:</strong> last {primary.hours} h · <strong>Incidents:</strong>{" "}
              {primary.totals?.count ?? 0} · <strong>Generated:</strong>{" "}
              {summary?.generated_at ? new Date(summary.generated_at).toLocaleString() : "—"}
            </p>
            {cmp && (
              <p>
                <strong>Comparison window:</strong> {cmp.hours} h before that ·{" "}
                <strong>Incidents:</strong> {cmp.totals?.count ?? 0}
              </p>
            )}
          </div>

          {cmp && (
            <div className="reports-compare-cards">
              <div className="muted-card compare-card">
                <h3 className="reports-chart-title">Primary totals</h3>
                <pre className="reports-pre">{JSON.stringify(primary.totals?.by_severity, null, 2)}</pre>
              </div>
              <div className="muted-card compare-card">
                <h3 className="reports-chart-title">Previous period</h3>
                <pre className="reports-pre">{JSON.stringify(cmp.totals?.by_severity, null, 2)}</pre>
              </div>
            </div>
          )}

          <div className="reports-charts">
            <div className="muted-card reports-chart-card">
              <h3 className="reports-chart-title">Severity over time</h3>
              {seriesTime.length === 0 ? (
                <p className="reports-empty">No time series data in this window.</p>
              ) : (
                <div className="reports-chart-wrap">
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={seriesTime}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis dataKey="label" tick={{ fill: "#9ca3af", fontSize: 10 }} height={56} />
                      <YAxis tick={{ fill: "#9ca3af", fontSize: 11 }} allowDecimals={false} />
                      <Tooltip
                        contentStyle={{
                          background: "#111827",
                          border: "1px solid rgba(255,255,255,0.12)",
                          borderRadius: "8px",
                        }}
                        labelStyle={{ color: "#e5e7eb" }}
                      />
                      <Legend />
                      <Line type="monotone" dataKey="high" name="High" stroke="#fbbf24" strokeWidth={2} dot={false} />
                      <Line
                        type="monotone"
                        dataKey="medium"
                        name="Medium"
                        stroke="#38bdf8"
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line type="monotone" dataKey="low" name="Low" stroke="#94a3b8" strokeWidth={2} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            <div className="muted-card reports-chart-card">
              <h3 className="reports-chart-title">By type</h3>
              {byType.length === 0 ? (
                <p className="reports-empty">No type breakdown.</p>
              ) : (
                <div className="reports-chart-wrap">
                  <ResponsiveContainer width="100%" height={260}>
                    <BarChart data={byType} layout="vertical" margin={{ left: 8, right: 16 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis type="number" tick={{ fill: "#9ca3af" }} allowDecimals={false} />
                      <YAxis type="category" dataKey="type" width={100} tick={{ fill: "#9ca3af", fontSize: 11 }} />
                      <Tooltip
                        contentStyle={{
                          background: "#111827",
                          border: "1px solid rgba(255,255,255,0.12)",
                          borderRadius: "8px",
                        }}
                      />
                      <Bar dataKey="count" name="Count" fill="#c9a227" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            <div className="muted-card reports-chart-card">
              <h3 className="reports-chart-title">Top sources</h3>
              {topSources.length === 0 ? (
                <p className="reports-empty">No sources in window.</p>
              ) : (
                <div className="reports-chart-wrap">
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={topSources.slice(0, 10)}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis dataKey="source" tick={{ fill: "#9ca3af", fontSize: 9 }} interval={0} angle={-25} textAnchor="end" height={72} />
                      <YAxis tick={{ fill: "#9ca3af" }} allowDecimals={false} />
                      <Tooltip
                        contentStyle={{
                          background: "#111827",
                          border: "1px solid rgba(255,255,255,0.12)",
                          borderRadius: "8px",
                        }}
                      />
                      <Bar dataKey="count" fill="#5eead4" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            <div className="muted-card reports-chart-card">
              <h3 className="reports-chart-title">Trust score distribution</h3>
              {trustDist.length === 0 ? (
                <p className="reports-empty">No trust data.</p>
              ) : (
                <div className="reports-chart-wrap">
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={trustDist}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                      <XAxis dataKey="range" tick={{ fill: "#9ca3af" }} />
                      <YAxis tick={{ fill: "#9ca3af" }} allowDecimals={false} />
                      <Tooltip
                        contentStyle={{
                          background: "#111827",
                          border: "1px solid rgba(255,255,255,0.12)",
                          borderRadius: "8px",
                        }}
                      />
                      <Bar dataKey="count" fill="#a78bfa" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>
          </div>

          <div className="muted-card reports-ai-card">
            <h3 className="reports-chart-title">
              <FileText className="icon reports-inline-icon" aria-hidden="true" />
              AI summary and entity graph
            </h3>
            {llmNotice && <p className="reports-llm-notice">{llmNotice}</p>}
            {llmError && (
              <p className="error-banner-text reports-llm-error" role="status">
                AI unavailable: {llmError}
              </p>
            )}
            {insights?.executive_summary && (
              <p className="reports-summary-text">{insights.executive_summary}</p>
            )}
            {!includeLlm && (
              <p className="reports-llm-notice">AI sections disabled in Settings.</p>
            )}
            {includeLlm && !insights?.executive_summary && !llmError && !llmNotice && !loading && (
              <p className="reports-llm-notice">No AI output for this window.</p>
            )}

            {insights?.entity_graph?.nodes?.length > 0 && (
              <div className="entity-graph-block">
                <h4 className="entity-graph-heading">Entities</h4>
                <div className="entity-chips" role="list">
                  {insights.entity_graph.nodes.map((n) => (
                    <span key={n.id} className="entity-chip" role="listitem">
                      {n.label}
                      <span className="entity-chip-type">{n.type}</span>
                    </span>
                  ))}
                </div>
                {insights.entity_graph.edges?.length > 0 && (
                  <>
                    <h4 className="entity-graph-heading">Relationships</h4>
                    <ul className="entity-edges">
                      {insights.entity_graph.edges.map((e, idx) => (
                        <li key={`${e.source}-${e.target}-${idx}`}>
                          <span className="entity-edge-src">{e.source}</span>
                          <span className="entity-edge-rel">{e.relation}</span>
                          <span className="entity-edge-tgt">{e.target}</span>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </div>
            )}
          </div>

          <p className="reports-disclaimer">
            Decision-support only — not an official emergency channel. Verify with local authorities.
          </p>
        </>
      )}
    </section>
  )
}
