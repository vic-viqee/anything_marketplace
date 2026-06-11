'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Star, Pencil, Trash2 } from 'lucide-react';

export interface MyProduct {
  id: number;
  title: string;
  price: number;
  image_url: string | null;
  status: string;
  is_approved: boolean;
  is_featured: boolean;
  featured_until: string | null;
  created_at: string;
}

interface MyProductCardProps {
  product: MyProduct;
  onMarkSold?: (id: number) => void;
  markingSold?: number | null;
  sold?: boolean;
  onToggleFeatured?: (id: number, current: boolean) => void;
  togglingFeatured?: number | null;
  onDelete?: (id: number) => void;
  deleting?: number | null;
  confirmDelete?: number | null;
  setConfirmDelete?: (id: number | null) => void;
}

export default function MyProductCard({
  product,
  onMarkSold,
  markingSold,
  sold,
  onToggleFeatured,
  togglingFeatured,
  onDelete,
  deleting,
  confirmDelete,
  setConfirmDelete,
}: MyProductCardProps) {
  const router = useRouter();
  const [imgError, setImgError] = useState(false);
  const src = product.image_url
    ? (product.image_url.startsWith('http') ? product.image_url : `${process.env.NEXT_PUBLIC_API_URL}/uploads/${product.image_url}`)
    : null;

  const isDeleting = deleting === product.id;
  const showConfirm = confirmDelete === product.id;

  return (
    <div className="group border border-border rounded-xl overflow-hidden hover:shadow-lg transition-all">
      {showConfirm && (
        <div className="px-4 pt-3 pb-2 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
          <p className="text-sm font-medium text-red-600 dark:text-red-400 mb-2">Delete this listing?</p>
          <div className="flex gap-2">
            <button
              onClick={(e) => { e.stopPropagation(); onDelete?.(product.id); }}
              disabled={isDeleting}
              className="flex-1 py-1.5 text-xs bg-destructive text-destructive-foreground rounded-md font-medium hover:bg-destructive/80 disabled:opacity-50"
            >
              {isDeleting ? 'Deleting...' : 'Yes, Delete'}
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setConfirmDelete?.(null); }}
              className="flex-1 py-1.5 text-xs border border-input rounded-md text-foreground hover:bg-muted"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
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
        {product.is_featured && !sold && (
          <div className="absolute top-2 left-2 px-2 py-1 bg-amber-500 text-white text-xs font-semibold rounded-full flex items-center gap-1">
            <Star className="w-3 h-3 fill-current" />
            Featured
          </div>
        )}
        <div className="absolute top-2 right-2 flex gap-1">
          {!sold && (
            <button
              onClick={(e) => { e.stopPropagation(); router.push(`/product/${product.id}/edit`); }}
              className="p-1.5 bg-background/80 backdrop-blur-sm rounded-lg text-muted-foreground hover:text-primary hover:bg-background transition-colors"
              title="Edit"
            >
              <Pencil className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={(e) => { e.stopPropagation(); setConfirmDelete?.(product.id); }}
            className="p-1.5 bg-background/80 backdrop-blur-sm rounded-lg text-muted-foreground hover:text-destructive hover:bg-background transition-colors"
            title="Delete"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
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
        {!sold && onToggleFeatured && product.is_approved && (
          <button
            onClick={(e) => { e.stopPropagation(); onToggleFeatured(product.id, product.is_featured); }}
            disabled={togglingFeatured === product.id}
            className={`mt-2 w-full py-2 text-sm border rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2 ${
              product.is_featured
                ? 'border-amber-500 text-amber-500 hover:bg-amber-500/10'
                : 'border-input text-muted-foreground hover:border-amber-500 hover:text-amber-500'
            }`}
          >
            <Star className={`w-4 h-4 ${product.is_featured ? 'fill-current' : ''}`} />
            {togglingFeatured === product.id ? 'Updating...' : product.is_featured ? 'Remove Featured' : 'Feature'}
          </button>
        )}
        <p className="mt-2 text-xs text-muted-foreground">
          Posted {new Date(product.created_at).toLocaleDateString()}
        </p>
      </div>
    </div>
  );
}
