export interface User {
  id: number;
  phone: string;
  username: string | null;
  role: string;
  is_active: boolean;
  profile_image: string | null;
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
  created_at: string;
}

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
