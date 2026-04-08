'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { notificationsApi } from '@/lib/api';
import { useAuthStore } from '@/context/auth-store';
import { Bell, CheckCircle, XCircle, MessageCircle, Star, ArrowLeft, CheckCheck } from 'lucide-react';
import { Notification } from '@/types';

export default function Notifications() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    notificationsApi.list()
      .then(res => setNotifications(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return null;
  }

  const getIcon = (type: string) => {
    switch (type) {
      case 'product_approved':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'product_rejected':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'new_message':
        return <MessageCircle className="w-5 h-5 text-blue-500" />;
      case 'new_rating':
        return <Star className="w-5 h-5 text-yellow-500" />;
      default:
        return <Bell className="w-5 h-5 text-muted-foreground" />;
    }
  };

  const handleMarkAllRead = async () => {
    await notificationsApi.markAllRead();
    setNotifications(notifications.map(n => ({ ...n, is_read: true })));
  };

  const handleMarkRead = async (id: number) => {
    await notificationsApi.markRead(id);
    setNotifications(notifications.map(n => n.id === id ? { ...n, is_read: true } : n));
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.back()}
            className="p-2 rounded-full hover:bg-muted transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="font-serif text-3xl text-foreground">Notifications</h1>
            <p className="mt-1 text-muted-foreground">Stay updated on your activity</p>
          </div>
        </div>
        {notifications.some(n => !n.is_read) && (
          <button
            onClick={handleMarkAllRead}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          >
            <CheckCheck className="w-4 h-4" />
            Mark all read
          </button>
        )}
      </div>

      {loading ? (
        <div className="text-center py-12 text-muted-foreground">Loading...</div>
      ) : notifications.length === 0 ? (
        <div className="text-center py-12">
          <Bell className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">No notifications yet</p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map(notification => (
            <div
              key={notification.id}
              onClick={() => !notification.is_read && handleMarkRead(notification.id)}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                notification.is_read
                  ? 'border-border bg-background'
                  : 'border-primary/20 bg-primary/5 hover:bg-primary/10'
              }`}
            >
              <div className="flex items-start gap-4">
                <div className="mt-1">{getIcon(notification.notification_type)}</div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-foreground">{notification.title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground line-clamp-2">{notification.message}</p>
                  <p className="mt-2 text-xs text-muted-foreground">
                    {new Date(notification.created_at).toLocaleString()}
                  </p>
                </div>
                {!notification.is_read && (
                  <div className="w-2 h-2 rounded-full bg-primary" />
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}