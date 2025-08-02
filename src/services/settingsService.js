const SETTINGS_KEY = 'pinnacle-settings'

export default {
  getSettings() {
    return JSON.parse(localStorage.getItem(SETTINGS_KEY)) || {}
  },

  saveSettings(settings) {
    localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings))
  },

  updateSetting(key, value) {
    const current = this.getSettings()
    this.saveSettings({ ...current, [key]: value })
  },

  resetSettings() {
    localStorage.removeItem(SETTINGS_KEY)
  }
}
