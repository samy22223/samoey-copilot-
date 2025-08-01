// General utility functions
export const formatDate = (date) => {
  return new Date(date).toLocaleString()
}

export const truncate = (str, length = 100) => {
  return str.length > length ? str.substring(0, length) + '...' : str
}

// Error handling utilities
export const handleError = (error) => {
  console.error('Error:', error)
  return {
    error: true,
    message: error.message || 'An unknown error occurred'
  }
}

// Validation helpers
export const isValidEmail = (email) => {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

export const isNotEmpty = (value) => {
  return value.trim() !== ''
}

// AI-specific utilities
export const getModelInfo = (modelId) => {
  const models = require('../config/aiModels')
  return Object.values(models).flatMap(group => 
    Object.entries(group).find(([_, model]) => model.id === modelId)
  ).find(Boolean)?.[1]
}
