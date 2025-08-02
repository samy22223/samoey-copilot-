import axios from 'axios'

const API_BASE_URL = 'http://localhost:11434/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export default {
  async getCodeCompletion(prompt, model = 'codellama') {
    try {
      const response = await api.post('/generate', {
        model,
        prompt,
        stream: false
      })
      return response.data
    } catch (error) {
      console.error('AI API Error:', error)
      throw error
    }
  },

  async listModels() {
    try {
      const response = await api.get('/tags')
      return response.data
    } catch (error) {
      console.error('Failed to fetch models:', error)
      return []
    }
  }
}
