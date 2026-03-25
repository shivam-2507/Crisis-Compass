const STORAGE_KEY = "crisis-compass-settings@v1"

export const DEFAULT_SETTINGS = {
  severityFloor: "low",
  quietStart: "22:00",
  quietEnd: "07:00",
  channelInApp: true,
  channelEmail: false,
  channelSms: false,
  includeLlm: true,
  llmTone: "neutral",
  llmLength: "short",
  fontScale: 100,
  reducedMotion: false,
}

function merge(base, patch) {
  return { ...base, ...patch }
}

export function loadSettings() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { ...DEFAULT_SETTINGS }
    const parsed = JSON.parse(raw)
    if (typeof parsed !== "object" || parsed === null) return { ...DEFAULT_SETTINGS }
    return merge(DEFAULT_SETTINGS, parsed)
  } catch {
    return { ...DEFAULT_SETTINGS }
  }
}

export function saveSettings(settings) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch {
    /* ignore quota */
  }
}

export const SEVERITY_FLOOR_OPTIONS = [
  { id: "low", label: "Low and above (all)" },
  { id: "medium", label: "Medium and high only" },
  { id: "high", label: "High only" },
]

export const LLM_TONE_OPTIONS = [
  { id: "neutral", label: "Neutral" },
  { id: "urgent", label: "Direct / urgent" },
  { id: "calm", label: "Calm / plain language" },
]

export const LLM_LENGTH_OPTIONS = [
  { id: "short", label: "Short" },
  { id: "medium", label: "Medium" },
  { id: "long", label: "Longer" },
]

export function inQuietHours(date, quietStart, quietEnd) {
  const start = (quietStart || "22:00").trim()
  const end = (quietEnd || "07:00").trim()
  const parse = (s) => {
    const [h, m] = s.split(":").map((x) => parseInt(x, 10))
    if (Number.isNaN(h)) return null
    return (h % 24) * 60 + (Number.isNaN(m) ? 0 : m % 60)
  }
  const sm = parse(start)
  const em = parse(end)
  if (sm == null || em == null) return false
  const m = date.getHours() * 60 + date.getMinutes()
  if (sm <= em) return m >= sm && m < em
  return m >= sm || m < em
}

export function severityMeetsFloor(severity, floor) {
  const rank = { low: 1, medium: 2, high: 3 }
  const r = rank[(severity || "low").toLowerCase()] || 1
  const f = rank[(floor || "low").toLowerCase()] || 1
  return r >= f
}
