// Settings management for the drone control app

const STORAGE_KEY = "drone-control-settings"

export type AppSettings = {
  apiUrl: string
  theme: "dark" | "light"
}

export const DEFAULT_SETTINGS: AppSettings = {
  apiUrl: "http://localhost:8000",
  theme: "dark",
}

// Load settings from localStorage
export function loadSettings(): AppSettings {
  if (typeof window === "undefined") {
    return DEFAULT_SETTINGS
  }

  try {
    const savedSettings = localStorage.getItem(STORAGE_KEY)
    if (savedSettings) {
      return JSON.parse(savedSettings) as AppSettings
    }
  } catch (error) {
    console.error("Error loading settings:", error)
  }

  return DEFAULT_SETTINGS
}

// Save settings to localStorage
export function saveSettings(settings: AppSettings): void {
  if (typeof window === "undefined") {
    return
  }

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  } catch (error) {
    console.error("Error saving settings:", error)
  }
}

// Update a single setting
export function updateSetting<K extends keyof AppSettings>(key: K, value: AppSettings[K]): AppSettings {
  const currentSettings = loadSettings()
  const newSettings = { ...currentSettings, [key]: value }
  saveSettings(newSettings)
  return newSettings
}
