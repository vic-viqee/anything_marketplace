'use client';

import { useState, useEffect, use } from 'react';
import { useRouter } from 'next/navigation';
import { productsApi, chatApi } from '@/lib/api';
import { useAuthStore } from '@/context/auth-store';
import { ArrowLeft, MessageCircle, CheckCircle, Clock, MapPin, Phone, Star, MessageSquare } from 'lucide-react';

interface ProductDetail {
  id: number;
  title: string;
  description: string | null;
  price: number;
  image_url: string | null;
  status: string;
  is_approved: boolean;
  seller_id: number;
  category_id: number | null;
  created_at: string;
  seller: {
    id: number;
    username: string | null;
    phone: string;
    profile_image: string | null;
  } | null;
}

interface RatingStats {
  average_rating: number;
  total_ratings: number;
}

export default function ProductPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [ratingStats, setRatingStats] = useState<RatingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [sendingMessage, setSendingMessage] = useState(false);
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    productsApi.get(Number(id))
      .then(res => setProduct(res.data))
      .catch(() => {})
      .finally(() => setLoading(false));

    if (product?.seller?.id) {
      productsApi.getUserRatings(product.seller.id)
        .then(res => setRatingStats(res.data))
        .catch(() => {});
    }
  }, [id, product?.seller?.id]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-64 bg-muted rounded-xl"></div>
          <div className="h-8 bg-muted rounded w-3/4"></div>
          <div className="h-6 bg-muted rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <h1 className="text-2xl font-bold text-foreground">Product not found</h1>
        <button
          onClick={() => router.push('/')}
          className="mt-4 text-primary hover:underline"
        >
          Go back to feed
        </button>
      </div>
    );
  }

  const isOwner = user?.id === product.seller_id;
  const isSold = product.status === 'sold';

  const handleMessageSeller = async () => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    if (!product.seller) return;

    setSendingMessage(true);
    try {
      const res = await chatApi.createConversation({
        product_id: product.id,
        receiver_id: product.seller.id,
      });
      router.push(`/messages?conversation=${res.data.id}`);
    } catch (err: any) {
      if (err.response?.status === 400) {
        router.push('/messages');
      }
    } finally {
      setSendingMessage(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back
      </button>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="relative">
          {product.image_url ? (
            <img
              src={`${process.env.NEXT_PUBLIC_API_URL}/uploads/${product.image_url}`}
              alt={product.title}
              className="w-full aspect-[4/3] object-cover rounded-xl"
            />
          ) : (
            <div className="w-full aspect-[4/3] bg-muted rounded-xl flex items-center justify-center">
              <span className="text-muted-foreground">No image</span>
            </div>
          )}
          
          {!product.is_approved && isOwner && (
            <div className="absolute top-4 left-4 px-3 py-1.5 bg-yellow-500/90 text-white text-sm font-medium rounded-full flex items-center gap-1.5">
              <Clock className="w-4 h-4" />
              Pending Approval
            </div>
          )}
          
          {isSold && (
            <div className="absolute inset-0 bg-black/60 rounded-xl flex items-center justify-center">
              <span className="px-4 py-2 bg-destructive text-white font-medium rounded-lg">
                SOLD
              </span>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              {product.is_approved && !isSold && (
                <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full dark:bg-green-900/30 dark:text-green-400">
                  Available
                </span>
              )}
            </div>
            <h1 className="text-3xl font-serif font-bold text-foreground">{product.title}</h1>
            <p className="mt-3 text-2xl font-bold text-primary">
              KES {product.price.toLocaleString()}
            </p>
          </div>

          {product.description && (
            <div>
              <h2 className="text-sm font-medium text-muted-foreground mb-2">Description</h2>
              <p className="text-foreground whitespace-pre-wrap">{product.description}</p>
            </div>
          )}

          {product.seller && (
            <div className="border-t border-border pt-6">
              <h2 className="text-sm font-medium text-muted-foreground mb-4">Seller</h2>
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center overflow-hidden">
                  {product.seller.profile_image ? (
                    <img
                      src={`${process.env.NEXT_PUBLIC_API_URL}/uploads/${product.seller.profile_image}`}
                      alt={product.seller.username || 'Seller'}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <span className="text-lg font-medium text-muted-foreground">
                      {(product.seller.username || product.seller.phone).charAt(0).toUpperCase()}
                    </span>
                  )}
                </div>
                <div className="flex-1">
                  <p className="font-medium text-foreground">
                    {product.seller.username || 'Anonymous Seller'}
                  </p>
                  {ratingStats && ratingStats.total_ratings > 0 && (
                    <div className="flex items-center gap-1 text-sm text-muted-foreground mt-0.5">
                      <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                      <span>{ratingStats.average_rating.toFixed(1)} ({ratingStats.total_ratings} reviews)</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="border-t border-border pt-6 space-y-3">
            {!isOwner && product.is_approved && !isSold && (
              <>
                <button
                  onClick={handleMessageSeller}
                  disabled={sendingMessage}
                  className="w-full py-3 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                >
                  <MessageCircle className="w-5 h-5" />
                  {sendingMessage ? 'Starting...' : 'Message Seller'}
                </button>
                
                {product.seller?.phone && (
                  <a
                    href={`https://wa.me/${product.seller.phone.replace('+', '')}?text=Hi, I'm interested in your "${product.title}" listed for KES ${product.price.toLocaleString()}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full py-3 bg-green-500 text-white rounded-full font-medium hover:bg-green-600 transition-colors flex items-center justify-center gap-2"
                  >
                    <MessageSquare className="w-5 h-5" />
                    WhatsApp
                  </a>
                )}
              </>
            )}
            
            <p className="text-center text-sm text-muted-foreground">
              Payment on delivery - meet the seller and pay when you receive the item
            </p>
          </div>

          <div className="text-xs text-muted-foreground">
            Posted {new Date(product.created_at).toLocaleDateString()}
          </div>
        </div>
      </div>
    </div>
  );
}