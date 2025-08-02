import syncService from '../services/syncService'
import authService from '../services/authService'
import settingsService from '../services/settingsService'

export default {
  async initializePlatforms() {
    const settings = settingsService.getSettings()
    const authTokens = authService.getCachedAuthTokens()
    
    // Initialize each enabled platform
    const initializedPlatforms = {}
    for (const platform of settings.platforms || []) {
      try {
        // Verify authentication
        if (!authTokens[platform]) {
          await authService.authenticate(platform)
        }
        
        // Initialize sync
        initializedPlatforms[platform] = await syncService.initialize({
          provider: platform,
          autoSync: settings.autoSync
        })
      } catch (error) {
        console.error(`Failed to initialize ${platform}:`, error)
      }
    }
    
    return initializedPlatforms
  },

  async syncAllPlatforms() {
    const platforms = Object.keys(this.initializePlatforms())
    const results = {}
    
    for (const platform of platforms) {
      try {
        results[platform] = await syncService.fullSync(platform)
      } catch (error) {
        results[platform] = { error: error.message }
      }
    }
    
    return results
  },

  async getSyncStatus() {
    const status = {}
    const platforms = Object.keys(this.initializePlatforms())
    
    for (const platform of platforms) {
      status[platform] = await syncService.status(platform)
    }
    
    return status
  },

  async resolveConflicts(conflictResolution) {
    // Handle any sync conflicts
    return syncService.resolveConflicts(conflictResolution)
  }
}
