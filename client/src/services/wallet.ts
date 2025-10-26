import { XummSdkJwt } from "@xamanapp/sdk";

type WalletState = {
  address?: string;
  connected: boolean;
  loading: boolean;
};

const apiKey = import.meta.env.VITE_XAMAN_API_KEY ?? "";
const apiSecret = import.meta.env.VITE_XAMAN_API_SECRET ?? "";

const sdk = new XummSdkJwt(apiKey, apiSecret);

let state: WalletState = {
  connected: false,
  loading: false,
};

const subscribers = new Set<() => void>();

function notify() {
  subscribers.forEach((callback) => callback());
}

export function getWalletState() {
  return state;
}

function setState(partial: Partial<WalletState>) {
  state = { ...state, ...partial };
  notify();
}

export async function connectWallet() {
  if (state.loading) return;
  setState({ loading: true });
  try {
    const payload = await sdk.authorize();
    setState({
      loading: false,
      connected: true,
      address: payload?.me?.account,
    });
  } catch (error) {
    console.error("Xaman wallet connection failed", error);
    setState({ loading: false, connected: false, address: undefined });
    throw error;
  }
}

export function disconnect() {
  setState({ connected: false, address: undefined, loading: false });
}

export async function signTransaction(tx: Record<string, unknown>) {
  if (!state.connected || !state.address) {
    throw new Error("Wallet not connected");
  }
  return sdk.sign(tx);
}

export function getAddress() {
  return state.address;
}

export function subscribe(callback: () => void) {
  subscribers.add(callback);
  return () => subscribers.delete(callback);
}
