'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Wallet, Lock, Mail, AlertCircle } from 'lucide-react';
import { authApi, formatErrorMessage } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');
  const [showOtpInput, setShowOtpInput] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (showOtpInput) {
        await authApi.verifyOtp({ email, otp });
        router.push('/dashboard');
      } else {
        await authApi.login({ email, password });
        router.push('/dashboard');
      }
    } catch (err: any) {
      const msg = formatErrorMessage(err, 'Authentication failed.');
      if (typeof msg === 'string' && msg.includes('not verified')) {
        setShowOtpInput(true);
        setError('Account not verified. Please enter the 6-digit OTP code sent to your email.');
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="glass-card relative w-full max-w-md rounded-3xl p-8 border border-emerald-500/30 shadow-2xl">
        {/* Logo */}
        <div className="flex flex-col items-center justify-center text-center space-y-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <Wallet className="h-7 w-7" />
          </div>
          <h2 className="text-2xl font-black text-white">Welcome Back</h2>
          <p className="text-xs text-gray-400">Sign in to your NovaPay Digital Wallet</p>
        </div>

        {error && (
          <div className="mt-4 flex items-center gap-2 rounded-xl bg-rose-500/10 p-3 text-xs text-rose-400 border border-rose-500/20">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleLogin} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">Email Address</label>
            <div className="relative">
              <input
                type="email"
                placeholder="user@fintech.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="glass-input w-full rounded-xl pl-10 pr-4 py-3 text-sm"
              />
              <Mail className="absolute left-3 top-3.5 h-4 w-4 text-gray-400" />
            </div>
          </div>

          {!showOtpInput ? (
            <div>
              <label className="block text-xs font-semibold text-gray-300 mb-1">Password</label>
              <div className="relative">
                <input
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="glass-input w-full rounded-xl pl-10 pr-4 py-3 text-sm"
                />
                <Lock className="absolute left-3 top-3.5 h-4 w-4 text-gray-400" />
              </div>
            </div>
          ) : (
            <div>
              <label className="block text-xs font-semibold text-emerald-400 mb-1">6-Digit Email OTP</label>
              <input
                type="text"
                maxLength={6}
                placeholder="123456"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                required
                className="glass-input w-full rounded-xl px-4 py-3 text-center text-xl tracking-[0.5em] font-bold"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-emerald-500 hover:bg-emerald-400 text-gray-950 py-3.5 text-sm font-bold transition shadow-lg shadow-emerald-500/20 disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : showOtpInput ? 'Verify OTP & Enter Wallet' : 'Sign In'}
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-gray-400">
          Don't have an account?{' '}
          <Link href="/register" className="font-semibold text-emerald-400 hover:underline">
            Register Account
          </Link>
        </div>
      </div>
    </div>
  );
}
