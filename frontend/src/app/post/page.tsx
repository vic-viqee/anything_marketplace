'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { productsApi } from '@/lib/api';
import { useAuthStore } from '@/context/auth-store';
import { Category, ApiError } from '@/types';
import { Upload, X, ShieldCheck, MessageCircle } from 'lucide-react';

export default function PostAd() {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [price, setPrice] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const { isAuthenticated, isSeller, user } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    if (!isSeller) {
      return;
    }
    productsApi.categories().then(res => setCategories(res.data)).catch(() => {});
  }, [isAuthenticated, isSeller, router]);

  if (!isAuthenticated) {
    return null;
  }

  if (!isSeller) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full mb-6">
          <svg className="w-8 h-8 text-yellow-600 dark:text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
        <h2 className="font-serif text-2xl text-foreground mb-2">Become a Seller</h2>
        <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
          You need a seller account to post products. Upgrade your account to start selling.
        </p>
        <button
          onClick={() => router.push('/profile?upgrade=true')}
          className="px-6 py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 transition-colors"
        >
          Upgrade to Seller
        </button>
      </div>
    );
  }

  if (!user?.is_identity_verified) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full mb-6">
          <ShieldCheck className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
        </div>
        <h2 className="font-serif text-2xl text-foreground mb-2">Account Not Verified</h2>
        <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
          Your account needs to be verified before you can post products. Contact admin on WhatsApp to get verified.
        </p>
        <a
          href={`https://wa.me/254114086112?text=${encodeURIComponent(`Hi, I want to verify my seller account. My phone: ${user?.phone}`)}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-6 py-3 bg-green-500 text-white rounded-full font-medium hover:bg-green-600 transition-colors"
        >
          <MessageCircle className="w-5 h-5" />
          Contact Admin on WhatsApp
        </a>
      </div>
    );
  }

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImage(file);
      setImagePreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('description', description);
      formData.append('price', price);
      if (categoryId) formData.append('category_id', categoryId);
      if (image) formData.append('image', image);

      await productsApi.create(formData);
      setSubmitted(true);
    } catch (err) {
      const e = err as ApiError;
      const status = e.response?.status;
      const detail = e.response?.data?.detail;
      if (status === 403) {
        setError(detail || 'You need to be a seller to post products. Upgrade your account in profile settings.');
      } else if (status === 401) {
        setError('Session expired. Please login again.');
        router.push('/login');
      } else {
        setError(detail || 'Failed to create listing');
      }
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full mb-6">
          <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 className="font-serif text-2xl text-foreground mb-2">Ad Posted!</h2>
        <p className="text-muted-foreground mb-6 max-w-sm mx-auto">
          Your listing has been submitted. It will appear in the marketplace once an admin reviews and approves it.
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => router.push('/my-products')}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 transition-colors"
          >
            View My Products
          </button>
          <button
            onClick={() => { setTitle(''); setDescription(''); setPrice(''); setCategoryId(''); setImage(null); setImagePreview(null); setSubmitted(false); }}
            className="px-6 py-3 border border-input text-foreground rounded-full font-medium hover:bg-muted transition-colors"
          >
            Post Another
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="font-serif text-3xl text-foreground">Post an Ad</h1>
        <p className="mt-2 text-muted-foreground">List your item for sale</p>
      </div>

      <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl text-sm text-blue-800 dark:text-blue-300">
        <p className="font-medium mb-1">What happens next?</p>
        <ul className="space-y-1">
          <li>1. Your ad is submitted for review</li>
          <li>2. An admin will approve it (usually within 24 hours)</li>
          <li>3. Once approved, your listing appears in the marketplace</li>
          <li>4. You&apos;ll receive a notification when it goes live</li>
        </ul>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
            {error}
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Title *
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-0 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            placeholder="What are you selling?"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-0 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background resize-none"
            placeholder="Describe your item..."
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Price (KES) *
            </label>
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-0 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              placeholder="0"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Category
            </label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground focus:border-primary focus:ring-0 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              <option value="">Select category</option>
              {categories.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Image
          </label>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleImageChange}
            accept="image/*"
            className="hidden"
          />
          
          {imagePreview ? (
            <div className="relative aspect-[4/3] w-full max-w-md bg-muted rounded-lg overflow-hidden">
              <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
              <button
                type="button"
                onClick={() => { setImage(null); setImagePreview(null); if (fileInputRef.current) fileInputRef.current.value = ''; }}
                className="absolute top-2 right-2 p-1 bg-background rounded-full shadow-md hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                aria-label="Remove image"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="w-full max-w-md aspect-[4/3] flex flex-col items-center justify-center border-2 border-dashed border-input rounded-lg text-muted-foreground hover:border-primary hover:text-primary transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              <Upload className="w-8 h-8 mb-2" />
              <span className="text-sm">Click to upload image</span>
            </button>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          {loading ? 'Posting...' : 'Post Ad'}
        </button>
      </form>
    </div>
  );
}
