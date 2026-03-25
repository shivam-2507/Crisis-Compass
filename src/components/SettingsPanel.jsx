import {
  SEVERITY_FLOOR_OPTIONS,
  LLM_TONE_OPTIONS,
  LLM_LENGTH_OPTIONS,
} from "../settingsStorage"

/* eslint-disable react/prop-types */
export function SettingsPanel({ settings, onChange }) {
  const patch = (partial) => onChange({ ...settings, ...partial })

  return (
    <section className="static-panel settings-panel" aria-labelledby="settings-heading">
      <h2 id="settings-heading" className="static-panel-title">
        Settings
      </h2>
      <p className="static-panel-text">
        Preferences are stored in this browser only. The incident list uses your severity floor; reports use
        the same account for optional AI summaries when an API key is configured on the server.
      </p>

      <div className="settings-grid">
        <fieldset className="settings-fieldset">
          <legend className="settings-legend">Incident list</legend>
          <label className="settings-label" htmlFor="severity-floor">
            Minimum severity to show
          </label>
          <select
            id="severity-floor"
            className="settings-select"
            value={settings.severityFloor}
            onChange={(e) => patch({ severityFloor: e.target.value })}
          >
            {SEVERITY_FLOOR_OPTIONS.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
        </fieldset>

        <fieldset className="settings-fieldset">
          <legend className="settings-legend">Quiet hours</legend>
          <p className="settings-hint">
            During this range, the incidents view shows a quiet-hours notice. Email/SMS are not wired in this
            build.
          </p>
          <div className="settings-row">
            <div>
              <label className="settings-label" htmlFor="quiet-start">
                Start
              </label>
              <input
                id="quiet-start"
                type="time"
                className="settings-input"
                value={settings.quietStart}
                onChange={(e) => patch({ quietStart: e.target.value })}
              />
            </div>
            <div>
              <label className="settings-label" htmlFor="quiet-end">
                End
              </label>
              <input
                id="quiet-end"
                type="time"
                className="settings-input"
                value={settings.quietEnd}
                onChange={(e) => patch({ quietEnd: e.target.value })}
              />
            </div>
          </div>
        </fieldset>

        <fieldset className="settings-fieldset">
          <legend className="settings-legend">Delivery channels</legend>
          <label className="settings-check">
            <input
              type="checkbox"
              checked={settings.channelInApp}
              onChange={(e) => patch({ channelInApp: e.target.checked })}
            />
            In-app notices (quiet-hours banner on Incidents)
          </label>
          <label className="settings-check settings-check-disabled">
            <input type="checkbox" disabled checked={false} readOnly />
            Email (requires server deployment)
          </label>
          <label className="settings-check settings-check-disabled">
            <input type="checkbox" disabled checked={false} readOnly />
            SMS (requires server deployment)
          </label>
        </fieldset>

        <fieldset className="settings-fieldset">
          <legend className="settings-legend">Reports — AI (LangChain / OpenAI)</legend>
          <label className="settings-check">
            <input
              type="checkbox"
              checked={settings.includeLlm}
              onChange={(e) => patch({ includeLlm: e.target.checked })}
            />
            Include AI summary and entity graph on Reports
          </label>
          <label className="settings-label" htmlFor="llm-tone">
            Tone
          </label>
          <select
            id="llm-tone"
            className="settings-select"
            value={settings.llmTone}
            onChange={(e) => patch({ llmTone: e.target.value })}
          >
            {LLM_TONE_OPTIONS.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
          <label className="settings-label" htmlFor="llm-length">
            Summary length
          </label>
          <select
            id="llm-length"
            className="settings-select"
            value={settings.llmLength}
            onChange={(e) => patch({ llmLength: e.target.value })}
          >
            {LLM_LENGTH_OPTIONS.map((o) => (
              <option key={o.id} value={o.id}>
                {o.label}
              </option>
            ))}
          </select>
        </fieldset>

        <fieldset className="settings-fieldset">
          <legend className="settings-legend">Accessibility</legend>
          <label className="settings-label" htmlFor="font-scale">
            Base size ({settings.fontScale}%)
          </label>
          <input
            id="font-scale"
            type="range"
            min="90"
            max="120"
            step="5"
            value={settings.fontScale}
            onChange={(e) => patch({ fontScale: Number(e.target.value) })}
          />
          <label className="settings-check">
            <input
              type="checkbox"
              checked={settings.reducedMotion}
              onChange={(e) => patch({ reducedMotion: e.target.checked })}
            />
            Reduce motion (limits animations)
          </label>
        </fieldset>
      </div>
    </section>
  )
}
