'use client';

import { useState } from 'react';
import { X, KeyRound, ShieldCheck, AlertCircle } from 'lucide-react';
import { walletApi, formatErrorMessage } from '@/lib/api';

interface SetPinModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export default function SetPinModal({ isOpen, onClose, onSuccess }: SetPinModalProps) {
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (pin.length !== 6 || !/^\d+$/.test(pin)) {
      setError('PIN must be exactly 6 digits');
      return;
    }

    if (pin !== confirmPin) {
      setError('PIN and Confirm PIN do not match');
      return;
    }

    setLoading(true);
    try {
      await walletApi.setPin({ pin, confirm_pin: confirmPin });
      onSuccess();
      onClose();
      setPin('');
      setConfirmPin('');
    } catch (err: any) {
      setError(formatErrorMessage(err, 'Failed to update PIN.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
      <div className="glass-card relative w-full max-w-md rounded-3xl p-8 border border-amber-500/30 shadow-2xl">
        <div className="flex items-center justify-between border-b border-gray-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/20 text-amber-400">
              <KeyRound className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white">Manage Security PIN</h3>
              <p className="text-xs text-gray-400">6-Digit Transaction PIN</p>
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
            <label className="block text-xs font-semibold text-gray-300 mb-1">New 6-Digit PIN</label>
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

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">Confirm New 6-Digit PIN</label>
            <input
              type="password"
              maxLength={6}
              placeholder="● ● ● ● ● ●"
              value={confirmPin}
              onChange={(e) => setConfirmPin(e.target.value)}
              required
              className="glass-input w-full rounded-xl px-4 py-3 text-center text-xl tracking-[0.5em] font-bold"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-amber-500 hover:bg-amber-400 text-gray-950 py-3.5 text-sm font-bold transition disabled:opacity-50"
          >
            {loading ? 'Updating PIN...' : 'Save Security PIN'}
          </button>
        </form>
      </div>
    </div>
  );
}
