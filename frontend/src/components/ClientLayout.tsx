'use client';

import { ReactNode } from 'react';
import { ThemeProvider } from '@/context/theme';
import Navbar from '@/components/Navbar';

export default function ClientLayout({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <div className="min-h-screen bg-background">
        <Navbar />
        <main>{children}</main>
      </div>
    </ThemeProvider>
  );
}
