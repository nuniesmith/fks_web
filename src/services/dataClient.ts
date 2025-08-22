import axios from 'axios';

import { config } from './config';

import type { AxiosError } from 'axios';

// Resolve data service base: default piggybacks on apiBaseUrl but removes trailing /api if present then appends /data
function computeBase(): string {
  const override = (import.meta as any).env?.VITE_DATA_BASE_URL as string | undefined;
  if (override) return override.replace(/\/$/, '');
  const api = config.apiBaseUrl.replace(/\/$/, '');
  const trimmed = api.endsWith('/api') ? api.slice(0, -4) : api;
  return `${trimmed}/data`;
}

export const dataBaseUrl = computeBase();

export const dataClient = axios.create({
  baseURL: dataBaseUrl,
  timeout: Number(import.meta.env.VITE_DATA_TIMEOUT || import.meta.env.VITE_API_TIMEOUT || 30000),
});

dataClient.interceptors.request.use(req => {
  try {
    const lsToken = typeof window !== 'undefined' ? localStorage.getItem('fks_api_token') : null;
    const envToken = (import.meta as any).env?.VITE_API_TOKEN as string | undefined;
    const authTokensRaw = typeof window !== 'undefined' ? localStorage.getItem('auth_tokens') : null;
    const authAccess = authTokensRaw ? (JSON.parse(authTokensRaw)?.access_token as string | undefined) : undefined;
    const token = authAccess || lsToken || envToken;
    if (token) {
      (req.headers as any) = { ...(req.headers||{}), Authorization: `Bearer ${token}`, 'X-API-Key': token };
    }
  } catch {}
  return req;
});

export interface DataSuccess<T=any> { ok: true; data?: T; [k: string]: any }
export interface DataError { ok: false; error: string; code?: string; [k: string]: any }

export function isDataError(v: any): v is DataError { return v && v.ok === false && typeof v.error === 'string'; }

export async function getData<T=any>(path: string, params?: Record<string, any>): Promise<T> {
  try {
    const res = await dataClient.get(path, { params });
    const j = res.data;
    if (isDataError(j)) throw new Error(j.error);
    return (j?.data ?? j) as T;
  } catch (e) {
    throw wrapError(e);
  }
}

export async function postData<T=any>(path: string, body?: any): Promise<T> {
  try {
    const res = await dataClient.post(path, body);
    const j = res.data;
    if (isDataError(j)) throw new Error(j.error);
    return (j?.data ?? j) as T;
  } catch (e) {
    throw wrapError(e);
  }
}

function wrapError(e: any): Error {
  if (e instanceof Error) return e;
  try {
    if ((e as AxiosError)?.response) {
      const ax = e as AxiosError<any>;
      const status = ax.response?.status;
      const payload = ax.response?.data;
      const msg = payload?.error || payload?.message || ax.message || `HTTP ${status}`;
      return new Error(msg);
    }
  } catch {}
  return new Error(String(e));
}

export default dataClient;
