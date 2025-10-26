import * as xrpl from 'xrpl';

interface XRPLConfig {
  network: 'mainnet' | 'testnet' | 'devnet';
  serverUrl: string;
}

class XRPLService {
  private client: xrpl.Client | null;
  private isConnected: boolean;
  private reconnectAttempts: number;
  private maxReconnectAttempts: number;
  private reconnectDelay: number;
  private config: XRPLConfig;

  constructor(config?: XRPLConfig) {
    this.client = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 5000; // 5 seconds
    this.config = config || {
      network: 'testnet',
      serverUrl: 'wss://s.altnet.rippletest.net:51233'
    };
  }

  async connect(): Promise<boolean> {
    try {
      this.client = new xrpl.Client(this.config.serverUrl);
      
      this.client.on('connected', () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
      });

      this.client.on('disconnected', () => {
        this.isConnected = false;
        this._handleDisconnection();
      });

      this.client.on('error', (error: Error) => {
        console.error('XRP Ledger client error:', error.message);
      });

      await this.client.connect();
      return true;
    } catch (error: any) {
      throw new Error(`Failed to connect to XRP Ledger: ${error.message}`);
    }
  }

  async _handleDisconnection(): Promise<void> {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;

    setTimeout(async () => {
      try {
        await this.connect();
      } catch (error: any) {
        console.error('Reconnection attempt failed:', error.message);
      }
    }, this.reconnectDelay * this.reconnectAttempts);
  }

  async disconnect(): Promise<void> {
    try {
      if (this.client && this.isConnected) {
        await this.client.disconnect();
      }
    } catch (error: any) {
      console.error('Error disconnecting from XRP Ledger:', error.message);
    }
  }

  generateWallet() {
    try {
      const wallet = xrpl.Wallet.generate();

      return {
        address: wallet.address,
        seed: wallet.seed,
        publicKey: wallet.publicKey
      };
    } catch (error: any) {
      throw new Error(`Failed to generate wallet: ${error.message}`);
    }
  }

  async getBalance(address: string): Promise<number> {
    try {
      if (!this.isConnected || !this.client) {
        throw new Error('Not connected to XRP Ledger');
      }

      const balance = await this.client.getXrpBalance(address);
      return parseFloat(balance);
    } catch (error: any) {
      if (error.message.includes('actNotFound')) {
        // Account doesn't exist yet (hasn't been funded)
        return 0;
      }
      throw new Error(`Failed to get balance: ${error.message}`);
    }
  }

  async getRLUSDBalance(address: string): Promise<number> {
    try {
      const trustlineInfo = await this.checkRLUSDTrustline(address);
      return trustlineInfo.balance;
    } catch (error: any) {
      throw new Error(`Failed to get RLUSD balance: ${error.message}`);
    }
  }

  async getAllBalances(address: string) {
    try {
      const [xrpBalance, rlusdBalance] = await Promise.all([
        this.getBalance(address),
        this.getRLUSDBalance(address)
      ]);

      return {
        xrp: xrpBalance,
        rlusd: rlusdBalance
      };
    } catch (error: any) {
      throw error;
    }
  }

  async sendPayment(senderSeed: string, receiverAddress: string, amount: number, memo: string | null = null) {
    try {
      if (!this.isConnected || !this.client) {
        throw new Error('Not connected to XRP Ledger');
      }

      const senderWallet = xrpl.Wallet.fromSeed(senderSeed);
      
      // Check sender balance first
      const senderBalance = await this.getBalance(senderWallet.address);
      const totalRequired = parseFloat(amount.toString()) + 0.000012; // Add reserve for transaction fee
      
      if (senderBalance < totalRequired) {
        throw new Error(`Insufficient XRP funds. Required: ${totalRequired}, Available: ${senderBalance}`);
      }

      // Prepare payment transaction
      const payment: any = {
        TransactionType: 'Payment',
        Account: senderWallet.address,
        Destination: receiverAddress,
        Amount: xrpl.xrpToDrops(amount.toString())
      };

      // Add memo if provided
      if (memo) {
        payment.Memos = [{
          Memo: {
            MemoData: Buffer.from(memo, 'utf8').toString('hex').toUpperCase()
          }
        }];
      }

      // Submit transaction
      const prepared = await this.client.autofill(payment, {
        maxLedgerVersionOffset: 75
      });
      
      const signed = senderWallet.sign(prepared);
      
      const result: any = await Promise.race([
        this.client.submitAndWait(signed.tx_blob),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Transaction submission timeout after 30 seconds')), 30000)
        )
      ]);

      const success = result.result.meta.TransactionResult === 'tesSUCCESS';

      if (!success) {
        throw new Error(`Transaction failed: ${result.result.meta.TransactionResult}`);
      }

      return {
        success: true,
        hash: signed.hash,
        senderAddress: senderWallet.address,
        receiverAddress,
        amount,
        fee: xrpl.dropsToXrp(prepared.Fee),
        result
      };
    } catch (error: any) {
      throw new Error(`Payment failed: ${error.message}`);
    }
  }

  async sendRLUSDPayment(senderSeed: string, receiverAddress: string, amount: number) {
    try {
      if (!this.isConnected || !this.client) {
        throw new Error('Not connected to XRP Ledger');
      }

      const senderWallet = xrpl.Wallet.fromSeed(senderSeed);
      
      // Check if sender has RLUSD balance
      const rlusdBalance = await this.getRLUSDBalance(senderWallet.address);
      if (rlusdBalance < amount) {
        throw new Error(`Insufficient RLUSD funds. Required: ${amount}, Available: ${rlusdBalance}`);
      }

      // Check if sender has enough XRP for transaction fees
      const xrpBalance = await this.getBalance(senderWallet.address);
      const feeRecommendation = await this.getFeeRecommendation();
      if (xrpBalance < feeRecommendation.recommendedFee) {
        throw new Error(`Insufficient XRP for transaction fee. Need ${feeRecommendation.recommendedFee} XRP`);
      }

      // RLUSD issuer address
      const rlusdIssuer = this.config.network === 'testnet' 
        ? 'rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De' // Testnet RLUSD issuer
        : 'rUSDdLhcFfcgCbvhLPLrHGqy6WpqNFnCVa';  // Mainnet RLUSD issuer

      // Prepare payment transaction
      const payment: any = {
        TransactionType: 'Payment',
        Account: senderWallet.address,
        Destination: receiverAddress,
        Amount: {
          currency: 'USD',
          issuer: rlusdIssuer,
          value: amount.toString()
        }
      };

      // Submit transaction
      const prepared = await this.client.autofill(payment, {
        maxLedgerVersionOffset: 75
      });
      const signed = senderWallet.sign(prepared);
      const result: any = await Promise.race([
        this.client.submitAndWait(signed.tx_blob),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Transaction submission timeout after 30 seconds')), 30000)
        )
      ]);

      const success = result.result.meta.TransactionResult === 'tesSUCCESS';

      if (!success) {
        throw new Error(`RLUSD payment failed: ${result.result.meta.TransactionResult}`);
      }

      return {
        success: true,
        hash: signed.hash,
        fee: xrpl.dropsToXrp(prepared.Fee),
        currency: 'RLUSD',
        result
      };
    } catch (error: any) {
      throw new Error(`RLUSD payment failed: ${error.message}`);
    }
  }

  async getTransactionHistory(address: string, limit: number = 10) {
    try {
      if (!this.isConnected || !this.client) {
        throw new Error('Not connected to XRP Ledger');
      }

      const response: any = await this.client.request({
        command: 'account_tx',
        account: address,
        limit: limit,
        forward: false
      });

      const transactions = response.result.transactions.map((tx: any) => ({
        hash: tx.tx.hash,
        type: tx.tx.TransactionType,
        account: tx.tx.Account,
        destination: tx.tx.Destination,
        amount: tx.tx.Amount ? xrpl.dropsToXrp(tx.tx.Amount) : null,
        fee: xrpl.dropsToXrp(tx.tx.Fee),
        date: new Date((tx.tx.date + 946684800) * 1000).toISOString(), // Convert from Ripple epoch
        validated: tx.validated
      }));

      return transactions;
    } catch (error: any) {
      throw new Error(`Failed to get transaction history: ${error.message}`);
    }
  }

  async validateAddress(address: string): Promise<boolean> {
    try {
      return xrpl.isValidAddress(address);
    } catch (error) {
      return false;
    }
  }

  async getServerInfo() {
    try {
      if (!this.isConnected || !this.client) {
        throw new Error('Not connected to XRP Ledger');
      }

      const response: any = await this.client.request({
        command: 'server_info'
      });

      return {
        network: this.config.network,
        serverUrl: this.config.serverUrl,
        serverInfo: response.result.info,
        connected: this.isConnected
      };
    } catch (error: any) {
      throw new Error(`Failed to get server info: ${error.message}`);
    }
  }

  // Health check method
  async healthCheck() {
    try {
      if (!this.isConnected) {
        return { status: 'unhealthy', service: 'XRPL', error: 'Not connected' };
      }

      await this.getServerInfo();
      return { status: 'healthy', service: 'XRPL' };
    } catch (error: any) {
      return { status: 'unhealthy', service: 'XRPL', error: error.message };
    }
  }

  async createRLUSDTrustline(senderSeed: string, limit: string = '1000000000') {
    try {
      if (!this.isConnected || !this.client) {
        throw new Error('Not connected to XRP Ledger');
      }

      const senderWallet = xrpl.Wallet.fromSeed(senderSeed);
      
      // Check if sender has enough XRP for reserve and fees  
      const balance = await this.getBalance(senderWallet.address);
      const feeRecommendation = await this.getFeeRecommendation();
      const requiredXRP = feeRecommendation.recommendedFee + 0.1; // Small buffer for fees
      
      if (balance < requiredXRP) {
        throw new Error(`Insufficient XRP for trustline creation. Need ${requiredXRP} XRP, have ${balance} XRP`);
      }

      // RLUSD issuer address
      const rlusdIssuer = this.config.network === 'testnet' 
        ? 'rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De' // Testnet RLUSD issuer
        : 'rUSDdLhcFfcgCbvhLPLrHGqy6WpqNFnCVa';  // Mainnet RLUSD issuer

      // Prepare trustline transaction
      const trustSet: any = {
        TransactionType: 'TrustSet',
        Account: senderWallet.address,
        LimitAmount: {
          currency: 'USD',
          issuer: rlusdIssuer,
          value: limit
        }
      };

      // Submit transaction
      const prepared = await this.client.autofill(trustSet, {
        maxLedgerVersionOffset: 75
      });
      const signed = senderWallet.sign(prepared);
      const result: any = await Promise.race([
        this.client.submitAndWait(signed.tx_blob),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Transaction submission timeout after 30 seconds')), 30000)
        )
      ]);

      const success = result.result.meta.TransactionResult === 'tesSUCCESS';

      if (!success) {
        throw new Error(`Trustline creation failed: ${result.result.meta.TransactionResult}`);
      }

      return {
        success: true,
        hash: signed.hash,
        fee: xrpl.dropsToXrp(prepared.Fee),
        result
      };
    } catch (error: any) {
      throw new Error(`Trustline creation failed: ${error.message}`);
    }
  }

  async checkRLUSDTrustline(address: string) {
    try {
      if (!this.isConnected || !this.client) {
        throw new Error('Not connected to XRP Ledger');
      }

      // RLUSD issuer address
      const rlusdIssuer = this.config.network === 'testnet' 
        ? 'rMxCKbEDwqr76QuheSUMdEGf4B9xJ8m5De' // Testnet RLUSD issuer
        : 'rUSDdLhcFfcgCbvhLPLrHGqy6WpqNFnCVa';  // Mainnet RLUSD issuer

      const balances: any = await this.client.request({
        command: 'account_lines',
        account: address,
        ledger_index: 'validated'
      });

      // Check if RLUSD trustline exists
      const rlusdLine = balances.result.lines.find((line: any) => 
        line.currency === 'USD' && line.account === rlusdIssuer
      );

      return {
        exists: !!rlusdLine,
        balance: rlusdLine ? parseFloat(rlusdLine.balance) : 0,
        limit: rlusdLine ? parseFloat(rlusdLine.limit) : 0
      };
    } catch (error: any) {
      if (error.message.includes('actNotFound')) {
        return { exists: false, balance: 0, limit: 0 };
      }
      
      throw new Error(`Failed to check trustline: ${error.message}`);
    }
  }

  // Get network fee recommendations
  async getFeeRecommendation() {
    try {
      if (!this.isConnected || !this.client) {
        throw new Error('Not connected to XRP Ledger');
      }

      const response: any = await this.client.request({
        command: 'server_info'
      });

      const baseFee = response.result.info.validated_ledger.base_fee_xrp;
      const reserveBase = response.result.info.validated_ledger.reserve_base_xrp;

      return {
        baseFee,
        reserveBase,
        recommendedFee: Math.max(baseFee * 1.2, 0.000012) // 20% above base or minimum
      };
    } catch (error: any) {
      return {
        baseFee: 0.00001,
        reserveBase: 10,
        recommendedFee: 0.000012
      };
    }
  }
}

export default new XRPLService();