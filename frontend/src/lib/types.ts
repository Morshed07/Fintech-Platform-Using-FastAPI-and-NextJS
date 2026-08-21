export interface User {
  id: string;
  full_name: string;
  email: string;
  avatar_url?: string;
  is_verified: boolean;
  is_active: boolean;
  role: string;
}

export interface Wallet {
  id: string;
  user_id: string;
  account_number: string;
  balance: number | string;
  currency: string;
  status: string;
  has_pin: boolean;
  created_at: string;
  updated_at: string;
}

export interface LedgerEntry {
  id: string;
  wallet_id: string;
  entry_type: 'DEBIT' | 'CREDIT';
  amount: number | string;
  balance_after: number | string;
  created_at: string;
}

export interface Transaction {
  id: string;
  reference_id: string;
  idempotency_key?: string | null;
  transaction_type: 'P2P_TRANSFER' | 'DEPOSIT' | 'WITHDRAWAL' | 'FEE';
  status: 'PENDING' | 'COMPLETED' | 'FAILED';
  amount: number | string;
  currency: string;
  description?: string | null;
  created_at: string;
  ledger_entries: LedgerEntry[];
}

export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  page: number;
  size: number;
}

export interface KYC {
  id: string;
  user_id: string;
  tier: 'TIER_0' | 'TIER_1' | 'TIER_2';
  document_type?: string | null;
  verification_status: 'PENDING' | 'APPROVED' | 'REJECTED';
  daily_limit: number | string;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface MessageResponse {
  message: string;
}
