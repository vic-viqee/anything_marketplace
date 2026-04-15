'use client';

import { useEffect, useState } from 'react';
import { productsApi } from '@/lib/api';
import { ProductListItem, Category } from '@/types';
import ProductCard from '@/components/ProductCard';
import { Search } from 'lucide-react';

export default function Home() {
  const [products, setProducts] = useState<ProductListItem[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');

  useEffect(() => {
    loadProducts(1);
    loadCategories();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intentional: loadProducts is stable
  }, []);

  const loadProducts = async (pageNum: number, searchTerm?: string) => {
    try {
      setLoading(true);
      const res = await productsApi.feed({
        page: pageNum,
        page_size: 12,
        search: searchTerm || undefined,
        category_id: selectedCategory || undefined
      });
      if (pageNum === 1) {
        setProducts(res.data);
      } else {
        setProducts(prev => [...prev, ...res.data]);
      }
      setHasMore(res.data.length === 12);
    } catch {
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const res = await productsApi.categories();
      setCategories(res.data);
    } catch {
      // Silently fail for categories
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const term = searchInput.trim();
    setSearch(term);
    setPage(1);
    loadProducts(1, term);
  };

  const handleLoadMore = () => {
    const nextPage = page + 1;
    setPage(nextPage);
    loadProducts(nextPage, search || undefined);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="font-serif text-4xl text-foreground">Discover</h1>
        <p className="mt-2 text-muted-foreground">Find anything you need</p>
      </div>

      <form onSubmit={handleSearch} className="mb-6">
        <div className="relative">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search products..."
            className="w-full pl-12 pr-4 py-3 bg-card border border-border rounded-lg text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </form>

      <div className="flex gap-2 overflow-x-auto pb-4 mb-6 scrollbar-hide">
        <button
          onClick={() => { setSelectedCategory(null); setPage(1); loadProducts(1); }}
          className={`px-4 py-2 min-h-[44px] min-w-[44px] rounded-full text-sm whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
            selectedCategory === null
              ? 'bg-primary text-primary-foreground'
              : 'bg-muted text-muted-foreground hover:bg-muted/80'
          }`}
        >
          All
        </button>
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => { setSelectedCategory(cat.id); setPage(1); loadProducts(1); }}
            className={`px-4 py-2 min-h-[44px] min-w-[44px] rounded-full text-sm whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
              selectedCategory === cat.id
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted text-muted-foreground hover:bg-muted/80'
            }`}
          >
            {cat.name}
          </button>
        ))}
      </div>

      {products.length === 0 && !loading ? (
        <div className="text-center py-20">
          <p className="text-muted-foreground text-lg">No products yet. Be the first to post!</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {products.map(product => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>

          {hasMore && (
            <div className="mt-12 text-center">
              <button
                onClick={handleLoadMore}
                disabled={loading}
                className="px-8 py-3 bg-primary text-primary-foreground rounded-full text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                {loading ? 'Loading...' : 'Load More'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
