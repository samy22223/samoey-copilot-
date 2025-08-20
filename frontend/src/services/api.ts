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

// File Types
type FileInfo = {
  id: string;
  original_filename: string;
  stored_filename: string;
  file_size: number;
  content_type: string;
  description: string;
  uploaded_at: string;
  downloads: number;
};

// Files API
export const filesApi = {
  upload: (file: File, description?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (description) formData.append('description', description);
    return api.post<{ file_id: string; filename: string; file_size: number; uploaded_at: string }>('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  getAll: (params?: { skip?: number; limit?: number }) =>
    api.get<{ files: FileInfo[] }>('/files/', { params }),

  getById: (id: string) =>
    api.get<FileInfo>(`/files/${id}`),

  download: (id: string) =>
    api.get<{ file_path: string; filename: string; content_type: string; downloads: number }>(`/files/${id}/download`),

  delete: (id: string) =>
    api.delete<{ message: string }>(`/files/${id}`),

  updateDescription: (id: string, description: string) =>
    api.put<{ message: string }>(`/files/${id}`, { description }),

  getStorageStats: () =>
    api.get<{ total_files: number; total_size_bytes: number; total_size_mb: number; total_downloads: number; by_file_type: Record<string, number> }>('/files/stats/storage'),
};

// Notification Types
type Notification = {
  id: string;
  user_id: string;
  title: string;
  message: string;
  type: string;
  data: Record<string, any>;
  created_at: string;
  read: boolean;
};

// Notifications API
export const notificationsApi = {
  getAll: (params?: { skip?: number; limit?: number; unread_only?: boolean }) =>
    api.get<{ notifications: Notification[] }>('/notifications/', { params }),

  markAsRead: (id: string) =>
    api.post<{ message: string }>(`/notifications/${id}/read`),

  markAllAsRead: () =>
    api.post<{ message: string }>('/notifications/mark-all-read'),

  delete: (id: string) =>
    api.delete<{ message: string }>(`/notifications/${id}`),

  getStats: () =>
    api.get<{ total: number; unread: number; read: number; by_type: Record<string, number> }>('/notifications/stats'),

  create: (title: string, message: string, type?: string) =>
    api.post<{ message: string; notification: Notification }>('/notifications/create', { title, message, type }),
};

// Analytics Types
type UsageAnalytics = {
  period: { start_date: string; end_date: string };
  user_activity: { total_sessions: number; active_days: number; average_session_duration: string; last_activity: string };
  messaging: { total_messages_sent: number; total_messages_received: number; average_response_time: string; conversations_started: number };
  file_operations: { files_uploaded: number; files_downloaded: number; total_storage_used: string; file_types: Record<string, number> };
  api_usage: { total_requests: number; successful_requests: number; failed_requests: number; average_response_time: string; peak_hour: string };
  ai_interactions: { ai_queries: number; code_generations: number; document_analyses: number; average_ai_response_time: string };
};

type PerformanceMetrics = {
  timestamp: string;
  system: { cpu_usage: string; memory_usage: string; memory_total: string; memory_available: string; disk_usage: string; disk_total: string; disk_free: string };
  process: { memory_usage: string; cpu_usage: string; threads: number; open_files: number };
  network: { bytes_sent: number; bytes_recv: number; packets_sent: number; packets_recv: number };
  response_times: { average_api_response: string; p95_response_time: string; p99_response_time: string };
  health: { status: string; uptime: number };
};

// Analytics API
export const analyticsApi = {
  getUsage: (params?: { start_date?: string; end_date?: string }) =>
    api.get<UsageAnalytics>('/analytics/usage', { params }),

  getPerformance: () =>
    api.get<PerformanceMetrics>('/analytics/performance'),

  getUser: (days?: number) =>
    api.get<{ user_id: string; period: string; activity_summary: any; feature_usage: any; engagement_metrics: any; growth_trend: any }>('/analytics/user', { params: { days } }),

  getSystem: () =>
    api.get<{ timestamp: string; overview: any; performance: any; resource_usage: any; top_features: any; alerts: any }>('/analytics/system'),

  getRealtime: () =>
    api.get<{ timestamp: string; current: any; performance: any; health: any }>('/analytics/realtime'),

  recordEvent: (event_type: string, data: Record<string, any>) =>
    api.post<{ message: string }>('/analytics/events', { event_type, data }),
};

// Health Types
type HealthStatus = {
  status: string;
  service: string;
  version: string;
  checks: Record<string, any>;
};

// Health API
export const healthApi = {
  check: () => api.get<HealthStatus>('/health/'),
  simple: () => api.get<{ status: string; service: string; version: string }>('/health/simple'),
  ready: () => api.get<{ status: string; service: string; version: string }>('/health/ready'),
  live: () => api.get<{ status: string; service: string; version: string }>('/health/live'),
};

// Security Status Types
type SecurityOverview = {
  security_enabled: boolean;
  rate_limiting_enabled: boolean;
  last_security_scan: string;
  threat_level: string;
  active_sessions: number;
  blocked_attempts: number;
  security_score: number;
};

// Security Status API
export const securityApi = {
  getOverview: () => api.get<SecurityOverview>('/security_status/overview'),
  getMetrics: () => api.get<any>('/security_status/metrics'),
  getAlerts: (params?: { limit?: number; severity?: string }) =>
    api.get<{ alerts: any[] }>('/security_status/alerts', { params }),
  getAuditLog: (params?: { limit?: number; offset?: number; event_type?: string; start_date?: string; end_date?: string }) =>
    api.get<{ logs: any[] }>('/security_status/audit-log', { params }),
  getVulnerabilities: () => api.get<{ vulnerabilities: any[] }>('/security_status/vulnerabilities'),
  initiateScan: () => api.post<{ scan_id: string; message: string; status: string }>('/security_status/scan'),
  getScanResults: (scan_id: string) => api.get<any>(`/security_status/scan/${scan_id}`),
  getFirewallRules: () => api.get<any>('/security_status/firewall-rules'),
  getCompliance: () => api.get<any>('/security_status/compliance'),
  getIncidents: (params?: { limit?: number; status?: string }) =>
    api.get<{ incidents: any[] }>('/security_status/incidents', { params }),
  resolveIncident: (incident_id: string) =>
    api.post<{ message: string }>(`/security_status/incidents/${incident_id}/resolve`),
  getThreatIntelligence: () => api.get<{ threats: any[] }>('/security_status/threat-intelligence'),
  getBackupStatus: () => api.get<any>('/security_status/backup-status'),
};

// Storage Types
type StorageStats = {
  success: boolean;
  storage_stats: { total_files: number; total_size_bytes: number; total_size_mb: number; total_downloads: number; by_file_type: Record<string, number> };
};

// Storage API
export const storageApi = {
  optimize: () => api.post<{ success: boolean; message: string; results: any }>('/storage/optimize'),
  optimizeCache: () => api.post<{ success: boolean; message: string; results: any }>('/storage/optimize/cache'),
  optimizeLogs: (days?: number) => api.post<{ success: boolean; message: string; results: any }>('/storage/optimize/logs', { params: { days } }),
  optimizeUploads: () => api.post<{ success: boolean; message: string; results: any }>('/storage/optimize/uploads'),
  optimizeDatabase: () => api.post<{ success: boolean; message: string; results: any }>('/storage/optimize/database'),
  getStats: () => api.get<StorageStats>('/storage/stats'),
};

// Export API instance with types
export default api;
