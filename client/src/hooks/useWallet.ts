import { useCallback, useMemo, useSyncExternalStore } from "react";
import {
  connectWallet,
  disconnect,
  getWalletState,
  signTransaction,
  subscribe,
} from "../services/wallet";

export function useWallet() {
  const state = useSyncExternalStore(subscribe, getWalletState, getWalletState);

  const handleConnect = useCallback(() => connectWallet(), []);
  const handleDisconnect = useCallback(() => disconnect(), []);
  const handleSign = useCallback(
    (tx: Record<string, unknown>) => signTransaction(tx),
    [],
  );

  return useMemo(
    () => ({
      ...state,
      connect: handleConnect,
      disconnect: handleDisconnect,
      sign: handleSign,
    }),
    [state, handleConnect, handleDisconnect, handleSign],
  );
}
