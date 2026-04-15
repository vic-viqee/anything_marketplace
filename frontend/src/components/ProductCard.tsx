'use client';

import Link from 'next/link';
import { BadgeCheck, Star } from 'lucide-react';
import { ProductListItem } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ProductCardProps {
  product: ProductListItem;
}

export default function ProductCard({ product }: ProductCardProps) {
  const imageUrl = product.image_url
    ? product.image_url.startsWith('http')
      ? product.image_url
      : `${API_URL}/uploads/${product.image_url}`
    : null;

  const isVerified = product.seller_is_verified;
  const isFeatured = product.is_featured;

  return (
    <Link href={`/product/${product.id}`} className="group block">
      <div className="bg-card rounded-lg overflow-hidden border border-border transition-all duration-300 hover:border-primary hover:shadow-lg relative">
        <div className="aspect-[4/3] relative bg-muted">
          {imageUrl ? (
            <img
              src={imageUrl}
              alt={product.title}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <span className="text-4xl font-light">+</span>
            </div>
          )}
          {isFeatured && (
            <div className="absolute top-2 left-2 px-2 py-1 bg-amber-500 text-white text-xs font-semibold rounded-full flex items-center gap-1 shadow-md">
              <Star className="w-3 h-3 fill-current" />
              Featured
            </div>
          )}
        </div>
        <div className="p-4">
          <div className="flex items-center gap-2">
            <h3 className="font-serif text-lg text-foreground truncate flex-1">{product.title}</h3>
            {isVerified && (
              <span title="Verified Seller">
                <BadgeCheck className="w-5 h-5 text-blue-500 flex-shrink-0" />
              </span>
            )}
          </div>
          <p className="mt-1 text-lg font-semibold text-foreground">
            KES {product.price.toLocaleString()}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {new Date(product.created_at).toLocaleDateString()}
          </p>
        </div>
      </div>
    </Link>
  );
}
