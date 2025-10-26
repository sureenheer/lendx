import { useCallback, useMemo, useState } from "react";
import { XummSdkJwt } from "xumm";

const apiKey = import.meta.env.VITE_XAMAN_API_KEY ?? "";
const apiSecret = import.meta.env.VITE_XAMAN_API_SECRET ?? "";

const sdk = new XummSdkJwt(apiKey, apiSecret);

export interface WalletState {
  address?: string;
  activated: boolean;
  isConnecting: boolean;
}

export function useXaman() {
  const [walletState, setWalletState] = useState<WalletState>({
    activated: false,
    isConnecting: false,
  });

  const connectWallet = useCallback(async () => {
    setWalletState((prev) => ({ ...prev, isConnecting: true }));
    try {
      const payload = await sdk.authorize();
      setWalletState({
        isConnecting: false,
        activated: true,
        address: payload?.me?.account,
      });
    } catch (error) {
      console.error("Wallet connection failed", error);
      setWalletState({ activated: false, isConnecting: false });
      throw error;
    }
  }, []);

  const signTransaction = useCallback(
    async (tx: Record<string, unknown>) => {
      if (!walletState.address) {
        throw new Error("Connect wallet first");
      }
      const response = await sdk.sign(tx);
      return response;
    },
    [walletState.address],
  );

  const value = useMemo(
    () => ({
      walletState,
      connectWallet,
      signTransaction,
    }),
    [walletState, connectWallet, signTransaction],
  );

  return value;
}
