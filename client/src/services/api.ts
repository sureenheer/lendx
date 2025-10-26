import axios, { AxiosError } from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ message?: string }>) => {
    const status = error.response?.status;
    const message = error.response?.data?.message ?? error.message;
    console.error(`[API] (${status}) ${message}`);
    return Promise.reject(new Error(message ?? "Request failed"));
  },
);

export interface GroupResponse {
  id: string;
  name: string;
  members: number;
  totalLocked: number;
  depositAccount: string;
  memberDetails: any[];
}

export interface BalancesResponse {
  [address: string]: number;
}

export interface SettlementResponse {
  id: string;
  payments: any[];
  requiredSignatures: number;
  collectedSignatures: number;
  status: string;
}

export async function fetchGroup(groupId: string) {
  const response = await api.get<GroupResponse>(`/groups/${groupId}`);
  return response.data;
}

export async function fetchBalances(groupId: string) {
  const response = await api.get<BalancesResponse>(`/groups/${groupId}/balances`);
  return response.data;
}

export async function fetchSettlement(groupId: string) {
  const response = await api.get<SettlementResponse>(`/groups/${groupId}/settlement`);
  return response.data;
}

export async function signSettlement(proposalId: string) {
  const response = await api.post<SettlementResponse>(`/settlements/${proposalId}/sign`);
  return response.data;
}

export async function broadcastSettlement(proposalId: string) {
  const response = await api.post<SettlementResponse>(`/settlements/${proposalId}/broadcast`);
  return response.data;
}
