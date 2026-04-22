import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/types';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isSeller: boolean;
  isAdmin: boolean;
  pendingKyc: boolean;
  kycStatus: string;
  isVerified: boolean;
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
      pendingKyc: false,
      kycStatus: 'none',
      isVerified: false,
      setAuth: (user, token) => {
        localStorage.setItem('access_token', token);
        set({ 
          user, 
          token, 
          isAuthenticated: true,
          isSeller: user.role === 'seller',
          isAdmin: user.role === 'admin',
          pendingKyc: user.pending_kyc || false,
          kycStatus: user.kyc_status || 'none',
          isVerified: user.is_verified || false,
        });
      },
      logout: () => {
        localStorage.removeItem('access_token');
        set({ user: null, token: null, isAuthenticated: false, isSeller: false, isAdmin: false, pendingKyc: false, kycStatus: 'none', isVerified: false });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, token: state.token, isAuthenticated: state.isAuthenticated, isSeller: state.isSeller, isAdmin: state.isAdmin, pendingKyc: state.pendingKyc, kycStatus: state.kycStatus, isVerified: state.isVerified }),
    }
  )
);
