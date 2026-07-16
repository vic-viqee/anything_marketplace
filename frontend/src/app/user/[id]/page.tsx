'use client';

import { useState, useEffect, use } from 'react';
import { useRouter, notFound } from 'next/navigation';
import Link from 'next/link';
import { usersApi, productsApi } from '@/lib/api';
import { User, ProductListItem, RatingStats } from '@/types';
import { BadgeCheck, Star, Calendar, Package, ArrowLeft, MessageCircle, ChevronLeft, ChevronRight, Shield, Crown, Zap } from 'lucide-react';

export default function UserProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [profile, setProfile] = useState<User | null>(null);
  const [products, setProducts] = useState<ProductListItem[]>([]);
  const [ratingStats, setRatingStats] = useState<RatingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [productPage, setProductPage] = useState(0);
  const PRODUCTS_PER_PAGE = 8;

  const userId = Number(id);

  useEffect(() => {
    if (!userId) return;

    Promise.all([
      usersApi.get(userId),
      usersApi.getProducts(userId),
      productsApi.getUserRatings(userId),
    ])
      .then(([profileRes, productsRes, ratingsRes]) => {
        setProfile(profileRes.data);
        setProducts(productsRes.data);
        setRatingStats(ratingsRes.data);
      })
      .catch(() => {
        setProfile(null);
      })
      .finally(() => setLoading(false));
  }, [userId]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="animate-pulse space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-20 h-20 bg-muted rounded-full"></div>
            <div className="space-y-2">
              <div className="h-6 bg-muted rounded w-40"></div>
              <div className="h-4 bg-muted rounded w-24"></div>
            </div>
          </div>
          <div className="h-48 bg-muted rounded-xl"></div>
        </div>
      </div>
    );
  }

  if (!profile) notFound();

  const paginatedProducts = products.slice(
    productPage * PRODUCTS_PER_PAGE,
    (productPage + 1) * PRODUCTS_PER_PAGE
  );
  const totalPages = Math.ceil(products.length / PRODUCTS_PER_PAGE);

  const tierIcon = (tier: string) => {
    switch (tier) {
      case 'premium': return <Crown className="w-4 h-4" />;
      case 'standard': return <BadgeCheck className="w-4 h-4" />;
      case 'basic': return <Zap className="w-4 h-4" />;
      default: return <Shield className="w-4 h-4" />;
    }
  };

  const tierColors: Record<string, string> = {
    premium: 'text-amber-500',
    standard: 'text-blue-500',
    basic: 'text-orange-500',
    free: 'text-muted-foreground',
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

      <div className="bg-card border border-border rounded-xl p-6 mb-8">
        <div className="flex items-center gap-5">
          <div className="w-20 h-20 rounded-full bg-muted flex items-center justify-center overflow-hidden flex-shrink-0">
            {profile.profile_image ? (
              <img
                src={profile.profile_image.startsWith('http') ? profile.profile_image : `${process.env.NEXT_PUBLIC_API_URL}/uploads/${profile.profile_image}`}
                alt={profile.username || 'User'}
                className="w-full h-full object-cover"
              />
            ) : (
              <span className="text-2xl font-medium text-muted-foreground">
                {(profile.username || profile.phone).charAt(0).toUpperCase()}
              </span>
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="font-serif text-2xl text-foreground truncate">
                {profile.username || 'Anonymous User'}
              </h1>
              {profile.is_verified && (
                <span title="Verified Seller">
                  <BadgeCheck className="w-5 h-5 text-blue-500 flex-shrink-0" />
                </span>
              )}
            </div>
            <div className="flex items-center gap-3 mt-1 text-sm text-muted-foreground flex-wrap">
              {profile.role && (
                <span className="capitalize">{profile.role}</span>
              )}
              <span className={`flex items-center gap-1 ${tierColors[profile.subscription_tier] || 'text-muted-foreground'}`}>
                {tierIcon(profile.subscription_tier)}
                {profile.subscription_tier?.charAt(0).toUpperCase() + profile.subscription_tier?.slice(1) || 'Free'}
              </span>
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                Joined {new Date(profile.created_at).toLocaleDateString()}
              </span>
            </div>
            {ratingStats && ratingStats.total_ratings > 0 && (
              <div className="flex items-center gap-1 mt-2 text-sm">
                <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                <span className="font-medium text-foreground">{ratingStats.average_rating.toFixed(1)}</span>
                <span className="text-muted-foreground">({ratingStats.total_ratings} reviews)</span>
              </div>
            )}
          </div>
        </div>

        {profile.role === 'seller' && (
          <a
            href={`https://wa.me/${profile.phone.replace('+', '')}`}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-flex items-center gap-2 px-5 py-2.5 bg-green-500 text-white rounded-full text-sm font-medium hover:bg-green-600 transition-colors"
          >
            <MessageCircle className="w-4 h-4" />
            Contact on WhatsApp
          </a>
        )}
      </div>

      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-serif text-xl text-foreground flex items-center gap-2">
            <Package className="w-5 h-5 text-muted-foreground" />
            Listings
            <span className="text-sm font-normal text-muted-foreground">({products.length})</span>
          </h2>
        </div>

        {products.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            No listings yet
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {paginatedProducts.map((product) => (
                <Link
                  key={product.id}
                  href={`/product/${product.id}`}
                  className="group block"
                >
                  <div className="bg-card border border-border rounded-lg overflow-hidden transition-all duration-300 hover:border-primary hover:shadow-md">
                    <div className="aspect-[4/3] bg-muted relative">
                      {product.image_url ? (
                        <img
                          src={product.image_url.startsWith('http') ? product.image_url : `${process.env.NEXT_PUBLIC_API_URL}/uploads/${product.image_url}`}
                          alt={product.title}
                          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                        />
                      ) : (
                        <div className="flex items-center justify-center h-full text-muted-foreground">
                          <span className="text-3xl font-light">+</span>
                        </div>
                      )}
                      {product.is_featured && (
                        <div className="absolute top-2 left-2 px-2 py-1 bg-amber-500 text-white text-xs font-semibold rounded-full flex items-center gap-1">
                          <Star className="w-3 h-3 fill-current" />
                          Featured
                        </div>
                      )}
                    </div>
                    <div className="p-3">
                      <h3 className="font-medium text-foreground text-sm truncate">{product.title}</h3>
                      <p className="mt-1 text-sm font-semibold text-primary">
                        KES {product.price.toLocaleString()}
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {new Date(product.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-4 mt-6">
                <button
                  onClick={() => setProductPage(p => Math.max(0, p - 1))}
                  disabled={productPage === 0}
                  className="p-2 rounded-lg border border-input hover:bg-muted disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-sm text-muted-foreground">
                  Page {productPage + 1} of {totalPages}
                </span>
                <button
                  onClick={() => setProductPage(p => Math.min(totalPages - 1, p + 1))}
                  disabled={productPage >= totalPages - 1}
                  className="p-2 rounded-lg border border-input hover:bg-muted disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
