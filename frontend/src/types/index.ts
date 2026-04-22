export interface User {
  id: number;
  phone: string;
  username: string | null;
  role: string;
  is_active: boolean;
  is_suspended: boolean;
  profile_image: string | null;
  subscription_tier: string;
  subscription_expires_at?: string;
  kyc_status: string;
  is_verified: boolean;
  pending_kyc: boolean;
  featured_listings_used: number;
  featured_listings_limit: number;
  created_at: string;
}

export interface Product {
  id: number;
  title: string;
  description: string | null;
  price: number;
  image_url: string | null;
  status: string;
  is_approved: boolean;
  is_featured: boolean;
  seller_id: number;
  category_id: number | null;
  created_at: string;
  updated_at: string | null;
  sold_at: string | null;
}

export interface ProductListItem {
  id: number;
  title: string;
  price: number;
  image_url: string | null;
  status: string;
  is_approved: boolean;
  is_featured: boolean;
  seller_id?: number;
  seller_username?: string;
  seller_is_verified: boolean;
  created_at: string;
}

export type SubscriptionTier = 'free' | 'basic' | 'standard' | 'premium';

export interface SubscriptionTierInfo {
  tier: SubscriptionTier;
  name: string;
  price: number;
  featuredLimit: number;
  hasVerifiedBadge: boolean;
  hasContactAdmin: boolean;
}

export const SUBSCRIPTION_TIERS: SubscriptionTierInfo[] = [
  { tier: 'free', name: 'Free', price: 0, featuredLimit: 2, hasVerifiedBadge: false, hasContactAdmin: false },
  { tier: 'basic', name: 'Basic', price: 200, featuredLimit: 5, hasVerifiedBadge: false, hasContactAdmin: true },
  { tier: 'standard', name: 'Standard', price: 500, featuredLimit: 15, hasVerifiedBadge: true, hasContactAdmin: true },
  { tier: 'premium', name: 'Premium', price: 1000, featuredLimit: -1, hasVerifiedBadge: true, hasContactAdmin: true },
];

export interface Category {
  id: number;
  name: string;
  slug: string;
  created_at: string;
}

export interface Conversation {
  id: number;
  product_id: number;
  initiator_id: number;
  receiver_id: number;
  last_message_at: string;
  created_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  sender_id: number;
  content: string;
  is_read: boolean;
  created_at: string;
}

export interface Rating {
  id: number;
  rater_id: number;
  rated_user_id: number;
  product_id: number;
  stars: number;
  comment: string | null;
  created_at: string;
}

export interface RatingStats {
  average_rating: number;
  total_ratings: number;
  stars_breakdown: Record<string, number>;
}

export interface Nudge {
  conversation_id: number;
  other_user_id: number;
  other_username: string | null;
  unread_count: number;
  last_message_at: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}

export interface Analytics {
  total_users: number;
  total_products: number;
  pending_products: number;
  approved_products: number;
  sold_products: number;
  customers: number;
  sellers: number;
  activity_today?: number;
  products_by_category?: Array<{ name: string; count: number }>;
  users_over_time?: Array<{ name: string; count: number }>;
}

export interface Notification {
  id: number;
  notification_type: string;
  title: string;
  message: string;
  is_read: boolean;
  related_id: number | null;
  created_at: string;
}

export interface Ticket {
  id: number;
  user_id: number;
  reported_user_id?: number;
  product_id?: number;
  ticket_type: string;
  description: string;
  status: string;
  created_at: string;
  updated_at?: string;
}

export interface Report {
  id: number;
  reporter_id: number;
  reported_user_id?: number;
  reported_product_id?: number;
  reported_conversation_id?: number;
  reason: string;
  description?: string;
  status: string;
  admin_notes?: string;
  created_at: string;
  resolved_at?: string;
}

export interface KYCSubmission {
  id: number;
  phone: string;
  username: string | null;
  role: string;
  kyc_id_number?: string;
  kyc_id_front_url?: string;
  kyc_selfie_url?: string;
  kyc_submitted_at?: string;
}

export interface Subscription {
  id: number;
  phone: string;
  username: string | null;
  subscription_tier: string;
  subscription_started_at?: string;
  subscription_expires_at?: string;
  featured_listings_used: number;
  is_verified: boolean;
}

export interface ApiError {
  response?: {
    status?: number;
    data?: {
      detail?: string;
    };
  };
}

export interface ActivityLog {
  id: number;
  user_id: number;
  action: string;
  entity_type: string;
  entity_id: number;
  details: string | null;
  created_at: string;
}

export type AdminTab = 'analytics' | 'products' | 'users' | 'kyc' | 'subscriptions' | 'reports' | 'tickets' | 'reviews' | 'broadcast' | 'activity' | 'categories';

export type ReportReason = 'fake_product' | 'scam' | 'harassment' | 'wrong_category' | 'spam' | 'other';

export const REPORT_REASONS: { value: ReportReason; label: string }[] = [
  { value: 'fake_product', label: 'Fake/Defective Product' },
  { value: 'scam', label: 'Scam' },
  { value: 'harassment', label: 'Harassment' },
  { value: 'wrong_category', label: 'Wrong Category' },
  { value: 'spam', label: 'Spam' },
  { value: 'other', label: 'Other' },
];
