'use client';

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ApiError, SUBSCRIPTION_TIERS, SubscriptionTier } from '@/types';
import { authApi } from '@/lib/api';
import { useAuthStore } from '@/context/auth-store';
import PhoneInput from '@/components/PhoneInput';
import PasswordInput from '@/components/PasswordInput';
import { Upload, ArrowLeft, Star, Shield } from 'lucide-react';

export default function Register() {
  const [step, setStep] = useState(1);
  const [phone, setPhone] = useState('+254');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState<'customer' | 'seller'>('customer');
  const [subscriptionTier, setSubscriptionTier] = useState<SubscriptionTier>('free');
  const [kycIdFront, setKycIdFront] = useState<File | null>(null);
  const [kycSelfie, setKycSelfie] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const { setAuth } = useAuthStore();
  const idFrontRef = useRef<HTMLInputElement>(null);
  const selfieRef = useRef<HTMLInputElement>(null);

  const handleBasicSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }

    if (role === 'customer') {
      handleRegister();
    } else {
      setStep(2);
    }
  };

  const handleTierSelect = (tier: SubscriptionTier) => {
    setSubscriptionTier(tier);
  };

  const handleTierContinue = () => {
    console.log('handleTierContinue called, tier:', subscriptionTier);
    if (subscriptionTier !== 'free') {
      setStep(3);
    } else {
      console.log('Calling handleRegister');
      handleRegister();
    }
  };

  const handleKycSubmit = async () => {
    if (!kycIdFront || !kycSelfie) {
      setError('Please upload both ID document and selfie');
      return;
    }
    await handleRegister();
  };

  const handleRegister = async () => {
    console.log('handleRegister called, role:', role, 'tier:', subscriptionTier);
    setError('');
    setLoading(true);

    try {
      const res = await authApi.register({ phone, username, password, role, subscription_tier: subscriptionTier });
      console.log('Registration successful:', res.data);
      const { access_token, user } = res.data;

      localStorage.setItem('access_token', access_token);

      if (role === 'seller' && kycIdFront && kycSelfie) {
        try {
          await authApi.uploadKYC(kycIdFront, kycSelfie);
        } catch {
          // KYC upload failed, but account was created
        }
      }

      setAuth(user, access_token);
      router.push('/');
    } catch (err) {
      console.error('Registration failed:', err);
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Registration failed');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 py-8">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <h1 className="font-serif text-3xl text-foreground">
            {step === 1 ? 'Create Account' : step === 2 ? 'Choose Your Plan' : 'Verify Identity'}
          </h1>
          <p className="mt-2 text-muted-foreground">
            {step === 1 ? 'Join Anything Marketplace' : step === 2 ? 'Select a subscription tier' : 'Upload ID for verification'}
          </p>
        </div>

        <div className="flex items-center justify-center gap-2 mb-8">
          {[1, 2, 3].map((s) => (
            <div key={s} className={`w-3 h-3 rounded-full ${s <= step ? 'bg-primary' : 'bg-muted'}`} />
          ))}
        </div>

        {step === 1 && (
          <form onSubmit={handleBasicSubmit} className="space-y-6">
            {error && (
              <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
                {error}
              </div>
            )}

            <PhoneInput label="Phone Number" value={phone} onChange={setPhone} />

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground focus:border-primary focus:ring-0"
                placeholder="yourname"
              />
            </div>

            <PasswordInput label="Password" value={password} onChange={setPassword} />
            <PasswordInput label="Confirm Password" value={confirmPassword} onChange={setConfirmPassword} />

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">I want to...</label>
              <div className="grid grid-cols-2 gap-4">
                <label className={`flex flex-col items-center p-4 rounded-lg border-2 cursor-pointer transition-colors ${role === 'customer' ? 'border-primary bg-primary/5' : 'border-input hover:border-primary/50'}`}>
                  <input type="radio" name="role" value="customer" checked={role === 'customer'} onChange={() => setRole('customer')} className="sr-only" />
                  <span className="font-medium text-foreground">Buy things</span>
                  <span className="text-xs text-muted-foreground mt-1">Browse & purchase</span>
                </label>
                <label className={`flex flex-col items-center p-4 rounded-lg border-2 cursor-pointer transition-colors ${role === 'seller' ? 'border-primary bg-primary/5' : 'border-input hover:border-primary/50'}`}>
                  <input type="radio" name="role" value="seller" checked={role === 'seller'} onChange={() => setRole('seller')} className="sr-only" />
                  <span className="font-medium text-foreground">Sell things</span>
                  <span className="text-xs text-muted-foreground mt-1">Post & sell products</span>
                </label>
              </div>
            </div>

            <button type="submit" disabled={loading} className="w-full py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors">
              {loading ? 'Creating account...' : role === 'customer' ? 'Create Account' : 'Continue'}
            </button>
          </form>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <button onClick={() => setStep(1)} className="flex items-center gap-2 text-muted-foreground hover:text-foreground">
              <ArrowLeft className="w-4 h-4" /> Back
            </button>

            <div className="space-y-4">
              {SUBSCRIPTION_TIERS.map((tier) => (
                <div
                  key={tier.tier}
                  onClick={() => handleTierSelect(tier.tier)}
                  className={`p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                    subscriptionTier === tier.tier ? 'border-primary bg-primary/5' : 'border-input hover:border-primary/50'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-medium text-foreground flex items-center gap-2">
                        {tier.tier === 'premium' && <Star className="w-4 h-4 text-yellow-500" />}
                        {tier.tier === 'standard' && <Shield className="w-4 h-4 text-blue-500" />}
                        {tier.name}
                        {tier.tier === 'free' && <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">Current</span>}
                      </h3>
                      <p className="text-sm text-muted-foreground mt-1">
                        {tier.featuredLimit > 0 ? `${tier.featuredLimit} featured listings/month` : tier.featuredLimit === -1 ? 'Unlimited featured listings' : 'No featured listings'}
                        {tier.hasVerifiedBadge && ' • Verified badge'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-medium text-foreground">KES {tier.price.toLocaleString()}</p>
                      {tier.price > 0 && <span className="text-xs text-muted-foreground">/month</span>}
                    </div>
                  </div>
                  {subscriptionTier === tier.tier && (
                    <div className="mt-3 pt-3 border-t border-primary/20">
                      {tier.tier === 'free' ? (
                        <p className="text-sm text-muted-foreground">You can upgrade later from your profile.</p>
                      ) : (
                        <button onClick={(e) => { e.stopPropagation(); handleTierContinue(); }} className="w-full py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium">
                          Contact Admin for Approval
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex gap-4">
              <button type="button" onClick={handleTierContinue} disabled={loading} className="flex-1 py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors">
                {loading ? 'Processing...' : subscriptionTier === 'free' ? 'Continue with Free' : 'Contact Admin'}
              </button>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <button onClick={() => setStep(2)} className="flex items-center gap-2 text-muted-foreground hover:text-foreground">
              <ArrowLeft className="w-4 h-4" /> Back
            </button>

            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4 text-sm text-blue-800 dark:text-blue-300">
              <p className="font-medium mb-2">Why verify?</p>
              <p>Your ID helps us keep the marketplace safe and trusted. Your documents are reviewed by our team and stored securely.</p>
            </div>

            {error && (
              <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
                {error}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">ID Document (Front)</label>
              <input type="file" ref={idFrontRef} accept="image/*" onChange={(e) => setKycIdFront(e.target.files?.[0] || null)} className="hidden" />
              <button
                type="button"
                onClick={() => idFrontRef.current?.click()}
                className="w-full aspect-[3/2] flex flex-col items-center justify-center border-2 border-dashed border-input rounded-lg text-muted-foreground hover:border-primary hover:text-primary transition-colors"
              >
                {kycIdFront ? (
                  <img src={URL.createObjectURL(kycIdFront)} alt="ID Front" className="w-full h-full object-cover rounded-lg" />
                ) : (
                  <>
                    <Upload className="w-8 h-8 mb-2" />
                    <span className="text-sm">Upload ID document</span>
                  </>
                )}
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium text-foreground mb-2">Selfie</label>
              <input type="file" ref={selfieRef} accept="image/*" onChange={(e) => setKycSelfie(e.target.files?.[0] || null)} className="hidden" />
              <button
                type="button"
                onClick={() => selfieRef.current?.click()}
                className="w-full aspect-[3/2] flex flex-col items-center justify-center border-2 border-dashed border-input rounded-lg text-muted-foreground hover:border-primary hover:text-primary transition-colors"
              >
                {kycSelfie ? (
                  <img src={URL.createObjectURL(kycSelfie)} alt="Selfie" className="w-full h-full object-cover rounded-lg" />
                ) : (
                  <>
                    <Upload className="w-8 h-8 mb-2" />
                    <span className="text-sm">Upload selfie</span>
                  </>
                )}
              </button>
            </div>

            <button onClick={handleKycSubmit} disabled={loading} className="w-full py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors">
              {loading ? 'Creating account...' : 'Create Account'}
            </button>

            <p className="text-center text-xs text-muted-foreground">
              By continuing, you agree to our Terms of Service and Privacy Policy.
            </p>
          </div>
        )}

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
