import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isSeller: boolean;
  isAdmin: boolean;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isSeller: false,
      isAdmin: false,
      setAuth: (user, token) => {
        localStorage.setItem('access_token', token);
        set({ 
          user, 
          token, 
          isAuthenticated: true,
          isSeller: user.role === 'seller',
          isAdmin: user.role === 'admin',
        });
      },
      logout: () => {
        localStorage.removeItem('access_token');
        set({ user: null, token: null, isAuthenticated: false, isSeller: false, isAdmin: false });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, token: state.token, isAuthenticated: state.isAuthenticated, isSeller: state.isSeller, isAdmin: state.isAdmin }),
    }
  )
);
