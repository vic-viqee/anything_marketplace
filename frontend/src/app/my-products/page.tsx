'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { productsApi } from '@/lib/api';
import { useAuthStore } from '@/context/auth-store';
import { Clock, CheckCircle, XCircle, ArrowLeft } from 'lucide-react';

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
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    if (user?.role === 'CUSTOMER') {
      router.push('/');
      return;
    }

    productsApi.myProducts()
      .then(res => setProducts(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isAuthenticated, user, router]);

  if (!isAuthenticated || user?.role === 'CUSTOMER') {
    return null;
  }

  const getStatusBadge = (isApproved: boolean) => {
    if (isApproved) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
          <CheckCircle className="w-3 h-3" />
          Approved
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400">
        <Clock className="w-3 h-3" />
        Pending Approval
      </span>
    );
  };

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
        <div className="text-center py-12">
          <p className="text-muted-foreground mb-4">You haven&apos;t posted any products yet</p>
          <button
            onClick={() => router.push('/post')}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 transition-colors"
          >
            Post Your First Ad
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {products.map(product => (
            <div
              key={product.id}
              className="group border border-border rounded-xl overflow-hidden hover:shadow-lg transition-all"
            >
              <div className="aspect-[4/3] bg-muted relative">
                {product.image_url ? (
                  <img
                    src={product.image_url.startsWith('http') ? product.image_url : `${process.env.NEXT_PUBLIC_API_URL}/uploads/${product.image_url}`}
                    alt={product.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-muted-foreground">
                    No image
                  </div>
                )}
                <div className="absolute top-3 right-3">
                  {getStatusBadge(product.is_approved)}
                </div>
              </div>
              <div className="p-4">
                <h3 className="font-medium text-foreground truncate">{product.title}</h3>
                <p className="mt-1 text-lg font-semibold text-primary">KES {product.price.toLocaleString()}</p>
                <p className="mt-2 text-xs text-muted-foreground">
                  Posted {new Date(product.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}