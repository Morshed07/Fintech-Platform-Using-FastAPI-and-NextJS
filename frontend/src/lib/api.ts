import axios from 'axios';
import { v4 as uuidv4 } from 'uuid';
import {
  User,
  Wallet,
  Transaction,
  TransactionListResponse,
  KYC,
  TokenResponse,
  MessageResponse,
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export function formatErrorMessage(err: any, fallback = 'An error occurred'): string {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail.map((e: any) => e.msg || e.detail || JSON.stringify(e)).join(', ');
  }
  if (typeof detail === 'object' && detail !== null) {
    return detail.msg || JSON.stringify(detail);
  }
  return err?.message || fallback;
}

// Auto-attach JWT Bearer token from localStorage
apiClient.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auth Endpoints
export const authApi = {
  register: async (data: { full_name: string; email: string; password: string }): Promise<MessageResponse> => {
    const res = await apiClient.post('/auth/register', data);
    return res.data;
  },
  verifyOtp: async (data: { email: string; otp: string }): Promise<TokenResponse> => {
    const res = await apiClient.post('/auth/verify-otp', data);
    if (res.data.access_token) {
      localStorage.setItem('access_token', res.data.access_token);
      localStorage.setItem('refresh_token', res.data.refresh_token);
    }
    return res.data;
  },
  login: async (data: { email: string; password: string }): Promise<TokenResponse> => {
    const res = await apiClient.post('/auth/login', data);
    if (res.data.access_token) {
      localStorage.setItem('access_token', res.data.access_token);
      localStorage.setItem('refresh_token', res.data.refresh_token);
    }
    return res.data;
  },
  logout: async (): Promise<void> => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try {
        await apiClient.post('/auth/logout', { refresh_token: refreshToken });
      } catch (e) {
        // Ignore logout errors
      }
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },
  getMe: async (): Promise<User> => {
    const res = await apiClient.get('/auth/me');
    return res.data;
  },
};

// Wallet Endpoints
export const walletApi = {
  getMyWallet: async (): Promise<Wallet> => {
    const res = await apiClient.get('/wallets/me');
    return res.data;
  },
  setPin: async (data: { pin: string; confirm_pin: string }): Promise<MessageResponse> => {
    const res = await apiClient.post('/wallets/pin', data);
    return res.data;
  },
};

// Transfer Endpoints with Idempotency Key
export const transferApi = {
  sendTransfer: async (data: {
    recipient_account_number: string;
    amount: number;
    pin: string;
    description?: string;
  }): Promise<Transaction> => {
    const idempotencyKey = uuidv4();
    const res = await apiClient.post('/transfers', data, {
      headers: {
        'Idempotency-Key': idempotencyKey,
      },
    });
    return res.data;
  },
  getHistory: async (page = 1, size = 20, type?: string): Promise<TransactionListResponse> => {
    const params: any = { page, size };
    if (type) params.transaction_type = type;
    const res = await apiClient.get('/transfers/history', { params });
    return res.data;
  },
  getReceipt: async (transactionId: string): Promise<Transaction> => {
    const res = await apiClient.get(`/transfers/${transactionId}`);
    return res.data;
  },
};

// Gateway Deposit & Withdrawal Endpoints
export const gatewayApi = {
  deposit: async (data: { amount: number; payment_method?: string; description?: string }): Promise<Transaction> => {
    const res = await apiClient.post('/gateway/deposit', data);
    return res.data;
  },
  withdraw: async (data: {
    amount: number;
    pin: string;
    bank_account_number: string;
    bank_code: string;
    description?: string;
  }): Promise<Transaction> => {
    const res = await apiClient.post('/gateway/withdraw', data);
    return res.data;
  },
};

// KYC Endpoints
export const kycApi = {
  getMyKYC: async (): Promise<KYC> => {
    const res = await apiClient.get('/kyc/me');
    return res.data;
  },
  submitKYC: async (data: { document_type: string; document_number: string }): Promise<KYC> => {
    const res = await apiClient.post('/kyc/submit', data);
    return res.data;
  },
};

// Health Endpoint
export const healthApi = {
  checkHealth: async (): Promise<any> => {
    const res = await axios.get('http://localhost:8000/health');
    return res.data;
  },
};
