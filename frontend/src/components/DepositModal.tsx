'use client';

import { useState } from 'react';
import { X, PlusCircle, AlertCircle } from 'lucide-react';
import { gatewayApi, formatErrorMessage } from '@/lib/api';

interface DepositModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function DepositModal({ isOpen, onClose, onSuccess }: DepositModalProps) {
  const [amount, setAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('CARD');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!amount || Number(amount) <= 0) {
      setError('Please enter a valid deposit amount');
      return;
    }

    setLoading(true);
    try {
      await gatewayApi.deposit({
        amount: Number(amount),
        payment_method: paymentMethod,
        description: `Deposit via ${paymentMethod}`,
      });
      onSuccess();
      onClose();
      setAmount('');
    } catch (err: any) {
      setError(formatErrorMessage(err, 'Deposit failed.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <div className="glass-card relative w-full max-w-md rounded-3xl p-8 border border-emerald-500/30 shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400">
              <PlusCircle className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Deposit Funds</h3>
              <p className="text-xs text-gray-400">Simulated Payment Gateway</p>
            </div>
          </div>
          <button onClick={onClose} className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="mt-4 flex items-center gap-2 rounded-xl bg-rose-500/10 p-3 text-xs text-rose-400 border border-rose-500/20">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">Deposit Amount ($ USD)</label>
            <input
              type="number"
              step="0.01"
              min="1.00"
              placeholder="250.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
              className="glass-input w-full rounded-xl px-4 py-3 text-xl font-bold"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">Payment Method</label>
            <select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
              className="glass-input w-full rounded-xl px-4 py-3 text-sm"
            >
              <option value="CARD" className="bg-gray-900 text-white">Credit / Debit Card</option>
              <option value="BANK_TRANSFER" className="bg-gray-900 text-white">Direct Bank Wire</option>
              <option value="GATEWAY" className="bg-gray-900 text-white">Payment Gateway Simulator</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-emerald-500 hover:bg-emerald-400 text-gray-950 py-3.5 text-sm font-bold transition disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Complete Deposit'}
          </button>
        </form>
      </div>
    </div>
  );
}
