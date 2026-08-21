'use client';

import { useState } from 'react';
import { Wallet } from '@/lib/types';
import { Copy, Check, ShieldCheck, ShieldAlert, ArrowUpRight, ArrowDownLeft, PlusCircle, KeyRound } from 'lucide-react';

interface BalanceCardProps {
  wallet: Wallet | null;
  onOpenSendModal: () => void;
  onOpenDepositModal: () => void;
  onOpenWithdrawModal: () => void;
  onOpenPinModal: () => void;
}

export default function BalanceCard({
  wallet,
  onOpenSendModal,
  onOpenDepositModal,
  onOpenWithdrawModal,
  onOpenPinModal,
}: BalanceCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopyAccount = () => {
    if (wallet?.account_number) {
      navigator.clipboard.writeText(wallet.account_number);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const balanceNum = wallet ? Number(wallet.balance) : 0;

  return (
    <div className="glass-card glass-glow relative overflow-hidden rounded-3xl p-8 border border-emerald-500/20">
      {/* Background Accent Gradients */}
      <div className="absolute -right-20 -top-20 h-64 w-64 rounded-full bg-emerald-500/10 blur-3xl" />
      <div className="absolute -left-20 -bottom-20 h-64 w-64 rounded-full bg-violet-500/10 blur-3xl" />

      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        {/* Left Side: Balance & Account Info */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
              Primary Fiat Wallet
            </span>
            {wallet?.has_pin ? (
              <span className="flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/20">
                <ShieldCheck className="h-3 w-3" /> PIN Active
              </span>
            ) : (
              <button
                onClick={onOpenPinModal}
                className="flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition"
              >
                <ShieldAlert className="h-3 w-3" /> Set Security PIN
              </button>
            )}
          </div>

          {/* Amount Display */}
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-4xl md:text-5xl font-black tracking-tight text-white">
                ${balanceNum.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
              <span className="text-lg font-bold text-gray-400">
                {wallet?.currency || 'USD'}
              </span>
            </div>

            {/* Account Number Copy Pill */}
            <div className="mt-3 flex items-center gap-2">
              <span className="text-xs text-gray-400">Account Number:</span>
              <button
                onClick={handleCopyAccount}
                className="flex items-center gap-1.5 rounded-lg bg-gray-900/80 px-3 py-1 text-xs font-mono font-semibold text-emerald-400 border border-gray-800 hover:border-emerald-500/40 transition"
              >
                <span>{wallet?.account_number || 'ACC-XXXXXXXXXX'}</span>
                {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5 text-gray-400" />}
              </button>
            </div>
          </div>
        </div>

        {/* Right Side: Quick Action Buttons */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <button
            onClick={onOpenSendModal}
            className="flex flex-col items-center justify-center gap-2 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-gray-950 p-4 text-xs font-bold transition shadow-lg shadow-emerald-500/20 hover:scale-[1.02]"
          >
            <ArrowUpRight className="h-6 w-6" />
            Send Money
          </button>

          <button
            onClick={onOpenDepositModal}
            className="flex flex-col items-center justify-center gap-2 rounded-2xl bg-gray-800 hover:bg-gray-700 text-white p-4 text-xs font-bold transition border border-gray-700 hover:scale-[1.02]"
          >
            <PlusCircle className="h-6 w-6 text-emerald-400" />
            Deposit
          </button>

          <button
            onClick={onOpenWithdrawModal}
            className="flex flex-col items-center justify-center gap-2 rounded-2xl bg-gray-800 hover:bg-gray-700 text-white p-4 text-xs font-bold transition border border-gray-700 hover:scale-[1.02]"
          >
            <ArrowDownLeft className="h-6 w-6 text-rose-400" />
            Withdraw
          </button>

          <button
            onClick={onOpenPinModal}
            className="flex flex-col items-center justify-center gap-2 rounded-2xl bg-gray-800 hover:bg-gray-700 text-gray-300 p-4 text-xs font-bold transition border border-gray-700 hover:scale-[1.02]"
          >
            <KeyRound className="h-6 w-6 text-amber-400" />
            Manage PIN
          </button>
        </div>
      </div>
    </div>
  );
}
