import React, { Component } from 'react'
import { handleError } from '../utils/helpers'

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error Boundary caught:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      const errorResult = handleError(this.state.error)
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>{errorResult.message}</p>
          <button onClick={() => window.location.reload()}>
            Reload Application
          </button>
        </div>
      )
    }

    return this.props.children
  }
}
