'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { productsApi } from '@/lib/api';
import { useAuthStore } from '@/context/auth-store';
import { Clock, CheckCircle, ArrowLeft, Package } from 'lucide-react';

interface MyProduct {
  id: number;
  title: string;
  price: number;
  image_url: string | null;
  status: string;
  is_approved: boolean;
  created_at: string;
}

export default function MyProducts() {
  const [products, setProducts] = useState<MyProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [markingSold, setMarkingSold] = useState<number | null>(null);
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

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

  if (!isAuthenticated || user?.role === 'customer') {
    return null;
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

      {loading ? (
        <div className="text-center py-12 text-muted-foreground">Loading...</div>
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
                  <ProductCard key={product.id} product={product} />
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
                  <ProductCard key={product.id} product={product} onMarkSold={handleMarkSold} markingSold={markingSold} />
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
                  <ProductCard key={product.id} product={product} sold />
                ))}
              </div>
            </section>
          )}
        </div>
      )}
    </div>
  );
}

function ProductCard({ product, onMarkSold, markingSold, sold }: {
  product: MyProduct;
  onMarkSold?: (id: number) => void;
  markingSold?: number | null;
  sold?: boolean;
}) {
  const router = useRouter();
  const [imgError, setImgError] = useState(false);
  const src = product.image_url
    ? (product.image_url.startsWith('http') ? product.image_url : `${process.env.NEXT_PUBLIC_API_URL}/uploads/${product.image_url}`)
    : null;

  return (
    <div className="group border border-border rounded-xl overflow-hidden hover:shadow-lg transition-all">
      <div
        className="aspect-[4/3] bg-muted relative cursor-pointer"
        onClick={() => router.push(`/product/${product.id}`)}
      >
        {src && !imgError ? (
          <img
            src={src}
            alt={product.title}
            className="w-full h-full object-cover"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-muted-foreground">
            No image
          </div>
        )}
        {sold && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <span className="px-3 py-1 bg-destructive text-white text-sm font-medium rounded-full">Sold</span>
          </div>
        )}
      </div>
      <div className="p-4">
        <h3 className="font-medium text-foreground truncate">{product.title}</h3>
        <p className="mt-1 text-lg font-semibold text-primary">KES {product.price.toLocaleString()}</p>
        {!sold && onMarkSold && product.is_approved && (
          <button
            onClick={(e) => { e.stopPropagation(); onMarkSold(product.id); }}
            disabled={markingSold === product.id}
            className="mt-2 w-full py-2 text-sm border border-input rounded-lg text-muted-foreground hover:border-primary hover:text-primary transition-colors disabled:opacity-50"
          >
            {markingSold === product.id ? 'Marking...' : 'Mark as Sold'}
          </button>
        )}
        <p className="mt-2 text-xs text-muted-foreground">
          Posted {new Date(product.created_at).toLocaleDateString()}
        </p>
      </div>
    </div>
  );
}
