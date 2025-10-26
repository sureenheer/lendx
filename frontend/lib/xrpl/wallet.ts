"use client";

import { create } from "zustand";
import { XRPLWalletGenerator, type XRPLWalletData } from "./wallet-generator";

interface WalletState {
  address?: string;
  connected: boolean;
  loading: boolean;
  did?: string;
  seed?: string;
  publicKey?: string;
  privateKey?: string;
  balance?: string;
}

interface WalletStore extends WalletState {
  generateNewWallet: () => Promise<XRPLWalletData>;
  restoreWallet: (seed: string, sequence?: number) => Promise<XRPLWalletData>;
  fundWallet: () => Promise<boolean>;
  getBalance: () => Promise<void>;
  disconnect: () => void;
  generateDID: () => void;
}

export const useWallet = create<WalletStore>((set, get) => ({
  connected: false,
  loading: false,

  generateNewWallet: async () => {
    const { loading } = get();
    if (loading) return {} as XRPLWalletData;

    set({ loading: true });
    try {
      // Generate new XRPL wallet (equivalent to Wallet(seed="s...", sequence=0))
      const walletData = await XRPLWalletGenerator.generateWallet();

      set({
        loading: false,
        connected: true,
        address: walletData.address,
        seed: walletData.seed,
        publicKey: walletData.publicKey,
        privateKey: walletData.privateKey,
        did: walletData.did,
      });

      return walletData;
    } catch (error) {
      console.error("XRPL wallet generation failed", error);
      set({ loading: false, connected: false });
      throw error;
    }
  },

  restoreWallet: async (seed: string, sequence: number = 0) => {
    const { loading } = get();
    if (loading) return {} as XRPLWalletData;

    set({ loading: true });
    try {
      // Restore wallet from seed (equivalent to Wallet(seed="s...", sequence=0))
      const walletData = await XRPLWalletGenerator.restoreWallet(seed, sequence);

      set({
        loading: false,
        connected: true,
        address: walletData.address,
        seed: walletData.seed,
        publicKey: walletData.publicKey,
        privateKey: walletData.privateKey,
        did: walletData.did,
      });

      return walletData;
    } catch (error) {
      console.error("XRPL wallet restoration failed", error);
      set({ loading: false, connected: false });
      throw error;
    }
  },

  fundWallet: async () => {
    const { address } = get();
    if (!address) {
      throw new Error("No wallet address available");
    }

    try {
      const funded = await XRPLWalletGenerator.fundWallet(address);
      if (funded) {
        // Refresh balance after funding
        await get().getBalance();
      }
      return funded;
    } catch (error) {
      console.error("Wallet funding failed", error);
      return false;
    }
  },

  getBalance: async () => {
    const { address } = get();
    if (!address) return;

    try {
      const balance = await XRPLWalletGenerator.getWalletBalance(address);
      set({ balance });
    } catch (error) {
      console.error("Failed to get balance", error);
    }
  },

  disconnect: () => {
    XRPLWalletGenerator.disconnect();
    set({
      connected: false,
      address: undefined,
      loading: false,
      did: undefined,
      seed: undefined,
      publicKey: undefined,
      privateKey: undefined,
      balance: undefined
    });
  },

  generateDID: () => {
    const { address } = get();
    if (address) {
      set({ did: `did:xrpl:${address}` });
    }
  },
}));

export type { WalletState };
