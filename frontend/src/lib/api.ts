import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

export const authApi = {
  register: (data: { phone: string; username?: string; password: string; role?: string }) =>
    api.post('/api/v1/auth/register', data),
  
  login: (data: { phone?: string; username?: string; password: string }) =>
    api.post('/api/v1/auth/login', data),
  
  me: () => api.get('/api/v1/auth/me'),
  
  updateMe: (data: { username?: string; password?: string; current_password?: string }) =>
    api.patch('/api/v1/auth/me', data),
  
  uploadProfileImage: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/v1/auth/me/profile-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const productsApi = {
  list: (params?: { skip?: number; limit?: number; category_id?: number; search?: string }) =>
    api.get('/api/v1/products', { params }),
  
  feed: (params?: { page?: number; page_size?: number; search?: string; category_id?: number }) =>
    api.get('/api/v1/products/feed', { params }),
  
  get: (id: number) => api.get(`/api/v1/products/${id}`),
  
  create: (data: FormData) =>
    api.post('/api/v1/products', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  update: (id: number, data: FormData) =>
    api.put(`/api/v1/products/${id}`, data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  
  delete: (id: number) => api.delete(`/api/v1/products/${id}`),
  
  categories: () => api.get('/api/v1/products/categories'),
  
  createCategory: (data: { name: string; slug: string }) =>
    api.post('/api/v1/products/categories', data),
  
  markSold: (id: number) => api.post(`/api/v1/products/${id}/mark-sold`),
  
  myProducts: () => api.get('/api/v1/products/my-products'),

  createRating: (id: number, data: { rated_user_id: number; product_id: number; stars: number; comment?: string }) =>
    api.post(`/api/v1/products/${id}/ratings`, data),
  
  getUserRatings: (userId: number) => api.get(`/api/v1/products/users/${userId}/ratings`),
};

export const chatApi = {
  createConversation: (data: { product_id: number; receiver_id: number }) =>
    api.post('/api/v1/chat/conversations', data),
  
  listConversations: () => api.get('/api/v1/chat/conversations'),
  
  getMessages: (conversationId: number) =>
    api.get(`/api/v1/chat/conversations/${conversationId}`),
  
  sendMessage: (data: { conversation_id: number; content: string }) =>
    api.post('/api/v1/chat/messages', data),
  
  markRead: (conversationId: number) =>
    api.post(`/api/v1/chat/conversations/${conversationId}/read`),
  
  getNudges: () => api.get('/api/v1/chat/nudges'),
  
  getUnreadCount: () => api.get('/api/v1/chat/unread-count'),
};

export const adminApi = {
  getAnalytics: () => api.get('/api/v1/admin/analytics'),
  
  getPendingProducts: (params?: { skip?: number; limit?: number; search?: string }) =>
    api.get('/api/v1/admin/products/pending', { params }),
  
  getAllProducts: (params?: { skip?: number; limit?: number; search?: string; status?: string; is_approved?: boolean }) =>
    api.get('/api/v1/admin/products', { params }),
  
  approveProduct: (productId: number) => api.post(`/api/v1/admin/products/${productId}/approve`),
  
  rejectProduct: (productId: number) => api.post(`/api/v1/admin/products/${productId}/reject`),
  
  bulkAction: (data: { product_ids: number[]; action: string }) =>
    api.post('/api/v1/admin/products/bulk', data),
  
  listUsers: (params?: { skip?: number; limit?: number; search?: string; role?: string; is_active?: boolean }) =>
    api.get('/api/v1/admin/users', { params }),
  
  getUser: (userId: number) => api.get(`/api/v1/admin/users/${userId}`),
  
  updateUserRole: (userId: number, role: string) =>
    api.patch(`/api/v1/admin/users/${userId}/role?new_role=${role}`),
  
  deactivateUser: (userId: number) => api.patch(`/api/v1/admin/users/${userId}/deactivate`),
  
  deleteUser: (userId: number) => api.delete(`/api/v1/admin/users/${userId}`),
  
  deleteProduct: (productId: number) => api.delete(`/api/v1/admin/products/${productId}`),

  getAllRatings: () => api.get('/api/v1/admin/ratings'),
  
  deleteRating: (ratingId: number) => api.delete(`/api/v1/admin/ratings/${ratingId}`),

  getTickets: () => api.get('/api/v1/admin/tickets'),
  
  updateTicketStatus: (ticketId: number, status: string) => 
    api.patch(`/api/v1/admin/tickets/${ticketId}/status`, { new_status: status }),

  getConversationMessages: (conversationId: number) => 
    api.get(`/api/v1/admin/conversations/${conversationId}/messages`),

  broadcastNotification: (data: { title: string; message: string }) =>
    api.post('/api/v1/admin/notify/broadcast', data),

  getActivityLogs: () => api.get('/api/v1/admin/activity-logs'),
};

export const notificationsApi = {
  list: () => api.get('/api/v1/notifications'),
  
  unreadCount: () => api.get('/api/v1/notifications/unread-count'),
  
  markRead: (notificationId: number) => api.post(`/api/v1/notifications/${notificationId}/read`),
  
  markAllRead: () => api.post('/api/v1/notifications/read-all'),
};

export const ticketsApi = {
  create: (data: { ticket_type: string; description: string; reported_user_id?: number; product_id?: number }) =>
    api.post('/api/v1/tickets', data),
  
  list: () => api.get('/api/v1/tickets'),
  
  myTickets: () => api.get('/api/v1/tickets/my-tickets'),
  
  get: (ticketId: number) => api.get(`/api/v1/tickets/${ticketId}`),
};

export default api;
