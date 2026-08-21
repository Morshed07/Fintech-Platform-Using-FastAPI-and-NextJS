'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { Wallet, ArrowLeftRight, CreditCard, ShieldCheck, LogOut, Activity } from 'lucide-react';
import { authApi, healthApi } from '@/lib/api';

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    // Fetch user info
    authApi.getMe()
      .then((u) => setUserEmail(u.email))
      .catch(() => setUserEmail(null));

    // Check system health
    healthApi.checkHealth()
      .then((res) => setIsHealthy(res.status === 'ok'))
      .catch(() => setIsHealthy(false));
  }, [pathname]);

  const handleLogout = async () => {
    await authApi.logout();
    router.push('/login');
  };

  if (pathname === '/login' || pathname === '/register') {
    return null;
  }

  return (
    <nav className="glass-card sticky top-0 z-40 border-b border-gray-800 px-6 py-4">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        {/* Brand Logo */}
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <Wallet className="h-6 w-6" />
          </div>
          <span className="text-xl font-extrabold tracking-tight text-white">
            Nova<span className="text-emerald-400">Pay</span>
          </span>
        </Link>

        {/* Nav Links */}
        <div className="hidden md:flex items-center gap-1 rounded-xl bg-gray-900/60 p-1 border border-gray-800">
          <Link
            href="/dashboard"
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition ${
              pathname === '/dashboard'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Wallet className="h-4 w-4" /> Dashboard
          </Link>
          <Link
            href="/transfers"
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition ${
              pathname === '/transfers'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <ArrowLeftRight className="h-4 w-4" /> Transfers
          </Link>
          <Link
            href="/gateway"
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition ${
              pathname === '/gateway'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <CreditCard className="h-4 w-4" /> Gateway
          </Link>
          <Link
            href="/kyc"
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition ${
              pathname === '/kyc'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <ShieldCheck className="h-4 w-4" /> KYC Verification
          </Link>
        </div>

        {/* User Actions & System Readiness */}
        <div className="flex items-center gap-4">
          {/* Health Status Indicator */}
          <div className="flex items-center gap-2 rounded-full bg-gray-900/80 px-3 py-1 text-xs border border-gray-800">
            <span
              className={`h-2 w-2 rounded-full ${
                isHealthy ? 'bg-emerald-400 animate-pulse' : 'bg-red-500'
              }`}
            />
            <span className="text-gray-400 hidden sm:inline">
              API {isHealthy ? 'Healthy' : 'Connecting'}
            </span>
          </div>

          {userEmail && (
            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-300 font-medium hidden lg:inline">
                {userEmail}
              </span>
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 rounded-lg bg-gray-800 hover:bg-gray-700 px-3 py-2 text-xs font-semibold text-gray-300 hover:text-white transition border border-gray-700"
              >
                <LogOut className="h-4 w-4" /> Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
