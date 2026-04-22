'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { chatApi } from '@/lib/api';
import { useAuthStore } from '@/context/auth-store';
import { useWebSocket } from '@/lib/websocket';
import { ArrowLeft, Send, MessageCircle, Wifi } from 'lucide-react';

interface Conversation {
  id: number;
  product_id: number;
  initiator_id: number;
  receiver_id: number;
  last_message_at: string;
  created_at: string;
  product_title?: string;
  other_username?: string;
  other_profile_image?: string;
  last_message?: string;
  unread: number;
}

interface Message {
  id: number;
  conversation_id: number;
  sender_id: number;
  content: string;
  is_read: boolean;
  message_status?: string;
  created_at: string;
}

function MessagesContent() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, user, token } = useAuthStore();

  const handleWsMessage = (msg: { type: string; data: Record<string, unknown> }) => {
    if (msg.type === 'new_message' && msg.data.conversation_id === selectedId) {
      setMessages(prev => [...prev, {
        id: msg.data.id as number || Date.now(),
        conversation_id: msg.data.conversation_id as number,
        sender_id: msg.data.sender_id as number,
        content: msg.data.content as string,
        is_read: msg.data.is_read as boolean || false,
        message_status: 'sent',
        created_at: msg.data.created_at as string || new Date().toISOString()
      }]);
    }
    if (msg.type === 'message_read' && msg.data.conversation_id === selectedId) {
      setMessages(prev => prev.map(m => 
        m.sender_id === user?.id ? { ...m, message_status: 'read' } : m
      ));
    }
  };

  const { connected } = useWebSocket(token, handleWsMessage);
  useEffect(() => setWsConnected(connected), [connected]);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    loadConversations();
  }, [isAuthenticated, router]);

  useEffect(() => {
    const conversationId = searchParams.get('conversation');
    if (conversationId && conversations.length > 0) {
      selectConversation(Number(conversationId));
    }
  }, [searchParams, conversations]);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const loadConversations = async () => {
    try {
      const res = await chatApi.listConversations();
      setConversations(res.data);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  const selectConversation = async (id: number) => {
    setSelectedId(id);
    try {
      const res = await chatApi.getMessages(id);
      setMessages(res.data);
      await chatApi.markRead(id);
    } catch {
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedId) return;

    const tempId = Date.now();
    const optimisticMessage: Message = {
      id: tempId,
      conversation_id: selectedId,
      sender_id: user!.id,
      content: newMessage.trim(),
      is_read: false,
      message_status: 'sent',
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, optimisticMessage]);
    setNewMessage('');
    setSending(true);

    try {
      const res = await chatApi.sendMessage({
        conversation_id: selectedId,
        content: optimisticMessage.content,
      });
      setMessages(prev => prev.map(m => m.id === tempId ? res.data : m));
    } catch {
      setMessages(prev => prev.filter(m => m.id !== tempId));
      setNewMessage(optimisticMessage.content);
    } finally {
      setSending(false);
    }
  };

  if (!isAuthenticated) return null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="font-serif text-3xl text-foreground">Messages</h1>
          <p className="mt-1 text-muted-foreground">Chat with buyers and sellers</p>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <Wifi className={`w-4 h-4 ${wsConnected ? 'text-green-500' : 'text-muted-foreground'}`} />
          <span className={wsConnected ? 'text-green-600' : 'text-muted-foreground'}>
            {wsConnected ? 'Live' : 'Polling'}
          </span>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-muted-foreground">Loading...</div>
      ) : conversations.length === 0 ? (
        <div className="text-center py-12">
          <MessageCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground mb-4">No conversations yet</p>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 transition-colors"
          >
            Browse Products
          </button>
        </div>
      ) : selectedId ? (
        <div className="border border-border rounded-xl overflow-hidden">
          <div className="bg-muted p-4 flex items-center gap-3">
            <button
              onClick={() => setSelectedId(null)}
              className="p-2 -ml-2 hover:bg-background rounded-full transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <span className="font-medium text-foreground">Chat</span>
          </div>
          
          <div className="h-[400px] overflow-y-auto p-4 space-y-4 bg-background">
            {messages.map(msg => (
              <div
                key={msg.id}
                className={`flex ${msg.sender_id === user?.id ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] px-4 py-2 rounded-2xl ${
                    msg.sender_id === user?.id
                      ? 'bg-primary text-primary-foreground rounded-br-md'
                      : 'bg-muted text-foreground rounded-bl-md'
                  }`}
                >
                  <p>{msg.content}</p>
                  <p className={`text-xs mt-1 flex items-center justify-end gap-1 ${
                    msg.sender_id === user?.id ? 'text-primary-foreground/70' : 'text-muted-foreground'
                  }`}>
                    {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    {msg.sender_id === user?.id && (
                      <span className={msg.message_status === 'read' ? 'text-blue-400' : 'text-primary-foreground/70'}>
                        {msg.message_status === 'read' ? '✓✓' : '✓'}
                      </span>
                    )}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSend} className="p-4 border-t border-border">
            <div className="flex gap-2">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                placeholder="Type a message..."
                className="flex-1 px-4 py-3 rounded-full border border-input bg-background text-foreground placeholder:text-muted-foreground focus:border-primary focus:ring-0 transition-colors"
              />
              <button
                type="submit"
                disabled={sending || !newMessage.trim()}
                className="p-3 bg-primary text-primary-foreground rounded-full hover:bg-primary/90 disabled:opacity-50 transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </form>
        </div>
      ) : (
        <div className="space-y-2">
          {conversations.map(conv => (
            <button
              key={conv.id}
              onClick={() => selectConversation(conv.id)}
              className="w-full p-4 text-left border border-border rounded-xl hover:bg-muted transition-colors"
            >
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center overflow-hidden">
                  {conv.other_profile_image ? (
                    <img
                      src={`${process.env.NEXT_PUBLIC_API_URL}/uploads/${conv.other_profile_image}`}
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <span className="text-lg font-medium text-muted-foreground">
                      {(conv.other_username || '?').charAt(0).toUpperCase()}
                    </span>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-foreground truncate">
                    {conv.other_username || 'Anonymous'}
                  </p>
                  <p className="text-sm text-muted-foreground truncate">
                    {conv.product_title || 'Product chat'}
                  </p>
                </div>
                {conv.unread > 0 && (
                  <span className="px-2 py-1 bg-primary text-primary-foreground text-xs font-medium rounded-full">
                    {conv.unread}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function MessagesPage() {
  return (
    <Suspense fallback={<div className="max-w-4xl mx-auto px-4 py-8 text-center">Loading...</div>}>
      <MessagesContent />
    </Suspense>
  );
}