'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/context/auth-store';
import PhoneInput from '@/components/PhoneInput';
import PasswordInput from '@/components/PasswordInput';

export default function Register() {
  const [phone, setPhone] = useState('+254');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('customer');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { setAuth } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      setLoading(false);
      return;
    }

    try {
      const res = await authApi.register({ phone, username, password, role });
      const { access_token } = res.data;
      
      localStorage.setItem('access_token', access_token);
      const meRes = await authApi.me();
      setAuth(meRes.data, access_token);
      
      router.push('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="font-serif text-3xl text-foreground">Create Account</h1>
          <p className="mt-2 text-muted-foreground">Join Anything Marketplace</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
              {error}
            </div>
          )}

          <PhoneInput label="Phone Number" value={phone} onChange={setPhone} />

            <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-0 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              placeholder="yourname"
            />
          </div>

          <PasswordInput label="Password" value={password} onChange={setPassword} />

          <PasswordInput label="Confirm Password" value={confirmPassword} onChange={setConfirmPassword} />

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              I want to...
            </label>
            <div className="grid grid-cols-2 gap-4">
              <label className={`flex flex-col items-center p-4 rounded-lg border-2 cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
                role === 'customer' ? 'border-primary bg-primary/5' : 'border-input hover:border-primary/50'
              }`}>
                <input
                  type="radio"
                  name="role"
                  value="customer"
                  checked={role === 'customer'}
                  onChange={(e) => setRole(e.target.value)}
                  className="sr-only"
                />
                <span className="font-medium text-foreground">Buy things</span>
                <span className="text-xs text-muted-foreground mt-1">Browse & purchase</span>
              </label>
              <label className={`flex flex-col items-center p-4 rounded-lg border-2 cursor-pointer transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
                role === 'seller' ? 'border-primary bg-primary/5' : 'border-input hover:border-primary/50'
              }`}>
                <input
                  type="radio"
                  name="role"
                  value="seller"
                  checked={role === 'seller'}
                  onChange={(e) => setRole(e.target.value)}
                  className="sr-only"
                />
                <span className="font-medium text-foreground">Sell things</span>
                <span className="text-xs text-muted-foreground mt-1">Post & sell products</span>
              </label>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account?{' '}
          <Link href="/login" className="text-primary font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
