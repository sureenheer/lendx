"use client";

import { Wallet, Client } from 'xrpl';

export interface XRPLWalletData {
  address: string;
  seed: string;
  publicKey: string;
  privateKey: string;
  did: string;
}

export class XRPLWalletGenerator {
  private static client: Client | null = null;

  private static async getClient(): Promise<Client> {
    if (!this.client) {
      // Use testnet for development
      this.client = new Client('wss://s.altnet.rippletest.net:51233');
      await this.client.connect();
    }
    return this.client;
  }

  /**
   * Generate a new XRPL wallet using the same pattern as xrpl-py 2.0
   * wallet = Wallet(seed="s...", sequence=0)
   */
  static async generateWallet(): Promise<XRPLWalletData> {
    try {
      // Generate a new wallet (equivalent to Wallet.create() in xrpl-py)
      const wallet = Wallet.generate();

      // Extract wallet information
      const walletData: XRPLWalletData = {
        address: wallet.address,
        seed: wallet.seed || '',
        publicKey: wallet.publicKey,
        privateKey: wallet.privateKey,
        did: `did:xrpl:${wallet.address}`
      };

      return walletData;
    } catch (error) {
      console.error('Failed to generate XRPL wallet:', error);
      throw new Error('Wallet generation failed');
    }
  }

  /**
   * Restore a wallet from a seed (equivalent to Wallet(seed="s...", sequence=0))
   */
  static async restoreWallet(seed: string, sequence: number = 0): Promise<XRPLWalletData> {
    try {
      // Create wallet from seed with sequence (equivalent to Python pattern)
      const wallet = Wallet.fromSeed(seed, { sequence });

      const walletData: XRPLWalletData = {
        address: wallet.address,
        seed: wallet.seed || seed,
        publicKey: wallet.publicKey,
        privateKey: wallet.privateKey,
        did: `did:xrpl:${wallet.address}`
      };

      return walletData;
    } catch (error) {
      console.error('Failed to restore XRPL wallet:', error);
      throw new Error('Wallet restoration failed');
    }
  }

  /**
   * Fund wallet on testnet (for development)
   */
  static async fundWallet(address: string): Promise<boolean> {
    try {
      const client = await this.getClient();

      // Fund the wallet on testnet
      const fundResult = await client.fundWallet();
      console.log('Wallet funded:', fundResult);

      return true;
    } catch (error) {
      console.error('Failed to fund wallet:', error);
      return false;
    }
  }

  /**
   * Get wallet balance
   */
  static async getWalletBalance(address: string): Promise<string> {
    try {
      const client = await this.getClient();

      const response = await client.request({
        command: 'account_info',
        account: address,
        ledger_index: 'validated'
      });

      return response.result.account_data.Balance;
    } catch (error) {
      console.error('Failed to get wallet balance:', error);
      return '0';
    }
  }

  /**
   * Cleanup client connection
   */
  static async disconnect(): Promise<void> {
    if (this.client) {
      await this.client.disconnect();
      this.client = null;
    }
  }
}