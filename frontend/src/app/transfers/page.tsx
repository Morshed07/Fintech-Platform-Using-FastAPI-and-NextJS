'use client';

import { useState, useEffect } from 'react';
import { transferApi } from '@/lib/api';
import { Transaction } from '@/lib/types';
import TransactionFeed from '@/components/TransactionFeed';
import P2PTransferModal from '@/components/P2PTransferModal';
import { ArrowUpRight, Filter } from 'lucide-react';

export default function TransfersPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>('');
  const [isSendOpen, setIsSendOpen] = useState(false);

  const loadTransfers = async () => {
    setLoading(true);
    try {
      const res = await transferApi.getHistory(1, 30, filterType || undefined);
      setTransactions(res.items || []);
    } catch (e) {
      // Ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTransfers();
  }, [filterType]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white">Transfers & Ledger Receipts</h1>
          <p className="text-xs text-gray-400 mt-1">Audit double-entry bookkeeping ledger activity</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-xl bg-gray-900 px-3 py-2 text-xs border border-gray-800">
            <Filter className="h-4 w-4 text-gray-400" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-transparent text-white focus:outline-none"
            >
              <option value="" className="bg-gray-900">All Activity Types</option>
              <option value="P2P_TRANSFER" className="bg-gray-900">P2P Transfers</option>
              <option value="DEPOSIT" className="bg-gray-900">Deposits</option>
              <option value="WITHDRAWAL" className="bg-gray-900">Bank Withdrawals</option>
            </select>
          </div>

          <button
            onClick={() => setIsSendOpen(true)}
            className="flex items-center gap-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-gray-950 px-4 py-2.5 text-xs font-bold transition shadow-lg shadow-emerald-500/20"
          >
            <ArrowUpRight className="h-4 w-4" /> Send Money
          </button>
        </div>
      </div>

      <TransactionFeed transactions={transactions} loading={loading} />

      <P2PTransferModal
        isOpen={isSendOpen}
        onClose={() => setIsSendOpen(false)}
        onSuccess={loadTransfers}
      />
    </div>
  );
}
