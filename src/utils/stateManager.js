const STATE_CACHE_KEY = 'pinnacle-state'

export class StateManager {
  constructor() {
    this.state = this.loadState() || {
      localChanges: [],
      cloudState: {},
      syncing: false
    }
  }

  loadState() {
    return JSON.parse(localStorage.getItem(STATE_CACHE_KEY))
  }

  async saveState() {
    localStorage.setItem(STATE_CACHE_KEY, JSON.stringify(this.state))
    return true
  }

  async restoreFromCloud(cloudState) {
    this.state.cloudState = cloudState
    return this.saveState()
  }
}

export default new StateManager()
