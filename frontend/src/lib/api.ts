import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios'
import { useToast } from '@/components/ui/use-toast'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

class ApiClient {
  private instance: AxiosInstance

  constructor() {
    this.instance = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.instance.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('access_token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return Promise.resolve(config)
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor to handle errors
    this.instance.interceptors.response.use(
      (response) => response,
      (error) => {
        const { toast } = useToast()

        if (error.response?.status === 401) {
          // Handle unauthorized access
          localStorage.removeItem('access_token')
          window.location.href = '/signin'
        }

        if (error.response?.status === 500) {
          toast({
            title: 'Server Error',
            description: 'An unexpected error occurred. Please try again later.',
            variant: 'destructive',
          })
        }

        return Promise.reject(error)
      }
    )
  }

  get instanceAxios() {
    return this.instance
  }

  // Generic request methods
  async get<T>(url: string, config?: InternalAxiosRequestConfig) {
    const response = await this.instance.get<T>(url, config)
    return response.data
  }

  async post<T>(url: string, data?: any, config?: InternalAxiosRequestConfig) {
    const response = await this.instance.post<T>(url, data, config)
    return response.data
  }

  async put<T>(url: string, data?: any, config?: InternalAxiosRequestConfig) {
    const response = await this.instance.put<T>(url, data, config)
    return response.data
  }

  async delete<T>(url: string, config?: InternalAxiosRequestConfig) {
    const response = await this.instance.delete<T>(url, config)
    return response.data
  }

  async patch<T>(url: string, data?: any, config?: InternalAxiosRequestConfig) {
    const response = await this.instance.patch<T>(url, data, config)
    return response.data
  }
}

// Create and export a singleton instance
export const api = new ApiClient().instanceAxios

// Export the class for testing or multiple instances
export { ApiClient }

// Type definitions for API responses
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message?: string
  errors?: string[]
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  has_more: boolean
}
