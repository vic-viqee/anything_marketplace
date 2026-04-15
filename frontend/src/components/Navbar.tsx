'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, PlusCircle, MessageCircle, User, LogIn, Settings, Menu, X, Sun, Moon, Bell } from 'lucide-react';
import { useAuthStore } from '@/context/auth-store';
import { useTheme } from '@/context/theme';
import { authApi, notificationsApi } from '@/lib/api';

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const pathname = usePathname();
  const menuRef = useRef<HTMLDivElement>(null);
  const { isAuthenticated, setAuth, logout, isSeller, isAdmin } = useAuthStore();
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token && !isAuthenticated) {
      authApi.me()
        .then(res => setAuth(res.data, token))
        .catch(() => logout());
    }
  }, [isAuthenticated, setAuth, logout]);

  useEffect(() => {
    if (!isAuthenticated) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setUnreadCount(0);
      return;
    }
    notificationsApi.unreadCount()
      .then(res => setUnreadCount(res.data.unread_count))
      .catch(() => {});
  }, [isAuthenticated]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMenuOpen) {
        setIsMenuOpen(false);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isMenuOpen]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setIsMenuOpen(false);
  }, [pathname]);

  const navLinks = [
    { href: '/', label: 'Feed', icon: Home },
  ];

  if (isSeller) {
    navLinks.push({ href: '/post', label: 'Post Ad', icon: PlusCircle });
    navLinks.push({ href: '/my-products', label: 'My Products', icon: PlusCircle });
  }

  const authLinks = isAuthenticated
    ? [
        { href: '/messages', label: 'Messages', icon: MessageCircle },
        { href: '/notifications', label: 'Notifications', icon: Bell, badge: unreadCount },
        ...(isAdmin ? [{ href: '/admin', label: 'Admin', icon: Settings }] : []),
        { href: '/profile', label: 'Profile', icon: User },
      ]
    : [
        { href: '/login', label: 'Login', icon: LogIn },
      ];

  return (
    <nav className="sticky top-0 z-50 bg-card border-b border-border" aria-label="Main navigation">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl font-bold tracking-tight text-foreground">
              Anything
            </span>
          </Link>

          <div className="hidden md:flex items-center gap-6">
            {navLinks.map(link => (
              <Link
                key={link.href}
                href={link.href}
                className={`text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background rounded px-2 py-1 ${
                  pathname === link.href
                    ? 'text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {link.label}
              </Link>
            ))}
            {authLinks.map(link => {
              const Icon = link.icon;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background rounded px-2 py-1 flex items-center gap-1 ${
                    pathname === link.href
                      ? 'text-foreground'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {link.label}
                  {'badge' in link && link.badge && link.badge > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 text-xs font-medium bg-destructive text-destructive-foreground rounded-full">
                      {link.badge}
                    </span>
                  )}
                </Link>
              );
            })}
            <button
              onClick={toggleTheme}
              className="p-2 text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-full"
              aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
            >
              {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            </button>
          </div>

          <button
            className="md:hidden p-3 min-w-[44px] min-h-[44px] flex items-center justify-center"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-expanded={isMenuOpen}
            aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
            aria-controls="mobile-menu"
          >
            {isMenuOpen ? (
              <X className="w-6 h-6 text-foreground" />
            ) : (
              <Menu className="w-6 h-6 text-foreground" />
            )}
          </button>
        </div>
      </div>

      {isMenuOpen && (
        <div 
          id="mobile-menu"
          ref={menuRef}
          className="md:hidden border-t border-border"
          role="menu"
        >
          <div className="px-4 py-3 space-y-1">
            {navLinks.map(link => (
              <Link
                key={link.href}
                href={link.href}
                className="block py-3 px-2 text-sm font-medium text-foreground rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                role="menuitem"
                onClick={() => setIsMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            {authLinks.map(link => {
              const Icon = link.icon;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className="flex items-center justify-between py-3 px-2 text-sm font-medium text-foreground rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  role="menuitem"
                  onClick={() => setIsMenuOpen(false)}
                >
                  <span className="flex items-center gap-2">
                    <Icon className="w-4 h-4" />
                    {link.label}
                  </span>
                  {'badge' in link && link.badge && link.badge > 0 && (
                    <span className="px-2 py-0.5 text-xs font-medium bg-destructive text-destructive-foreground rounded-full">
                      {link.badge}
                    </span>
                  )}
                </Link>
              );
            })}
            <button
              onClick={() => { toggleTheme(); setIsMenuOpen(false); }}
              className="flex items-center gap-2 w-full py-3 px-2 text-sm font-medium text-foreground rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
              {theme === 'light' ? 'Dark Mode' : 'Light Mode'}
            </button>
          </div>
        </div>
      )}
    </nav>
  );
}
