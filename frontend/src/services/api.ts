import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { getSession, signOut } from 'next-auth/react';
import { toast } from '@/components/ui/use-toest';

// Types
type ApiResponse<T = any> = {
  data: T;
  message?: string;
  success: boolean;
};

type ApiError = {
  message: string;
  statusCode: number;
  errors?: Record<string, string[]>;
};

// Create a custom axios instance with default config
const createApiClient = (): AxiosInstance => {
  const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
    headers: {
      'Content-Type': 'application/json',
    },
    withCredentials: true,
    timeout: 10000, // 10 seconds
  });

  return api;
};

const api = createApiClient();

// Request interceptor for adding auth token
api.interceptors.request.use(
  async (config: AxiosRequestConfig) => {
    try {
      const session = await getSession();
      if (session?.accessToken) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${session.accessToken}`;
      }
      return config;
    } catch (error) {
      return Promise.reject(error);
    }
  },
  (error: AxiosError) => {
    return Promise.reject(handleApiError(error));
  }
);

// Response interceptor for handling errors and token refresh
api.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    // Handle successful responses
    if (response.data?.message) {
      toast({
        title: 'Success',
        description: response.data.message,
        variant: 'default',
      });
    }
    return response;
  },
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as any;
    
    // Handle 401 Unauthorized errors (token expired)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Try to refresh the token
        const session = await getSession();
        if (session?.refreshToken) {
          const response = await axios.post<{ accessToken: string }>(
            '/auth/refresh-token',
            { refreshToken: session.refreshToken },
            { baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api' }
          );
          
          const { accessToken } = response.data;
          
          // Update the session with the new token
          // This would typically be handled by your auth provider
          // For NextAuth, you would update the session
          
          // Retry the original request with the new token
          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // If refresh token fails, sign out and redirect to login
        await signOut({ redirect: false });
        window.location.href = '/auth/login';
        return Promise.reject(refreshError);
      }
    }
    
    // Handle other errors
    const apiError = handleApiError(error);
    return Promise.reject(apiError);
  }
);

// Helper function to handle API errors
function handleApiError(error: unknown): ApiError {
  if (axios.isAxiosError(error)) {
    const status = error.response?.status || 500;
    const responseData = error.response?.data as ApiError;
    
    // Show error toast
    toast({
      title: 'Error',
      description: responseData?.message || 'An unexpected error occurred',
      variant: 'destructive',
    });
    
    return {
      message: responseData?.message || 'An error occurred',
      statusCode: status,
      errors: responseData?.errors,
    };
  }
  
  // Handle non-Axios errors
  console.error('Non-Axios error:', error);
  return {
    message: 'An unexpected error occurred',
    statusCode: 500,
  };
}

// API Response Types
type PaginatedResponse<T> = {
  data: T[];
  total: number;
  page: number;
  limit: number;
};

// Auth API
export const authApi = {
  login: (credentials: { email: string; password: string }) =>
    api.post<{ accessToken: string; refreshToken: string }>('/auth/login', credentials),
  
  register: (userData: { name: string; email: string; password: string }) =>
    api.post<{ id: string; email: string; name: string }>('/auth/register', userData),
  
  forgotPassword: (email: string) =>
    api.post<{ message: string }>('/auth/forgot-password', { email }),
  
  resetPassword: (token: string, newPassword: string) =>
    api.post<{ message: string }>('/auth/reset-password', { token, newPassword }),
  
  refreshToken: (refreshToken: string) =>
    api.post<{ accessToken: string }>('/auth/refresh-token', { refreshToken }),
  
  logout: () => api.post<{ message: string }>('/auth/logout'),
};

// Conversation Types
type Conversation = {
  id: string;
  title: string;
  userId: string;
  createdAt: string;
  updatedAt: string;
  lastMessage?: Message;
  unreadCount?: number;
};

// Conversations API
export const conversationsApi = {
  getAll: (params?: { page?: number; limit?: number; search?: string }) =>
    api.get<PaginatedResponse<Conversation>>('/conversations', { params }),
    
  getById: (id: string) =>
    api.get<Conversation>(`/conversations/${id}`),
    
  create: (data: { title: string; userIds?: string[] }) =>
    api.post<Conversation>('/conversations', data),
    
  update: (id: string, data: { title?: string; metadata?: Record<string, any> }) =>
    api.put<Conversation>(`/conversations/${id}`, data),
    
  delete: (id: string) =>
    api.delete<{ message: string }>(`/conversations/${id}`),
    
  markAsRead: (conversationId: string) =>
    api.post<{ message: string }>(`/conversations/${conversationId}/read`),
};

// Message Types
type Message = {
  id: string;
  content: string;
  conversationId: string;
  userId: string;
  user: {
    id: string;
    name: string;
    avatar?: string;
  };
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
};

// Messages API
export const messagesApi = {
  getByConversationId: (conversationId: string, params?: { 
    page?: number; 
    limit?: number; 
    before?: string;
  }) =>
    api.get<PaginatedResponse<Message>>(
      `/conversations/${conversationId}/messages`, 
      { params }
    ),
    
  send: (conversationId: string, content: string, metadata?: Record<string, any>) =>
    api.post<Message>(`/conversations/${conversationId}/messages`, { content, metadata }),
    
  update: (messageId: string, data: { content?: string; metadata?: Record<string, any> }) =>
    api.put<Message>(`/messages/${messageId}`, data),
    
  delete: (messageId: string) =>
    api.delete<{ message: string }>(`/messages/${messageId}`),
    
  uploadFile: (conversationId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<Message>(`/conversations/${conversationId}/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// User Types
type UserProfile = {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  createdAt: string;
  updatedAt: string;
};

// User API
export const userApi = {
  getProfile: () => api.get<UserProfile>('/users/me'),
  
  updateProfile: (data: { name?: string; email?: string; avatar?: string }) =>
    api.put<UserProfile>('/users/me', data),
    
  changePassword: (data: { currentPassword: string; newPassword: string }) =>
    api.put<{ message: string }>('/users/me/password', data),
    
  uploadAvatar: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<{ url: string }>('/users/me/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

// Export API instance with types
export default api;
