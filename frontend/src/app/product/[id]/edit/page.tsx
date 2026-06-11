'use client';

import { useState, useEffect, use } from 'react';
import { useRouter } from 'next/navigation';
import { productsApi } from '@/lib/api';
import { useAuthStore } from '@/context/auth-store';
import { ImagePlus, X, Loader2, ArrowLeft } from 'lucide-react';
import { Category, ApiError } from '@/types';

export default function EditProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  const [title, setTitle] = useState('');
  const [price, setPrice] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [categories, setCategories] = useState<Category[]>([]);
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [existingImage, setExistingImage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    const productId = Number(id);
    Promise.all([
      productsApi.get(productId),
      productsApi.categories(),
    ])
      .then(([productRes, catsRes]) => {
        const p = productRes.data;
        if (p.seller_id !== user?.id) {
          router.push(`/product/${id}`);
          return;
        }
        setTitle(p.title);
        setPrice(String(p.price));
        setDescription(p.description || '');
        setCategoryId(String(p.category_id || ''));
        setCategories(catsRes.data);
        if (p.image_url) {
          const src = p.image_url.startsWith('http')
            ? p.image_url
            : `${process.env.NEXT_PUBLIC_API_URL}/uploads/${p.image_url}`;
          setExistingImage(src);
        }
      })
      .catch(() => {
        setError('Failed to load product');
      })
      .finally(() => setLoading(false));
  }, [id, user, router]);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setImage(file);
    setImagePreview(URL.createObjectURL(file));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    const formData = new FormData();
    formData.append('title', title);
    formData.append('price', price);
    if (description) formData.append('description', description);
    if (categoryId) formData.append('category_id', categoryId);
    if (image) formData.append('image', image);

    try {
      await productsApi.update(Number(id), formData);
      setSuccess(true);
      setTimeout(() => router.push(`/product/${id}`), 1500);
    } catch (err) {
      const e = err as ApiError;
      setError(e.response?.data?.detail || 'Failed to update product');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/3"></div>
          <div className="h-12 bg-muted rounded"></div>
          <div className="h-12 bg-muted rounded"></div>
          <div className="h-32 bg-muted rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      <h1 className="font-serif text-3xl text-foreground mb-8">Edit Product</h1>

      {success ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <Loader2 className="w-8 h-8 text-green-500" />
          </div>
          <p className="text-lg font-medium text-foreground">Product Updated!</p>
          <p className="text-sm text-muted-foreground mt-2">Redirecting...</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground"
              placeholder="What are you selling?"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Price (KES) *</label>
            <input
              type="number"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              required
              min="1"
              className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground"
              placeholder="e.g. 5000"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Category</label>
            <select
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground"
            >
              <option value="">Select a category</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>{cat.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground resize-none"
              placeholder="Describe your item..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Image</label>
            <div className="flex items-start gap-4">
              <label className="flex flex-col items-center justify-center w-32 h-32 border-2 border-dashed border-input rounded-lg cursor-pointer hover:border-primary transition-colors">
                <ImagePlus className="w-6 h-6 text-muted-foreground" />
                <span className="mt-1 text-xs text-muted-foreground">Change image</span>
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageChange}
                  className="hidden"
                />
              </label>
              {(imagePreview || existingImage) && (
                <div className="relative w-32 h-32">
                  <img
                    src={imagePreview || existingImage!}
                    alt="Preview"
                    className="w-full h-full object-cover rounded-lg"
                  />
                  {imagePreview && (
                    <button
                      type="button"
                      onClick={() => { setImage(null); setImagePreview(null); }}
                      className="absolute -top-2 -right-2 p-1 bg-destructive text-white rounded-full"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  )}
                </div>
              )}
            </div>
            {existingImage && !image && (
              <p className="mt-1 text-xs text-muted-foreground">Current image shown. Upload a new one to replace it.</p>
            )}
          </div>

          <button
            type="submit"
            disabled={submitting || !title || !price}
            className="w-full py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
          >
            {submitting ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </button>
        </form>
      )}
    </div>
  );
}
