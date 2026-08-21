'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Wallet, Transaction, KYC, User } from '@/lib/types';
import { walletApi, transferApi, kycApi, authApi } from '@/lib/api';
import BalanceCard from '@/components/BalanceCard';
import TransactionFeed from '@/components/TransactionFeed';
import P2PTransferModal from '@/components/P2PTransferModal';
import DepositModal from '@/components/DepositModal';
import WithdrawModal from '@/components/WithdrawModal';
import SetPinModal from '@/components/SetPinModal';
import { ShieldCheck, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [kyc, setKyc] = useState<KYC | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  // Modal States
  const [isSendOpen, setIsSendOpen] = useState(false);
  const [isDepositOpen, setIsDepositOpen] = useState(false);
  const [isWithdrawOpen, setIsWithdrawOpen] = useState(false);
  const [isPinOpen, setIsPinOpen] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const u = await authApi.getMe();
      setUser(u);

      const w = await walletApi.getMyWallet();
      setWallet(w);

      const k = await kycApi.getMyKYC();
      setKyc(k);

      const txns = await transferApi.getHistory(1, 10);
      setTransactions(txns.items || []);
    } catch (e: any) {
      if (e.response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Welcome & KYC Tier Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white">
            Welcome back, <span className="text-emerald-400">{user?.full_name || 'User'}</span> 👋
          </h1>
          <p className="text-xs text-gray-400 mt-1">Manage your digital wallet and execute P2P transfers</p>
        </div>

        {kyc && (
          <Link
            href="/kyc"
            className="flex items-center gap-3 rounded-2xl bg-gray-900/80 p-3 border border-gray-800 hover:border-emerald-500/40 transition group"
          >
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div className="text-xs">
              <div className="flex items-center gap-1.5 font-bold text-white">
                <span>{kyc.tier} Verified</span>
                <span className="rounded bg-emerald-500/20 px-1.5 py-0.5 text-[10px] text-emerald-400">
                  ${Number(kyc.daily_limit).toLocaleString()}/day
                </span>
              </div>
              <p className="text-[10px] text-gray-400">Click to upgrade limit</p>
            </div>
            <ArrowRight className="h-4 w-4 text-gray-400 group-hover:translate-x-0.5 transition" />
          </Link>
        )}
      </div>

      {/* Main Glass Balance Card */}
      <BalanceCard
        wallet={wallet}
        onOpenSendModal={() => setIsSendOpen(true)}
        onOpenDepositModal={() => setIsDepositOpen(true)}
        onOpenWithdrawModal={() => setIsWithdrawOpen(true)}
        onOpenPinModal={() => setIsPinOpen(true)}
      />

      {/* Live Transaction Feed */}
      <TransactionFeed transactions={transactions} loading={loading} />

      {/* Modals */}
      <P2PTransferModal
        isOpen={isSendOpen}
        onClose={() => setIsSendOpen(false)}
        onSuccess={loadData}
      />
      <DepositModal
        isOpen={isDepositOpen}
        onClose={() => setIsDepositOpen(false)}
        onSuccess={loadData}
      />
      <WithdrawModal
        isOpen={isWithdrawOpen}
        onClose={() => setIsWithdrawOpen(false)}
        onSuccess={loadData}
      />
      <SetPinModal
        isOpen={isPinOpen}
        onClose={() => setIsPinOpen(false)}
        onSuccess={loadData}
      />
    </div>
  );
}
