'use client';

import { useState } from 'react';
import { Transaction } from '@/lib/types';
import { ArrowUpRight, ArrowDownLeft, Receipt, CheckCircle, Clock } from 'lucide-react';

interface TransactionFeedProps {
  transactions: Transaction[];
  loading: boolean;
}

export default function TransactionFeed({ transactions, loading }: TransactionFeedProps) {
  const [selectedReceipt, setSelectedReceipt] = useState<Transaction | null>(null);

  if (loading) {
    return (
      <div className="glass-card rounded-3xl p-8 border border-gray-800 space-y-4">
        <h3 className="text-lg font-bold text-white mb-4">Recent Transactions</h3>
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-16 rounded-2xl bg-gray-900/60 animate-pulse" />
        ))}
      </div>
    );
  }

  return (
    <div className="glass-card rounded-3xl p-8 border border-gray-800 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-white">Recent Transactions</h3>
          <p className="text-xs text-gray-400">Double-Entry Bookkeeping Ledger Feed</p>
        </div>
        <span className="rounded-full bg-gray-900 px-3 py-1 text-xs font-semibold text-gray-400 border border-gray-800">
          {transactions.length} Activity Events
        </span>
      </div>

      {transactions.length === 0 ? (
        <div className="py-12 text-center text-sm text-gray-400">
          No transaction activity found. Initiate a P2P transfer or deposit to see live entries.
        </div>
      ) : (
        <div className="space-y-3">
          {transactions.map((txn) => {
            const amountNum = Number(txn.amount);
            const isDebit = txn.transaction_type === 'P2P_TRANSFER' || txn.transaction_type === 'WITHDRAWAL';
            const dateStr = new Date(txn.created_at).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            });

            return (
              <div
                key={txn.id}
                onClick={() => setSelectedReceipt(txn)}
                className="flex items-center justify-between rounded-2xl bg-gray-900/50 p-4 border border-gray-800/80 hover:border-gray-700 transition cursor-pointer"
              >
                {/* Icon & Details */}
                <div className="flex items-center gap-4">
                  <div
                    className={`flex h-11 w-11 items-center justify-center rounded-2xl ${
                      isDebit ? 'bg-rose-500/10 text-rose-400' : 'bg-emerald-500/10 text-emerald-400'
                    }`}
                  >
                    {isDebit ? <ArrowUpRight className="h-5 w-5" /> : <ArrowDownLeft className="h-5 w-5" />}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">
                        {txn.transaction_type.replace('_', ' ')}
                      </span>
                      <span className="text-[10px] font-mono font-semibold text-gray-400">
                        {txn.reference_id}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-0.5">
                      {txn.description || 'System transaction'} • {dateStr}
                    </p>
                  </div>
                </div>

                {/* Amount */}
                <div className="text-right">
                  <span
                    className={`text-base font-extrabold ${
                      isDebit ? 'text-rose-400' : 'text-emerald-400'
                    }`}
                  >
                    {isDebit ? '-' : '+'}${amountNum.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                  <div className="flex items-center justify-end gap-1 text-[10px] font-medium text-emerald-400 mt-0.5">
                    <CheckCircle className="h-3 w-3" /> {txn.status}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Receipt Modal */}
      {selectedReceipt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
          <div className="glass-card relative w-full max-w-md rounded-3xl p-8 border border-emerald-500/30 shadow-2xl">
            <div className="flex items-center justify-between border-b border-gray-800 pb-4">
              <div className="flex items-center gap-3">
                <Receipt className="h-6 w-6 text-emerald-400" />
                <h4 className="text-lg font-bold text-white">Transaction Receipt</h4>
              </div>
              <button
                onClick={() => setSelectedReceipt(null)}
                className="rounded-lg p-2 text-gray-400 hover:bg-gray-800"
              >
                ✕
              </button>
            </div>

            <div className="mt-6 space-y-4 text-xs text-gray-300">
              <div className="flex justify-between py-1 border-b border-gray-800">
                <span className="text-gray-400">Reference ID:</span>
                <span className="font-mono font-bold text-emerald-400">{selectedReceipt.reference_id}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-800">
                <span className="text-gray-400">Transaction Type:</span>
                <span className="font-bold">{selectedReceipt.transaction_type}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-800">
                <span className="text-gray-400">Amount:</span>
                <span className="font-bold text-white">${Number(selectedReceipt.amount).toFixed(2)} USD</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-800">
                <span className="text-gray-400">Status:</span>
                <span className="font-bold text-emerald-400">{selectedReceipt.status}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-gray-800">
                <span className="text-gray-400">Date:</span>
                <span>{new Date(selectedReceipt.created_at).toLocaleString()}</span>
              </div>

              {selectedReceipt.ledger_entries && selectedReceipt.ledger_entries.length > 0 && (
                <div className="mt-4 rounded-xl bg-gray-900/80 p-4 border border-gray-800 space-y-2">
                  <h5 className="font-bold text-white text-[11px] uppercase tracking-wider text-emerald-400">
                    Double-Entry Ledger Entries
                  </h5>
                  {selectedReceipt.ledger_entries.map((entry) => (
                    <div key={entry.id} className="flex justify-between text-[11px] py-1 border-b border-gray-800/60">
                      <span className={entry.entry_type === 'DEBIT' ? 'text-rose-400' : 'text-emerald-400'}>
                        {entry.entry_type}
                      </span>
                      <span>${Number(entry.amount).toFixed(2)} (Balance After: ${Number(entry.balance_after).toFixed(2)})</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              onClick={() => setSelectedReceipt(null)}
              className="mt-6 w-full rounded-xl bg-gray-800 hover:bg-gray-700 py-3 text-xs font-bold text-white border border-gray-700 transition"
            >
              Close Receipt
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
