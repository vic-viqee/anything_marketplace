'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/context/auth-store';
import { adminApi, productsApi } from '@/lib/api';
import { User, Product, Analytics, Rating, Ticket, ActivityLog, Category, AdminTab, ApiError, Subscription, Report } from '@/types';
import { Users, Package, Check, X, Trash2, AlertCircle, Ticket as TicketIcon, Star, Bell, Search, History, Folder, CreditCard, Flag, ShieldCheck } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';

export const dynamic = 'force-dynamic';

function AdminContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isAdmin, logout } = useAuthStore();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [pendingProducts, setPendingProducts] = useState<Product[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [ratings, setRatings] = useState<Rating[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [userSearch, setUserSearch] = useState('');
  const [newCategory, setNewCategory] = useState('');
  const [activeTab, setActiveTab] = useState<AdminTab>('analytics');
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [broadcastTitle, setBroadcastTitle] = useState('');
  const [broadcastMessage, setBroadcastMessage] = useState('');
  const [unverifiedSellersCount, setUnverifiedSellersCount] = useState(0);

  useEffect(() => {
    if (!isAuthenticated || !isAdmin) {
      router.push('/login');
      return;
    }
    loadData();
  }, [isAuthenticated, isAdmin, router]);

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab) {
      setActiveTab(tab as AdminTab);
    }
  }, [searchParams]);

  const loadData = async () => {
    try {
      const [analyticsRes, productsRes, usersRes] = await Promise.all([
        adminApi.getAnalytics(),
        adminApi.getPendingProducts(),
        adminApi.listUsers(),
      ]);
      setAnalytics(analyticsRes.data);
      setPendingProducts(productsRes.data);
      setUsers(usersRes.data);
    } catch {
      // Silent failure
    } finally {
      setLoading(false);
    }
  };

  const loadRatings = async () => {
    try {
      const res = await adminApi.getAllRatings();
      setRatings(res.data);
    } catch {}
  };

  const loadTickets = async () => {
    try {
      const res = await adminApi.getTickets();
      setTickets(res.data);
    } catch {}
  };

  const loadActivityLogs = async () => {
    try {
      const res = await adminApi.getActivityLogs();
      setActivityLogs(res.data);
    } catch {}
  };

  const loadCategories = async () => {
    try {
      const res = await productsApi.categories();
      setCategories(res.data);
    } catch {}
  };

  const loadSubscriptions = async (tier?: string) => {
    try {
      const res = await adminApi.getSubscriptions({ tier });
      setSubscriptions(res.data);
    } catch {}
  };

  const loadReports = async (status?: string) => {
    try {
      const res = await adminApi.getReports({ status_filter: status });
      setReports(res.data);
    } catch {}
  };

  const handleVerifySeller = async (userId: number) => {
    setActionLoading(userId);
    try {
      await adminApi.verifySeller(userId);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_identity_verified: true } : u));
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to verify seller');
    } finally {
      setActionLoading(null);
    }
  };

  const handleUnverifySeller = async (userId: number) => {
    setActionLoading(userId);
    try {
      await adminApi.unverifySeller(userId);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_identity_verified: false } : u));
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to unverify seller');
    } finally {
      setActionLoading(null);
    }
  };

  const handleUpdateSubscription = async (userId: number, tier: string) => {
    setActionLoading(userId);
    try {
      await adminApi.updateSubscription(userId, tier, 30);
      loadSubscriptions();
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to update subscription');
    } finally {
      setActionLoading(null);
    }
  };

  const handleUpdateReport = async (reportId: number, status: string) => {
    try {
      await adminApi.updateReport(reportId, status);
      loadReports();
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to update report');
    }
  };

  const handleCreateCategory = async () => {
    if (!newCategory.trim()) return;
    setActionLoading(-3);
    try {
      await productsApi.createCategory({ name: newCategory, slug: newCategory.toLowerCase().replace(/\s+/g, '-') });
      setNewCategory('');
      loadCategories();
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to create category');
    } finally {
      setActionLoading(null);
    }
  };

  const handleUserSearch = async () => {
    if (!userSearch.trim()) {
      const res = await adminApi.listUsers();
      setUsers(res.data);
      return;
    }
    setActionLoading(-2);
    try {
      const res = await adminApi.listUsers({ search: userSearch });
      setUsers(res.data);
    } catch {} finally {
      setActionLoading(null);
    }
  };

  useEffect(() => {
    if (activeTab === 'reviews') loadRatings();
    if (activeTab === 'tickets') loadTickets();
    if (activeTab === 'activity') loadActivityLogs();
    if (activeTab === 'categories') loadCategories();
    if (activeTab === 'subscriptions') loadSubscriptions();
    if (activeTab === 'reports') loadReports();
    if (activeTab === 'users') setUnverifiedSellersCount(users.filter(u => u.role === 'seller' && !u.is_identity_verified).length);
  }, [activeTab]);

  const handleBroadcast = async () => {
    if (!broadcastTitle.trim() || !broadcastMessage.trim()) {
      setError('Title and message required');
      return;
    }
    setActionLoading(-1);
    try {
      await adminApi.broadcastNotification({ title: broadcastTitle, message: broadcastMessage });
      setBroadcastTitle('');
      setBroadcastMessage('');
      alert('Broadcast sent!');
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to send');
    } finally {
      setActionLoading(null);
    }
  };

  const handleApprove = async (productId: number) => {
    setActionLoading(productId);
    setError(null);
    try {
      await adminApi.approveProduct(productId);
      setPendingProducts(prev => prev.filter(p => p.id !== productId));
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to approve product');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (productId: number) => {
    setActionLoading(productId);
    setError(null);
    try {
      await adminApi.rejectProduct(productId);
      setPendingProducts(prev => prev.filter(p => p.id !== productId));
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to reject product');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteProduct = async (productId: number) => {
    if (!confirm('Delete this product?')) return;
    setActionLoading(productId);
    setError(null);
    try {
      await adminApi.deleteProduct(productId);
      setPendingProducts(prev => prev.filter(p => p.id !== productId));
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to delete product');
    } finally {
      setActionLoading(null);
    }
  };

  const handleUpdateRole = async (userId: number, role: string) => {
    setActionLoading(userId);
    setError(null);
    try {
      await adminApi.updateUserRole(userId, role);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, role } : u));
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to update role');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeactivate = async (userId: number) => {
    setActionLoading(userId);
    setError(null);
    try {
      await adminApi.deactivateUser(userId);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_active: !u.is_active } : u));
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to update user status');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Delete this user and all their data?')) return;
    setActionLoading(userId);
    setError(null);
    try {
      await adminApi.deleteUser(userId);
      setUsers(prev => prev.filter(u => u.id !== userId));
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to delete user');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteRating = async (ratingId: number) => {
    if (!confirm('Delete this review?')) return;
    setActionLoading(ratingId);
    setError(null);
    try {
      await adminApi.deleteRating(ratingId);
      setRatings(prev => prev.filter(r => r.id !== ratingId));
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to delete rating');
    } finally {
      setActionLoading(null);
    }
  };

  const handleUpdateTicketStatus = async (ticketId: number, status: string) => {
    setActionLoading(ticketId);
    setError(null);
    try {
      await adminApi.updateTicketStatus(ticketId, status);
      setTickets(prev => prev.map(t => t.id === ticketId ? { ...t, status } : t));
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to update ticket');
    } finally {
      setActionLoading(null);
    }
  };

  if (!isAdmin) return null;

  const tabs: Array<{ id: AdminTab; label: string; icon: React.ComponentType<{ className?: string }>; count?: number }> = [
    { id: 'analytics', label: 'Analytics', icon: AlertCircle },
    { id: 'products', label: 'Products', icon: Package },
    { id: 'users', label: 'Users', icon: Users, count: unverifiedSellersCount },
    { id: 'subscriptions', label: 'Subscriptions', icon: CreditCard },
    { id: 'reports', label: 'Reports', icon: Flag, count: reports.filter(r => r.status === 'open').length },
    { id: 'tickets', label: 'Tickets', icon: TicketIcon, count: tickets.filter(t => t.status === 'open').length },
    { id: 'reviews', label: 'Reviews', icon: Star },
    { id: 'broadcast', label: 'Broadcast', icon: Bell },
    { id: 'activity', label: 'Activity', icon: History },
    { id: 'categories', label: 'Categories', icon: Folder },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          {error}
          <button onClick={() => setError(null)} className="ml-2 float-right">×</button>
        </div>
      )}
      <div className="flex justify-between items-center mb-8">
        <h1 className="font-serif text-3xl text-foreground">Admin Dashboard</h1>
        <button onClick={logout} className="text-sm text-muted-foreground hover:text-foreground">
          Logout
        </button>
      </div>

      <div className="flex gap-4 mb-8 border-b border-border overflow-x-auto">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 pb-3 px-2 text-sm font-medium transition-colors whitespace-nowrap ${
              activeTab === tab.id
                ? 'text-foreground border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
            {tab.count !== undefined && tab.count > 0 && (
              <span className="bg-destructive text-destructive-foreground text-xs rounded-full px-1.5">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-20 text-muted-foreground">Loading...</div>
      ) : (
        <>
          {activeTab === 'analytics' && analytics && (
            <div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-card p-6 rounded-lg border border-border">
                  <p className="text-sm text-muted-foreground">Total Users</p>
                  <p className="text-3xl font-semibold text-foreground">{analytics.total_users}</p>
                </div>
                <div className="bg-card p-6 rounded-lg border border-border">
                  <p className="text-sm text-muted-foreground">Total Products</p>
                  <p className="text-3xl font-semibold text-foreground">{analytics.total_products}</p>
                </div>
                <div className="bg-card p-6 rounded-lg border border-border">
                  <p className="text-sm text-muted-foreground">Pending</p>
                  <p className="text-3xl font-semibold text-destructive">{analytics.pending_products}</p>
                </div>
                <div className="bg-card p-6 rounded-lg border border-border">
                  <p className="text-sm text-muted-foreground">Sold</p>
                  <p className="text-3xl font-semibold text-green-600">{analytics.sold_products}</p>
                </div>
                <div className="bg-card p-6 rounded-lg border border-border">
                  <p className="text-sm text-muted-foreground">Customers</p>
                  <p className="text-3xl font-semibold text-foreground">{analytics.customers}</p>
                </div>
                <div className="bg-card p-6 rounded-lg border border-border">
                  <p className="text-sm text-muted-foreground">Sellers</p>
                  <p className="text-3xl font-semibold text-foreground">{analytics.sellers}</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="bg-card p-6 rounded-lg border border-border">
                  <h3 className="text-lg font-medium mb-4">Products by Category</h3>
                  {analytics.products_by_category && analytics.products_by_category.length > 0 ? (
                    <ResponsiveContainer width="100%" height={250}>
                      <PieChart>
                        <Pie data={analytics.products_by_category} dataKey="count" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                          {(analytics.products_by_category || []).map((_, i: number) => (
                            <Cell key={i} fill={['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6'][i % 5]} />
                          ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                      </PieChart>
                    </ResponsiveContainer>
                  ) : <p className="text-muted-foreground text-center py-10">No data</p>}
                </div>
                <div className="bg-card p-6 rounded-lg border border-border">
                  <h3 className="text-lg font-medium mb-4">Users by Role</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={analytics.users_over_time || []}>
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="count" fill="#3b82f6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'products' && (
            <div>
              {pendingProducts.length === 0 ? (
                <div className="text-center py-20 text-muted-foreground">No pending products</div>
              ) : (
                <div className="space-y-4">
                  {pendingProducts.map(product => (
                    <div key={product.id} className="bg-card p-4 rounded-lg border border-border flex justify-between items-center">
                      <div>
                        <h3 className="font-medium text-foreground">{product.title}</h3>
                        <p className="text-sm text-muted-foreground">KES {product.price.toLocaleString()}</p>
                      </div>
                      <div className="flex gap-2">
                        <button 
                          onClick={() => handleApprove(product.id)} 
                          disabled={actionLoading === product.id}
                          className="p-2 text-green-600 hover:bg-green-50 rounded-lg disabled:opacity-50"
                        >
                          <Check className="w-5 h-5" />
                        </button>
                        <button 
                          onClick={() => handleReject(product.id)} 
                          disabled={actionLoading === product.id}
                          className="p-2 text-destructive hover:bg-destructive/10 rounded-lg disabled:opacity-50"
                        >
                          <X className="w-5 h-5" />
                        </button>
                        <button 
                          onClick={() => handleDeleteProduct(product.id)} 
                          disabled={actionLoading === product.id}
                          className="p-2 text-muted-foreground hover:bg-muted rounded-lg disabled:opacity-50"
                        >
                          <Trash2 className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'users' && (
            <div>
              <div className="flex gap-2 mb-4">
                <div className="flex-1 relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <input
                    type="text"
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleUserSearch()}
                    placeholder="Search by phone or username..."
                    className="w-full border rounded-lg pl-10 pr-3 py-2"
                  />
                </div>
                <button onClick={handleUserSearch} disabled={actionLoading === -2} className="px-4 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50">
                  Search
                </button>
              </div>
              <div className="bg-card rounded-lg border border-border overflow-hidden">
                <table className="w-full">
                  <thead className="bg-muted border-b border-border">
                    <tr>
                      <th className="text-left p-4 text-sm font-medium">Phone</th>
                      <th className="text-left p-4 text-sm font-medium">Username</th>
                      <th className="text-left p-4 text-sm font-medium">Role</th>
                      <th className="text-left p-4 text-sm font-medium">Verified</th>
                      <th className="text-left p-4 text-sm font-medium">Status</th>
                      <th className="text-left p-4 text-sm font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map(user => (
                      <tr key={user.id} className="border-b border-border">
                        <td className="p-4 text-sm">{user.phone}</td>
                        <td className="p-4 text-sm">{user.username || '-'}</td>
                        <td className="p-4">
                          <select value={user.role} onChange={(e) => handleUpdateRole(user.id, e.target.value)} className="text-sm border rounded px-2 py-1">
                            <option value="customer">Customer</option>
                            <option value="seller">Seller</option>
                            <option value="admin">Admin</option>
                          </select>
                        </td>
                        <td className="p-4">
                          {user.role === 'seller' && (
                            user.is_identity_verified ? (
                              <button onClick={() => handleUnverifySeller(user.id)} disabled={actionLoading === user.id} className="flex items-center gap-1 text-xs text-green-600 hover:text-green-700 disabled:opacity-50">
                                <Check className="w-4 h-4" /> Verified
                              </button>
                            ) : (
                              <button onClick={() => handleVerifySeller(user.id)} disabled={actionLoading === user.id} className="flex items-center gap-1 px-2 py-1 text-xs bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50">
                                <ShieldCheck className="w-4 h-4" /> Verify
                              </button>
                            )
                          )}
                        </td>
                        <td className="p-4">
                          <span className={`text-sm ${user.is_active ? 'text-green-600' : 'text-destructive'}`}>
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="p-4 flex gap-2">
                          <button onClick={() => handleDeactivate(user.id)} className="p-2 text-muted-foreground hover:bg-muted rounded">
                            {user.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                          <button onClick={() => handleDeleteUser(user.id)} className="p-2 text-destructive hover:bg-destructive/10 rounded">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'tickets' && (
            <div>
              {tickets.length === 0 ? (
                <div className="text-center py-20 text-muted-foreground">No tickets</div>
              ) : (
                <div className="space-y-4">
                  {tickets.map(ticket => (
                    <div key={ticket.id} className="bg-card p-4 rounded-lg border border-border">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium text-foreground">{ticket.ticket_type}</p>
                          <p className="text-sm text-muted-foreground mt-1">{ticket.description}</p>
                          <p className="text-xs text-muted-foreground mt-2">{new Date(ticket.created_at).toLocaleString()}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <select value={ticket.status} onChange={(e) => handleUpdateTicketStatus(ticket.id, e.target.value)} className="text-sm border rounded px-2 py-1">
                            <option value="open">Open</option>
                            <option value="in_progress">In Progress</option>
                            <option value="resolved">Resolved</option>
                            <option value="closed">Closed</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'reviews' && (
            <div>
              {ratings.length === 0 ? (
                <div className="text-center py-20 text-muted-foreground">No reviews</div>
              ) : (
                <div className="space-y-4">
                  {ratings.map(rating => (
                    <div key={rating.id} className="bg-card p-4 rounded-lg border border-border flex justify-between items-center">
                      <div>
                        <div className="flex gap-1">
                          {[...Array(5)].map((_, i) => (
                            <Star key={i} className={`w-4 h-4 ${i < rating.stars ? 'text-yellow-500 fill-yellow-500' : 'text-muted'}`} />
                          ))}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">{rating.comment || 'No comment'}</p>
                        <p className="text-xs text-muted-foreground mt-2">By user {rating.rater_id} for user {rating.rated_user_id}</p>
                      </div>
                      <button onClick={() => handleDeleteRating(rating.id)} className="p-2 text-destructive hover:bg-destructive/10 rounded">
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'broadcast' && (
            <div className="bg-card p-6 rounded-lg border border-border max-w-xl">
              <h3 className="text-lg font-medium mb-4">Broadcast Notification</h3>
              <p className="text-sm text-muted-foreground mb-4">Send notification to all users.</p>
              <div className="space-y-4">
                <input
                  type="text"
                  value={broadcastTitle}
                  onChange={(e) => setBroadcastTitle(e.target.value)}
                  placeholder="Title"
                  className="w-full border rounded-lg px-3 py-2"
                />
                <textarea
                  value={broadcastMessage}
                  onChange={(e) => setBroadcastMessage(e.target.value)}
                  placeholder="Message"
                  rows={4}
                  className="w-full border rounded-lg px-3 py-2"
                />
                <button
                  onClick={handleBroadcast}
                  disabled={actionLoading === -1}
                  className="w-full py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50"
                >
                  {actionLoading === -1 ? 'Sending...' : 'Send to All Users'}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'activity' && (
            <div>
              {activityLogs.length === 0 ? (
                <div className="text-center py-20 text-muted-foreground">No activity logs</div>
              ) : (
                <div className="space-y-2">
                  {activityLogs.map((log: ActivityLog) => (
                    <div key={log.id} className="bg-card p-3 rounded-lg border border-border text-sm">
                      <span className="text-muted-foreground">{new Date(log.created_at).toLocaleString()}</span>
                      <span className="mx-2">•</span>
                      <span className="font-medium">{log.action}</span>
                      <span className="text-muted-foreground mx-2">by user {log.user_id}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'categories' && (
            <div>
              <div className="flex gap-2 mb-6">
                <input
                  type="text"
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleCreateCategory()}
                  placeholder="New category name..."
                  className="flex-1 border rounded-lg px-3 py-2"
                />
                <button onClick={handleCreateCategory} disabled={actionLoading === -3} className="px-4 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50">
                  Add
                </button>
              </div>
              {categories.length === 0 ? (
                <div className="text-center py-20 text-muted-foreground">No categories</div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {categories.map((cat: Category) => (
                    <div key={cat.id} className="bg-card px-4 py-2 rounded-lg border border-border">
                      <span className="text-foreground">{cat.name}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'subscriptions' && (
            <div>
              <h2 className="text-xl font-medium mb-4">Subscriptions</h2>
              <div className="mb-4">
                <select onChange={(e) => loadSubscriptions(e.target.value || undefined)} className="border rounded-lg px-3 py-2">
                  <option value="">All Tiers</option>
                  <option value="free">Free</option>
                  <option value="basic">Basic</option>
                  <option value="standard">Standard</option>
                  <option value="premium">Premium</option>
                </select>
              </div>
              {subscriptions.length === 0 ? (
                <div className="text-center py-20 text-muted-foreground">No subscriptions found</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left p-2">User</th>
                        <th className="text-left p-2">Tier</th>
                        <th className="text-left p-2">Featured Used</th>
                        <th className="text-left p-2">Verified</th>
                        <th className="text-left p-2">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {subscriptions.map((sub) => (
                        <tr key={sub.id} className="border-b">
                          <td className="p-2">@{sub.username || sub.phone}</td>
                          <td className="p-2">
                            <select value={sub.subscription_tier} onChange={(e) => handleUpdateSubscription(sub.id, e.target.value)} className="border rounded px-2 py-1">
                              <option value="free">Free</option>
                              <option value="basic">Basic</option>
                              <option value="standard">Standard</option>
                              <option value="premium">Premium</option>
                            </select>
                          </td>
                          <td className="p-2">{sub.featured_listings_used}</td>
                          <td className="p-2">{sub.is_verified ? '✓' : '—'}</td>
                          <td className="p-2">
                            {sub.is_verified ? (
                              <button onClick={() => handleUpdateSubscription(sub.id, 'free')} className="text-xs text-red-500">Revoke</button>
                            ) : (
                              <button onClick={() => handleUpdateSubscription(sub.id, 'standard')} className="text-xs text-green-500">Verify</button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {activeTab === 'reports' && (
            <div>
              <h2 className="text-xl font-medium mb-4">User Reports</h2>
              <div className="mb-4">
                <select onChange={(e) => loadReports(e.target.value || undefined)} className="border rounded-lg px-3 py-2">
                  <option value="">All Status</option>
                  <option value="open">Open</option>
                  <option value="investigating">Investigating</option>
                  <option value="resolved">Resolved</option>
                  <option value="dismissed">Dismissed</option>
                </select>
              </div>
              {reports.length === 0 ? (
                <div className="text-center py-20 text-muted-foreground">No reports</div>
              ) : (
                <div className="space-y-4">
                  {reports.map((report) => (
                    <div key={report.id} className="bg-card p-4 rounded-lg border border-border">
                      <div className="flex justify-between items-start">
                        <div>
                          <span className="inline-block px-2 py-1 text-xs rounded-full bg-red-100 text-red-700 mr-2">{report.reason}</span>
                          <span className="inline-block px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700">{report.status}</span>
                        </div>
                        <span className="text-sm text-muted-foreground">{new Date(report.created_at).toLocaleDateString()}</span>
                      </div>
                      {report.description && <p className="mt-2 text-sm">{report.description}</p>}
                      <div className="mt-3 flex gap-2">
                        <button onClick={() => handleUpdateReport(report.id, 'investigating')} className="px-3 py-1 text-xs bg-yellow-500 text-white rounded">Investigate</button>
                        <button onClick={() => handleUpdateReport(report.id, 'resolved')} className="px-3 py-1 text-xs bg-green-500 text-white rounded">Resolve</button>
                        <button onClick={() => handleUpdateReport(report.id, 'dismissed')} className="px-3 py-1 text-xs bg-gray-500 text-white rounded">Dismiss</button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default function AdminDashboard() {
  return (
    <Suspense fallback={<div className="max-w-6xl mx-auto px-4 py-8 text-center">Loading...</div>}>
      <AdminContent />
    </Suspense>
  );
}
