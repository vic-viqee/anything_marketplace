'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/context/auth-store';
import { adminApi } from '@/lib/api';
import { User, Product, Analytics } from '@/types';
import { Users, Package, Check, X, Trash2, AlertCircle, Ticket, Star, MessageCircle } from 'lucide-react';

export const dynamic = 'force-dynamic';

function AdminContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, isAdmin, logout } = useAuthStore();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [pendingProducts, setPendingProducts] = useState<Product[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [ratings, setRatings] = useState<any[]>([]);
  const [tickets, setTickets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'analytics' | 'products' | 'users' | 'tickets' | 'reviews'>('analytics');

  useEffect(() => {
    if (!isAuthenticated || !isAdmin) {
      router.push('/login');
      return;
    }
    loadData();
  }, [isAuthenticated, isAdmin]);

  useEffect(() => {
    const tab = searchParams.get('tab');
    if (tab) {
      setActiveTab(tab as any);
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

  useEffect(() => {
    if (activeTab === 'reviews') loadRatings();
    if (activeTab === 'tickets') loadTickets();
  }, [activeTab]);

  const handleApprove = async (productId: number) => {
    try {
      await adminApi.approveProduct(productId);
      setPendingProducts(prev => prev.filter(p => p.id !== productId));
    } catch {}
  };

  const handleReject = async (productId: number) => {
    try {
      await adminApi.rejectProduct(productId);
      setPendingProducts(prev => prev.filter(p => p.id !== productId));
    } catch {}
  };

  const handleDeleteProduct = async (productId: number) => {
    if (!confirm('Delete this product?')) return;
    try {
      await adminApi.deleteProduct(productId);
      setPendingProducts(prev => prev.filter(p => p.id !== productId));
    } catch {}
  };

  const handleUpdateRole = async (userId: number, role: string) => {
    try {
      await adminApi.updateUserRole(userId, role);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, role } : u));
    } catch {}
  };

  const handleDeactivate = async (userId: number) => {
    try {
      await adminApi.deactivateUser(userId);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_active: !u.is_active } : u));
    } catch {}
  };

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Delete this user and all their data?')) return;
    try {
      await adminApi.deleteUser(userId);
      setUsers(prev => prev.filter(u => u.id !== userId));
    } catch {}
  };

  const handleDeleteRating = async (ratingId: number) => {
    if (!confirm('Delete this review?')) return;
    try {
      await adminApi.deleteRating(ratingId);
      setRatings(prev => prev.filter(r => r.id !== ratingId));
    } catch {}
  };

  const handleUpdateTicketStatus = async (ticketId: number, status: string) => {
    try {
      await adminApi.updateTicketStatus(ticketId, status);
      setTickets(prev => prev.map(t => t.id === ticketId ? { ...t, status } : t));
    } catch {}
  };

  if (!isAdmin) return null;

  const tabs = [
    { id: 'analytics', label: 'Analytics', icon: AlertCircle },
    { id: 'products', label: 'Products', icon: Package },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'tickets', label: 'Tickets', icon: Ticket, count: tickets.filter(t => t.status === 'open').length },
    { id: 'reviews', label: 'Reviews', icon: Star },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
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
            onClick={() => setActiveTab(tab.id as any)}
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
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-card p-6 rounded-lg border border-border">
                <p className="text-sm text-muted-foreground">Total Users</p>
                <p className="text-3xl font-semibold text-foreground">{analytics.total_users}</p>
              </div>
              <div className="bg-card p-6 rounded-lg border border-border">
                <p className="text-sm text-muted-foreground">Total Products</p>
                <p className="text-3xl font-semibold text-foreground">{analytics.total_products}</p>
              </div>
              <div className="bg-card p-6 rounded-lg border border-border">
                <p className="text-sm text-muted-foreground">Pending Approval</p>
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
                        <button onClick={() => handleApprove(product.id)} className="p-2 text-green-600 hover:bg-green-50 rounded-lg">
                          <Check className="w-5 h-5" />
                        </button>
                        <button onClick={() => handleReject(product.id)} className="p-2 text-destructive hover:bg-destructive/10 rounded-lg">
                          <X className="w-5 h-5" />
                        </button>
                        <button onClick={() => handleDeleteProduct(product.id)} className="p-2 text-muted-foreground hover:bg-muted rounded-lg">
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
            <div className="bg-card rounded-lg border border-border overflow-hidden">
              <table className="w-full">
                <thead className="bg-muted border-b border-border">
                  <tr>
                    <th className="text-left p-4 text-sm font-medium">Phone</th>
                    <th className="text-left p-4 text-sm font-medium">Username</th>
                    <th className="text-left p-4 text-sm font-medium">Role</th>
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
