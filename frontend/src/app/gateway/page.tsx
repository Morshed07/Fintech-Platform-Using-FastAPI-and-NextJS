'use client';

import { useState } from 'react';
import DepositModal from '@/components/DepositModal';
import WithdrawModal from '@/components/WithdrawModal';
import { PlusCircle, ArrowDownLeft, CreditCard, Landmark, CheckCircle2 } from 'lucide-react';

export default function GatewayPage() {
  const [isDepositOpen, setIsDepositOpen] = useState(false);
  const [isWithdrawOpen, setIsWithdrawOpen] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleSuccess = (msg: string) => {
    setSuccessMsg(msg);
    setTimeout(() => setSuccessMsg(null), 4000);
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold text-white">Payment Gateway & Banking</h1>
        <p className="text-xs text-gray-400 mt-1">Simulated Fiat Deposit & External Bank Withdrawal Engine</p>
      </div>

      {successMsg && (
        <div className="flex items-center gap-2 rounded-2xl bg-emerald-500/10 p-4 text-xs font-semibold text-emerald-400 border border-emerald-500/30">
          <CheckCircle2 className="h-5 w-5 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Deposit Card */}
        <div className="glass-card rounded-3xl p-8 border border-emerald-500/20 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 mb-4">
              <CreditCard className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Instant Fiat Deposit</h3>
            <p className="text-xs text-gray-400 mt-1">
              Top up your primary USD wallet using Credit Card or Direct Bank Transfer.
            </p>
          </div>

          <button
            onClick={() => setIsDepositOpen(true)}
            className="flex items-center justify-center gap-2 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-gray-950 py-3.5 text-xs font-bold transition shadow-lg shadow-emerald-500/20"
          >
            <PlusCircle className="h-4 w-4" /> Deposit Funds Now
          </button>
        </div>

        {/* Withdrawal Card */}
        <div className="glass-card rounded-3xl p-8 border border-rose-500/20 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-rose-500/20 text-rose-400 border border-rose-500/30 mb-4">
              <Landmark className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">External Bank Withdrawal</h3>
            <p className="text-xs text-gray-400 mt-1">
              Withdraw wallet funds directly to your external bank routing account. Requires 6-digit PIN.
            </p>
          </div>

          <button
            onClick={() => setIsWithdrawOpen(true)}
            className="flex items-center justify-center gap-2 rounded-2xl bg-rose-500 hover:bg-rose-400 text-white py-3.5 text-xs font-bold transition shadow-lg shadow-rose-500/20"
          >
            <ArrowDownLeft className="h-4 w-4" /> Request Bank Withdrawal
          </button>
        </div>
      </div>

      <DepositModal
        isOpen={isDepositOpen}
        onClose={() => setIsDepositOpen(false)}
        onSuccess={() => handleSuccess('Deposit completed successfully.')}
      />
      <WithdrawModal
        isOpen={isWithdrawOpen}
        onClose={() => setIsWithdrawOpen(false)}
        onSuccess={() => handleSuccess('Withdrawal request executed successfully.')}
      />
    </div>
  );
}
