'use client';

import { useState, useRef, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/context/auth-store';
import { authApi, ticketsApi } from '@/lib/api';
import { ApiError } from '@/types';
import { LogOut, User, Settings, Camera, Shield, Star, Crown, Zap, CreditCard, CheckCircle, Clock, XCircle } from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function compressImage(file: File): Promise<Blob> {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        const maxWidth = 400;
        const scale = maxWidth / img.width;
        const width = maxWidth;
        const height = img.height * scale;
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        ctx?.drawImage(img, 0, 0, width, height);
        canvas.toBlob((blob) => {
          resolve(blob || new Blob());
        }, 'image/jpeg', 0.85);
      };
      img.src = e.target?.result as string;
    };
    reader.readAsDataURL(file);
  });
}

function ProfileContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, logout, setAuth } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'profile' | 'account' | 'subscription'>('profile');
  const [username, setUsername] = useState(user?.username || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [contactAdminLoading, setContactAdminLoading] = useState(false);
  const [upgradingToSeller, setUpgradingToSeller] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (searchParams.get('tab') === 'subscription') {
      setActiveTab('subscription');
    }
    if (searchParams.get('upgrade') === 'true' && user?.role !== 'seller') {
      setActiveTab('subscription');
    }
  }, [searchParams, user]);

  const tierConfig: Record<string, { name: string; icon: React.ReactNode; color: string; bgColor: string }> = {
    free: { name: 'Free', icon: <Shield className="w-5 h-5" />, color: 'text-muted-foreground', bgColor: 'bg-muted' },
    basic: { name: 'Basic', icon: <Zap className="w-5 h-5" />, color: 'text-orange-500', bgColor: 'bg-orange-500/20' },
    standard: { name: 'Standard', icon: <Star className="w-5 h-5" />, color: 'text-blue-500', bgColor: 'bg-blue-500/20' },
    premium: { name: 'Premium', icon: <Crown className="w-5 h-5" />, color: 'text-amber-500', bgColor: 'bg-amber-500/20' },
  };

  const currentTier = user?.subscription_tier || 'free';
  const tier = tierConfig[currentTier] || tierConfig.free;

  const handleContactAdmin = async () => {
    setContactAdminLoading(true);
    setError('');
    setSuccess('');
    try {
      await ticketsApi.create({
        ticket_type: 'subscription_request',
        description: `I would like to upgrade my subscription from ${tierConfig[currentTier]?.name || 'Free'} to Standard plan. Please contact me with the payment details.`,
      });
      setSuccess('Your request has been sent. We will contact you shortly.');
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to send request');
    } finally {
      setContactAdminLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/');
    router.refresh();
  };

  const handleUpgradeToSeller = async () => {
    setUpgradingToSeller(true);
    setError('');
    setSuccess('');
    try {
      const res = await authApi.updateMe({ upgrade_to_seller: true });
      setSuccess('You are now a seller! You can now post products.');
      const token = localStorage.getItem('access_token');
      if (token) {
        setAuth(res.data, token);
      }
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to upgrade to seller');
    } finally {
      setUpgradingToSeller(false);
    }
  };

  const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setUploadingImage(true);
    try {
      const compressed = await compressImage(file);
      const compressedFile = new File([compressed], 'profile.jpg', { type: 'image/jpeg' });
      const res = await authApi.uploadProfileImage(compressedFile);
      setSuccess('Profile photo updated');
      const token = localStorage.getItem('access_token');
      if (token) {
        setAuth(res.data, token);
      }
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to upload image');
    } finally {
      setUploadingImage(false);
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      const res = await authApi.updateMe({ username: username || undefined });
      setSuccess('Profile updated successfully');
      const token = localStorage.getItem('access_token');
      if (token) {
        setAuth(res.data, token);
      }
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!currentPassword) {
      setError('Please enter your current password');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('New passwords do not match');
      return;
    }

    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    setLoading(true);
    try {
      await authApi.updateMe({ password: newPassword, current_password: currentPassword });
      setSuccess('Password updated successfully');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr.response?.data?.detail || 'Failed to update password');
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8 text-center">
        <p className="text-muted-foreground">Please login to view your profile</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="font-serif text-3xl text-foreground mb-8">Settings</h1>
      
      <div className="flex gap-4 mb-8 border-b border-border">
        <button
          onClick={() => setActiveTab('profile')}
          className={`flex items-center gap-2 pb-3 px-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
            activeTab === 'profile'
              ? 'text-foreground border-b-2 border-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <User className="w-4 h-4" />
          Profile
        </button>
        {user?.role === 'seller' && (
          <button
            onClick={() => setActiveTab('subscription')}
            className={`flex items-center gap-2 pb-3 px-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
              activeTab === 'subscription'
                ? 'text-foreground border-b-2 border-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <CreditCard className="w-4 h-4" />
            Subscription
          </button>
        )}
        <button
          onClick={() => setActiveTab('account')}
          className={`flex items-center gap-2 pb-3 px-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
            activeTab === 'account'
              ? 'text-foreground border-b-2 border-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Settings className="w-4 h-4" />
          Account
        </button>
      </div>

      {activeTab === 'profile' && (
        <div className="space-y-6">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageUpload}
            accept="image/*"
            className="hidden"
          />
          <div className="flex items-center gap-6 mb-8">
            <div className="w-24 h-24 rounded-full bg-muted flex items-center justify-center overflow-hidden">
              {user?.profile_image ? (
                <img
                  src={`${API_URL}/uploads/${user.profile_image}`}
                  alt="Profile"
                  className="w-full h-full object-cover"
                />
              ) : (
                <User className="w-10 h-10 text-muted-foreground" />
              )}
            </div>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadingImage}
              className="flex items-center gap-2 px-4 py-2 border border-input rounded-lg text-sm text-foreground hover:bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
            >
              <Camera className="w-4 h-4" />
              {uploadingImage ? 'Uploading...' : 'Change Photo'}
            </button>
          </div>

          <form onSubmit={handleUpdateProfile} className="space-y-4">
            {error && (
              <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
                {error}
              </div>
            )}
            {success && (
              <div className="p-4 bg-green-100 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-green-700 dark:text-green-400 text-sm">
                {success}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Phone Number
              </label>
              <input
                type="text"
                value={user.phone}
                disabled
                className="w-full px-4 py-3 rounded-lg border border-input bg-muted text-muted-foreground cursor-not-allowed"
              />
              <p className="text-xs text-muted-foreground mt-1">Phone number cannot be changed</p>
            </div>

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

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">
                Role
              </label>
              <input
                type="text"
                value={user.role}
                disabled
                className="w-full px-4 py-3 rounded-lg border border-input bg-muted text-muted-foreground capitalize cursor-not-allowed"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </form>
        </div>
      )}

      {activeTab === 'account' && (
        <form onSubmit={handleUpdatePassword} className="space-y-4">
          {error && (
            <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="p-4 bg-green-100 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-green-700 dark:text-green-400 text-sm">
              {success}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Current Password
            </label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-0 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              placeholder="••••••••"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              New Password
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-0 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              placeholder="••••••••"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Confirm New Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-0 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            {loading ? 'Updating...' : 'Update Password'}
          </button>

          <div className="pt-6 border-t border-border">
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 w-full justify-center px-4 py-3 bg-destructive text-destructive-foreground rounded-lg hover:bg-destructive/90 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </form>
      )}

      {activeTab === 'subscription' && (
        <div className="space-y-6">
          {error && (
            <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
              {error}
            </div>
          )}
          {success && (
            <div className="p-4 bg-green-100 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg text-green-700 dark:text-green-400 text-sm">
              {success}
            </div>
          )}

          {user?.role !== 'seller' && (
            <div className="border border-yellow-500/30 bg-yellow-500/10 rounded-xl p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 rounded-xl bg-yellow-500/20">
                  <Star className="w-5 h-5 text-yellow-600" />
                </div>
                <div>
                  <h3 className="text-xl font-medium text-foreground">Become a Seller</h3>
                  <p className="text-sm text-muted-foreground">Start selling on the marketplace</p>
                </div>
              </div>
              <button
                onClick={handleUpgradeToSeller}
                disabled={upgradingToSeller}
                className="w-full py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {upgradingToSeller ? 'Upgrading...' : 'Upgrade to Seller'}
              </button>
            </div>
          )}

          <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-border rounded-xl p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className={`p-3 rounded-xl ${tier.bgColor}`}>
                <span className={tier.color}>{tier.icon}</span>
              </div>
              <div>
                <h3 className="text-xl font-medium text-foreground">{tier.name} Plan</h3>
                <p className="text-sm text-muted-foreground">Your current subscription</p>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Featured listings</span>
                <span className="text-foreground font-medium">
                  {user?.featured_listings_used || 0} / {user?.featured_listings_limit || 0}
                </span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div
                  className="bg-primary h-2 rounded-full transition-all"
                  style={{
                    width: `${Math.min(((user?.featured_listings_used || 0) / (user?.featured_listings_limit || 1)) * 100, 100)}%`
                  }}
                />
              </div>
            </div>
          </div>

          <div className="border border-border rounded-xl p-6">
            <h4 className="font-medium text-foreground mb-4">Identity Verification (KYC)</h4>
            {user?.kyc_status === 'approved' ? (
              <div className="flex items-center gap-3 text-green-600">
                <CheckCircle className="w-5 h-5" />
                <span>Verified - Your identity has been confirmed</span>
              </div>
            ) : user?.kyc_status === 'pending' ? (
              <div className="flex items-center gap-3 text-yellow-600">
                <Clock className="w-5 h-5" />
                <span>Pending review - We will notify you once verified</span>
              </div>
            ) : user?.kyc_status === 'rejected' ? (
              <div className="flex items-center gap-3 text-red-600">
                <XCircle className="w-5 h-5" />
                <span>Verification rejected - Please resubmit your documents</span>
              </div>
            ) : (
              <div className="flex items-center gap-3 text-muted-foreground">
                <Clock className="w-5 h-5" />
                <span>Not submitted - Upload your ID to get verified</span>
              </div>
            )}
          </div>

          <div className="border border-border rounded-xl p-6">
            <h4 className="font-medium text-foreground mb-2">Upgrade Your Plan</h4>
            <p className="text-sm text-muted-foreground mb-4">
              Get more featured listings, verified badge, and priority support.
            </p>
            <button
              onClick={handleContactAdmin}
              disabled={contactAdminLoading}
              className="w-full py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {contactAdminLoading ? 'Sending...' : 'Contact Admin to Upgrade'}
            </button>
          </div>

          <div className="border border-border rounded-xl p-6">
            <h4 className="font-medium text-foreground mb-4">Plan Comparison</h4>
            <div className="space-y-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Featured listings</span>
                <div className="flex gap-4">
                  <span>Free: 0</span>
                  <span>Basic: 1</span>
                  <span className="text-primary font-medium">Standard: 3</span>
                  <span>Premium: 5</span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Verified badge</span>
                <div className="flex gap-4">
                  <span>-</span>
                  <span>-</span>
                  <span className="text-primary font-medium">Yes</span>
                  <span>Yes</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Profile() {
  return (
    <Suspense fallback={<div className="max-w-2xl mx-auto px-4 py-8 text-center"><p className="text-muted-foreground">Loading...</p></div>}>
      <ProfileContent />
    </Suspense>
  );
}
