'use client';

import { useState, useEffect, use } from 'react';
import { useRouter } from 'next/navigation';
import { productsApi, chatApi, reportsApi, paymentsApi } from '@/lib/api';
import { useAuthStore } from '@/context/auth-store';
import { ApiError, REPORT_REASONS } from '@/types';
import { ArrowLeft, MessageCircle, Clock, Star, MessageSquare, BadgeCheck, Flag, X, Smartphone, Loader2 } from 'lucide-react';

interface ProductDetail {
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
  seller: {
    id: number;
    username: string | null;
    phone: string;
    profile_image: string | null;
    subscription_tier?: string;
    is_verified?: boolean;
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
  const [showReportDialog, setShowReportDialog] = useState(false);
  const [reportReason, setReportReason] = useState('');
  const [reportDescription, setReportDescription] = useState('');
  const [submittingReport, setSubmittingReport] = useState(false);
  const [reportSuccess, setReportSuccess] = useState(false);
  const [showPaymentDialog, setShowPaymentDialog] = useState(false);
  const [paymentPhone, setPaymentPhone] = useState('');
  const [initiatingPayment, setInitiatingPayment] = useState(false);
  const [paymentSuccess, setPaymentSuccess] = useState(false);
  const [checkoutRequestId, setCheckoutRequestId] = useState('');
  const router = useRouter();
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    const productId = Number(id);
    productsApi.get(productId)
      .then(res => {
        setProduct(res.data);
        return res.data.seller?.id;
      })
      .then(sellerId => {
        if (sellerId) {
          return productsApi.getUserRatings(sellerId);
        }
        return null;
      })
      .then(res => {
        if (res) setRatingStats(res.data);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

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
    } catch (err) {
      const e = err as ApiError;
      if (e.response?.status === 400) {
        router.push('/messages');
      } else {
        alert('Could not start conversation. Please try again.');
      }
    } finally {
      setSendingMessage(false);
    }
  };

  const handleReport = async () => {
    if (!reportReason) {
      alert('Please select a reason for reporting');
      return;
    }

    setSubmittingReport(true);
    try {
      await reportsApi.create({
        reason: reportReason,
        description: reportDescription,
        reported_user_id: product.seller_id,
        reported_product_id: product.id,
      });
      setReportSuccess(true);
      setTimeout(() => {
        setShowReportDialog(false);
        setReportSuccess(false);
        setReportReason('');
        setReportDescription('');
      }, 2000);
    } catch (err) {
      const e = err as ApiError;
      alert(e.response?.data?.detail || 'Failed to submit report');
    } finally {
      setSubmittingReport(false);
    }
  };

  const handleInitiatePayment = async () => {
    if (!paymentPhone) {
      alert('Please enter your M-Pesa phone number');
      return;
    }

    setInitiatingPayment(true);
    try {
      const res = await paymentsApi.initiate({
        product_id: product.id,
        phone_number: paymentPhone,
      });
      setCheckoutRequestId(res.data.checkout_request_id);
      setPaymentSuccess(true);
    } catch (err) {
      const e = err as ApiError;
      alert(e.response?.data?.detail || 'Failed to initiate payment. Please try again.');
    } finally {
      setInitiatingPayment(false);
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
              src={product.image_url.startsWith('http') ? product.image_url : `${process.env.NEXT_PUBLIC_API_URL}/uploads/${product.image_url}`}
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
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-medium text-muted-foreground">Seller</h2>
                {!isOwner && (
                  <button
                    onClick={() => setShowReportDialog(true)}
                    className="text-sm text-muted-foreground hover:text-destructive flex items-center gap-1"
                  >
                    <Flag className="w-3 h-3" />
                    Report
                  </button>
                )}
              </div>
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
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-foreground">
                      {product.seller.username || 'Anonymous Seller'}
                    </p>
                    {(product.seller.is_verified || product.seller.subscription_tier === 'standard' || product.seller.subscription_tier === 'premium') && (
                      <span title="Verified Seller">
                        <BadgeCheck className="w-5 h-5 text-blue-500" />
                      </span>
                    )}
                  </div>
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

                <button
                  onClick={() => {
                    if (!isAuthenticated) {
                      router.push('/login');
                      return;
                    }
                    setShowPaymentDialog(true);
                  }}
                  className="w-full py-3 bg-green-600 text-white rounded-full font-medium hover:bg-green-700 transition-colors flex items-center justify-center gap-2"
                >
                  <Smartphone className="w-5 h-5" />
                  Pay with M-Pesa
                </button>

                {product.seller?.phone && (
                  <a
                    href={`https://wa.me/${product.seller.phone.replace('+', '')}?text=Hi, I\'m interested in your "${product.title}" listed for KES ${product.price.toLocaleString()}`}
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
          </div>

          <div className="text-xs text-muted-foreground">
            Posted {new Date(product.created_at).toLocaleDateString()}
          </div>
        </div>
      </div>

      {showReportDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-xl p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-foreground">Report Product</h3>
              <button onClick={() => setShowReportDialog(false)} className="text-muted-foreground hover:text-foreground">
                <X className="w-5 h-5" />
              </button>
            </div>

            {reportSuccess ? (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Star className="w-8 h-8 text-green-500" />
                </div>
                <p className="text-lg font-medium text-foreground">Report Submitted</p>
                <p className="text-sm text-muted-foreground mt-2">Thank you. We will review this report shortly.</p>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  Help us keep the marketplace safe by reporting suspicious content.
                </p>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Reason</label>
                  <select
                    value={reportReason}
                    onChange={(e) => setReportReason(e.target.value)}
                    className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground"
                  >
                    <option value="">Select a reason</option>
                    {REPORT_REASONS.map((reason) => (
                      <option key={reason.value} value={reason.value}>{reason.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Additional details (optional)</label>
                  <textarea
                    value={reportDescription}
                    onChange={(e) => setReportDescription(e.target.value)}
                    rows={3}
                    placeholder="Provide any additional context..."
                    className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground resize-none"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setShowReportDialog(false)}
                    className="flex-1 py-3 border border-input rounded-full text-foreground hover:bg-muted transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleReport}
                    disabled={submittingReport}
                    className="flex-1 py-3 bg-destructive text-destructive-foreground rounded-full font-medium hover:bg-destructive/90 disabled:opacity-50 transition-colors"
                  >
                    {submittingReport ? 'Submitting...' : 'Submit Report'}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {showPaymentDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-background rounded-xl p-6 max-w-md w-full">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-foreground">Pay with M-Pesa</h3>
              <button onClick={() => setShowPaymentDialog(false)} className="text-muted-foreground hover:text-foreground">
                <X className="w-5 h-5" />
              </button>
            </div>

            {paymentSuccess ? (
              <div className="text-center py-6">
                <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Smartphone className="w-8 h-8 text-green-500" />
                </div>
                <p className="text-lg font-medium text-foreground">STK Push Sent!</p>
                <p className="text-sm text-muted-foreground mt-2">
                  Check your phone and enter your PIN to confirm payment of KES {product.price.toLocaleString()}
                </p>
                <p className="text-xs text-muted-foreground mt-4">
                  Order: {checkoutRequestId}
                </p>
                <button
                  onClick={() => setShowPaymentDialog(false)}
                  className="mt-6 py-3 bg-primary text-primary-foreground rounded-full font-medium w-full"
                >
                  Done
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  You will receive an M-Pesa prompt on your phone to confirm payment of <strong>KES {product.price.toLocaleString()}</strong>.
                </p>

                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">M-Pesa Phone Number</label>
                  <input
                    type="tel"
                    value={paymentPhone}
                    onChange={(e) => setPaymentPhone(e.target.value)}
                    placeholder="2547XX XXX XXX"
                    className="w-full px-4 py-3 rounded-lg border border-input bg-background text-foreground"
                  />
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => setShowPaymentDialog(false)}
                    className="flex-1 py-3 border border-input rounded-full text-foreground hover:bg-muted transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleInitiatePayment}
                    disabled={initiatingPayment || !paymentPhone}
                    className="flex-1 py-3 bg-green-600 text-white rounded-full font-medium hover:bg-green-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                  >
                    {initiatingPayment ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      <>Pay KES {product.price.toLocaleString()}</>
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}