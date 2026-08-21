'use client';

import { useState } from 'react';
import { X, Send, Lock, AlertCircle } from 'lucide-react';
import { transferApi } from '@/lib/api';

interface P2PTransferModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function P2PTransferModal({ isOpen, onClose, onSuccess }: P2PTransferModalProps) {
  const [recipientAccount, setRecipientAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [pin, setPin] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!recipientAccount.startsWith('ACC-')) {
      setError('Account number must start with ACC-');
      return;
    }

    if (!amount || Number(amount) <= 0) {
      setError('Please enter a valid transfer amount');
      return;
    }

    if (pin.length !== 6 || !/^\d+$/.test(pin)) {
      setError('Please enter your 6-digit numerical security PIN');
      return;
    }

    setLoading(true);
    try {
      await transferApi.sendTransfer({
        recipient_account_number: recipientAccount.trim().toUpperCase(),
        amount: Number(amount),
        pin,
        description: description || undefined,
      });
      onSuccess();
      onClose();
      // Reset form
      setRecipientAccount('');
      setAmount('');
      setPin('');
      setDescription('');
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Transfer failed. Please check details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <div className="glass-card relative w-full max-w-lg rounded-3xl p-8 border border-emerald-500/30 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400">
              <Send className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Send P2P Payment</h3>
              <p className="text-xs text-gray-400">Instant Double-Entry Fund Transfer</p>
            </div>
          </div>
          <button onClick={onClose} className="rounded-lg p-2 text-gray-400 hover:bg-gray-800 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mt-4 flex items-center gap-2 rounded-xl bg-rose-500/10 p-3 text-xs font-medium text-rose-400 border border-rose-500/20">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">
              Recipient Account Number
            </label>
            <input
              type="text"
              placeholder="ACC-XXXXXXXXXX"
              value={recipientAccount}
              onChange={(e) => setRecipientAccount(e.target.value)}
              required
              className="glass-input w-full rounded-xl px-4 py-3 text-sm font-mono tracking-wide"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">
              Amount ($ USD)
            </label>
            <input
              type="number"
              step="0.01"
              min="0.01"
              placeholder="100.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
              className="glass-input w-full rounded-xl px-4 py-3 text-lg font-bold"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">
              Description / Note (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Lunch split"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="glass-input w-full rounded-xl px-4 py-3 text-sm"
            />
          </div>

          <div>
            <label className="flex items-center gap-1 text-xs font-semibold text-emerald-400 mb-1">
              <Lock className="h-3 w-3" /> 6-Digit Security PIN
            </label>
            <input
              type="password"
              maxLength={6}
              placeholder="● ● ● ● ● ●"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              required
              className="glass-input w-full rounded-xl px-4 py-3 text-center text-xl tracking-[0.5em] font-bold"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-emerald-500 hover:bg-emerald-400 text-gray-950 py-3.5 text-sm font-bold transition shadow-lg shadow-emerald-500/20 disabled:opacity-50"
          >
            {loading ? 'Processing Transfer...' : 'Confirm & Send Funds'}
          </button>
        </form>
      </div>
    </div>
  );
}
