'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { productsApi } from '@/lib/api';
import { useAuthStore } from '@/context/auth-store';
import { Clock, CheckCircle, ArrowLeft, Package, Star, Crown, Zap, Shield, ShieldCheck, MessageCircle } from 'lucide-react';
import MyProductCard, { MyProduct } from '@/components/MyProductCard';
import { SkeletonBlock } from '@/components/Skeleton';

export default function MyProducts() {
  const [products, setProducts] = useState<MyProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [markingSold, setMarkingSold] = useState<number | null>(null);
  const [togglingFeatured, setTogglingFeatured] = useState<number | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null);
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  const tierLimits: Record<string, { featured: number; name: string; icon: React.ReactNode }> = {
    free: { featured: 0, name: 'Free', icon: <Shield className="w-4 h-4" /> },
    basic: { featured: 1, name: 'Basic', icon: <Zap className="w-4 h-4" /> },
    standard: { featured: 3, name: 'Standard', icon: <Star className="w-4 h-4" /> },
    premium: { featured: 5, name: 'Premium', icon: <Crown className="w-4 h-4" /> },
  };

  const currentTier = user?.subscription_tier || 'free';
  const tierConfig = tierLimits[currentTier] || tierLimits.free;
  const usedFeatured = products.filter(p => p.is_featured).length;
  const canFeature = currentTier !== 'free' && usedFeatured < tierConfig.featured;

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    if (user?.role === 'customer') {
      router.push('/');
      return;
    }

    productsApi.myProducts()
      .then(res => setProducts(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isAuthenticated, user, router]);

  const handleMarkSold = async (productId: number) => {
    if (!confirm('Mark this item as sold? It will be removed from the marketplace.')) return;
    setMarkingSold(productId);
    try {
      await productsApi.markSold(productId);
      setProducts(prev => prev.map(p =>
        p.id === productId ? { ...p, status: 'sold', is_approved: false } : p
      ));
    } catch {
      alert('Failed to mark as sold');
    } finally {
      setMarkingSold(null);
    }
  };

  const handleDelete = async (productId: number) => {
    setDeleting(productId);
    try {
      await productsApi.delete(productId);
      setProducts(prev => prev.filter(p => p.id !== productId));
    } catch {
      alert('Failed to delete product');
    } finally {
      setDeleting(null);
      setConfirmDelete(null);
    }
  };

  const handleToggleFeatured = async (productId: number, currentlyFeatured: boolean) => {
    if (currentlyFeatured) {
      if (!confirm('Remove this listing from featured?')) return;
      setTogglingFeatured(productId);
      try {
        await productsApi.unfeatureProduct(productId);
        setProducts(prev => prev.map(p =>
          p.id === productId ? { ...p, is_featured: false, featured_until: null } : p
        ));
      } catch {
        alert('Failed to remove featured status');
      } finally {
        setTogglingFeatured(null);
      }
    } else {
      if (!canFeature) {
        alert(`Your ${tierConfig.name} plan allows ${tierConfig.featured} featured listings. Upgrade to feature more.`);
        return;
      }
      if (!confirm('Feature this listing? It will appear at the top of the feed for 7 days.')) return;
      setTogglingFeatured(productId);
      try {
        await productsApi.featureProduct(productId);
        const featuredUntil = new Date();
        featuredUntil.setDate(featuredUntil.getDate() + 7);
        setProducts(prev => prev.map(p =>
          p.id === productId ? { ...p, is_featured: true, featured_until: featuredUntil.toISOString() } : p
        ));
      } catch {
        alert('Failed to feature listing');
      } finally {
        setTogglingFeatured(null);
      }
    }
  };

  if (!isAuthenticated || user?.role === 'customer') {
    return null;
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

  const approved = products.filter(p => p.is_approved);
  const pending = products.filter(p => !p.is_approved && p.status === 'available');
  const sold = products.filter(p => p.status === 'sold');

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center gap-4 mb-8">
        <button
          onClick={() => router.back()}
          className="p-2 rounded-full hover:bg-muted transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="font-serif text-3xl text-foreground">My Products</h1>
          <p className="mt-1 text-muted-foreground">Manage your listings and check approval status</p>
        </div>
      </div>

      <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-border rounded-xl p-4 mb-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${currentTier === 'premium' ? 'bg-amber-500/20 text-amber-500' : currentTier === 'standard' ? 'bg-blue-500/20 text-blue-500' : currentTier === 'basic' ? 'bg-orange-500/20 text-orange-500' : 'bg-muted text-muted-foreground'}`}>
              {tierConfig.icon}
            </div>
            <div>
              <p className="font-medium text-foreground">{tierConfig.name} Plan</p>
              <p className="text-xs text-muted-foreground">
                {usedFeatured}/{tierConfig.featured} featured listings used
              </p>
            </div>
          </div>
          {currentTier !== 'premium' && (
            <button
              onClick={() => router.push('/profile?tab=subscription')}
              className="text-sm px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              Upgrade Plan
            </button>
          )}
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="border border-border rounded-xl overflow-hidden">
              <SkeletonBlock className="aspect-[4/3] rounded-none" />
              <div className="p-4 space-y-2">
                <SkeletonBlock className="h-5 w-3/4" />
                <SkeletonBlock className="h-6 w-1/2" />
                <SkeletonBlock className="h-9 w-full mt-3" />
                <SkeletonBlock className="h-4 w-1/3" />
              </div>
            </div>
          ))}
        </div>
      ) : products.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
            <Package className="w-8 h-8 text-muted-foreground" />
          </div>
          <p className="text-muted-foreground mb-6">You haven&apos;t posted any products yet</p>
          <button
            onClick={() => router.push('/post')}
            className="px-6 py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 transition-colors"
          >
            Post Your First Ad
          </button>
        </div>
      ) : (
        <div className="space-y-8">
          {pending.length > 0 && (
            <section>
              <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3 flex items-center gap-2">
                <Clock className="w-4 h-4 text-yellow-500" />
                Pending Approval ({pending.length})
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {pending.map(product => (
                  <MyProductCard key={product.id} product={product} onDelete={handleDelete} deleting={deleting} confirmDelete={confirmDelete} setConfirmDelete={setConfirmDelete} />
                ))}
              </div>
            </section>
          )}

          {approved.length > 0 && (
            <section>
              <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                Active Listings ({approved.length})
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {approved.map(product => (
                  <MyProductCard key={product.id} product={product} onMarkSold={handleMarkSold} markingSold={markingSold} onToggleFeatured={handleToggleFeatured} togglingFeatured={togglingFeatured} onDelete={handleDelete} deleting={deleting} confirmDelete={confirmDelete} setConfirmDelete={setConfirmDelete} />
                ))}
              </div>
            </section>
          )}

          {sold.length > 0 && (
            <section>
              <h2 className="text-sm font-medium text-muted-foreground uppercase tracking-wide mb-3">
                Sold ({sold.length})
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {sold.map(product => (
                  <MyProductCard key={product.id} product={product} sold onDelete={handleDelete} deleting={deleting} confirmDelete={confirmDelete} setConfirmDelete={setConfirmDelete} />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}


