import './globals.css';
import type { Metadata } from 'next';
import Navbar from '@/components/Navbar';

export const metadata: Metadata = {
  title: 'NovaPay | Production Digital Wallet & P2P System',
  description: 'High-concurrency digital wallet and double-entry bookkeeping payment system',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#0b0f19] text-gray-100 antialiased selection:bg-emerald-500 selection:text-gray-950">
        <Navbar />
        <main>{children}</main>
      </body>
    </html>
  );
}
