'use client';

import { useState, useEffect } from 'react';
import { kycApi, formatErrorMessage } from '@/lib/api';
import { KYC } from '@/lib/types';
import { ShieldCheck, FileCheck, AlertCircle, CheckCircle2, Award } from 'lucide-react';

export default function KYCPage() {
  const [kyc, setKyc] = useState<KYC | null>(null);
  const [documentType, setDocumentType] = useState('PASSPORT');
  const [documentNumber, setDocumentNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadKYC = async () => {
    try {
      const k = await kycApi.getMyKYC();
      setKyc(k);
    } catch (e) {
      // Ignore
    }
  };

  useEffect(() => {
    loadKYC();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setLoading(true);

    try {
      const updated = await kycApi.submitKYC({
        document_type: documentType,
        document_number: documentNumber,
      });
      setKyc(updated);
      setMessage(`Verification successful! Upgraded to ${updated.tier} ($${Number(updated.daily_limit).toLocaleString()}/day limit).`);
      setDocumentNumber('');
    } catch (err: any) {
      setError(formatErrorMessage(err, 'KYC submission failed.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold text-white">KYC Identity Verification Tiers</h1>
        <p className="text-xs text-gray-400 mt-1">Upgrade your daily P2P transfer and withdrawal limits</p>
      </div>

      {/* Tier Limit Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* TIER_0 */}
        <div
          className={`glass-card rounded-2xl p-6 border ${
            kyc?.tier === 'TIER_0' ? 'border-emerald-500 bg-emerald-500/5' : 'border-gray-800'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gray-400">Basic Tier</span>
            {kyc?.tier === 'TIER_0' && (
              <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-400">
                ACTIVE
              </span>
            )}
          </div>
          <h3 className="text-xl font-black text-white mt-2">TIER 0</h3>
          <p className="text-2xl font-extrabold text-emerald-400 mt-1">$1,000 / day</p>
          <p className="text-[11px] text-gray-400 mt-2">Default verification upon email activation.</p>
        </div>

        {/* TIER_1 */}
        <div
          className={`glass-card rounded-2xl p-6 border ${
            kyc?.tier === 'TIER_1' ? 'border-emerald-500 bg-emerald-500/5' : 'border-gray-800'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-400">Verified Tier</span>
            {kyc?.tier === 'TIER_1' && (
              <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-400">
                ACTIVE
              </span>
            )}
          </div>
          <h3 className="text-xl font-black text-white mt-2">TIER 1</h3>
          <p className="text-2xl font-extrabold text-emerald-400 mt-1">$10,000 / day</p>
          <p className="text-[11px] text-gray-400 mt-2">Requires Passport, NID, or Driver's License.</p>
        </div>

        {/* TIER_2 */}
        <div
          className={`glass-card rounded-2xl p-6 border ${
            kyc?.tier === 'TIER_2' ? 'border-emerald-500 bg-emerald-500/5' : 'border-gray-800'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-violet-400">Enterprise Tier</span>
            {kyc?.tier === 'TIER_2' && (
              <span className="rounded-full bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-400">
                ACTIVE
              </span>
            )}
          </div>
          <h3 className="text-xl font-black text-white mt-2">TIER 2</h3>
          <p className="text-2xl font-extrabold text-violet-400 mt-1">$100,000 / day</p>
          <p className="text-[11px] text-gray-400 mt-2">Full corporate & identity verification.</p>
        </div>
      </div>

      {/* Submission Form */}
      <div className="glass-card rounded-3xl p-8 border border-gray-800 space-y-6">
        <div className="flex items-center gap-3 border-b border-gray-800 pb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400">
            <FileCheck className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Submit Identity Document</h3>
            <p className="text-xs text-gray-400">Instant validation to unlock $10,000/day daily limits</p>
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 rounded-xl bg-rose-500/10 p-3 text-xs text-rose-400 border border-rose-500/20">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {message && (
          <div className="flex items-center gap-2 rounded-xl bg-emerald-500/10 p-3 text-xs text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{message}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">Document Type</label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              className="glass-input w-full rounded-xl px-4 py-3 text-sm"
            >
              <option value="PASSPORT" className="bg-gray-900 text-white">International Passport</option>
              <option value="DRIVERS_LICENSE" className="bg-gray-900 text-white">Driver's License</option>
              <option value="NID" className="bg-gray-900 text-white">National Identification (NID)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 mb-1">Document Identification Number</label>
            <input
              type="text"
              placeholder="e.g. A987654321"
              value={documentNumber}
              onChange={(e) => setDocumentNumber(e.target.value)}
              required
              className="glass-input w-full rounded-xl px-4 py-3 text-sm font-mono"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-emerald-500 hover:bg-emerald-400 text-gray-950 py-3.5 text-sm font-bold transition shadow-lg shadow-emerald-500/20 disabled:opacity-50"
          >
            {loading ? 'Verifying Document...' : 'Submit Document & Upgrade Tier'}
          </button>
        </form>
      </div>
    </div>
  );
}
