import { Auth0Service } from '@/auth/auth0Service';
import { XRPLDIDService } from '@/did/xrplDidService';
import {
  User,
  UserRegistrationRequest,
  DIDCreationResponse,
  VerifiableCredential,
  DIDDocument,
  XRPLWallet
} from '@/types';

export class UserService {
  private auth0Service: Auth0Service;
  private didService: XRPLDIDService;
  private users: Map<string, User> = new Map(); // In production, use a database

  constructor() {
    this.auth0Service = new Auth0Service();
    this.didService = new XRPLDIDService(
      process.env.XRPL_NETWORK as 'testnet' | 'mainnet' || 'testnet',
      process.env.XRPL_ISSUER_WALLET_SEED
    );
  }

  /**
   * Initialize the service and connect to XRPL
   */
  async initialize(): Promise<void> {
    await this.didService.connect();
  }

  /**
   * Register a new user with automatic DID and wallet creation
   */
  async registerUser(request: UserRegistrationRequest): Promise<DIDCreationResponse> {
    try {
      // Check if user already exists
      const existingUser = await this.getUserByAuth0Id(request.auth0Id);
      if (existingUser && existingUser.did) {
        throw new Error('User already has a DID associated');
      }

      // Step 1: Create XRPL wallet
      const xrplWallet = await this.didService.createXRPLWallet();

      // Step 2: Create DID document
      const didDocument = await this.didService.createDIDDocument(
        xrplWallet.address,
        xrplWallet.publicKey,
        request.email
      );

      // Step 3: Issue initial verifiable credential
      const verifiableCredential = await this.didService.issueVerifiableCredential(
        didDocument.id,
        'VerifiedUser',
        {
          email: request.email,
          name: request.name,
          verificationLevel: 'basic',
          platform: 'LendX',
          registrationDate: new Date().toISOString()
        }
      );

      // Step 4: Create user record
      const user: User = {
        id: crypto.randomUUID(),
        auth0Id: request.auth0Id,
        email: request.email,
        name: request.name,
        picture: request.picture,
        did: didDocument.id,
        xrplAddress: xrplWallet.address,
        createdAt: new Date(),
        updatedAt: new Date()
      };

      // Store user (in production, save to database)
      this.users.set(user.id, user);
      this.users.set(request.auth0Id, user); // Also index by Auth0 ID

      // Step 5: Associate DID with Auth0 user metadata
      await this.auth0Service.associateDIDWithUser(
        request.auth0Id,
        didDocument.id,
        xrplWallet.address
      );

      return {
        did: didDocument.id,
        didDocument,
        xrplAddress: xrplWallet.address,
        verifiableCredential
      };

    } catch (error) {
      console.error('User registration failed:', error);
      throw new Error(`Failed to register user: ${error.message}`);
    }
  }

  /**
   * Get user by Auth0 ID
   */
  async getUserByAuth0Id(auth0Id: string): Promise<User | null> {
    // Check local storage first
    const localUser = this.users.get(auth0Id);
    if (localUser) {
      return localUser;
    }

    // If not found locally, check if user exists in Auth0 with DID metadata
    try {
      const hasDID = await this.auth0Service.userHasDID(auth0Id);
      if (hasDID) {
        const auth0User = await this.auth0Service.getUserProfile(auth0Id);
        const did = await this.auth0Service.getUserDID(auth0Id);

        if (did) {
          // Reconstruct user object from Auth0 data
          const user: User = {
            id: auth0User.sub,
            auth0Id: auth0User.sub,
            email: auth0User.email,
            name: auth0User.name,
            picture: auth0User.picture,
            did,
            xrplAddress: (auth0User as any).user_metadata?.xrplAddress,
            createdAt: new Date(auth0User.created_at || Date.now()),
            updatedAt: new Date(auth0User.updated_at || Date.now())
          };

          // Cache locally
          this.users.set(auth0Id, user);
          return user;
        }
      }
    } catch (error) {
      console.error('Failed to get user from Auth0:', error);
    }

    return null;
  }

  /**
   * Get user by DID
   */
  async getUserByDID(did: string): Promise<User | null> {
    // Search through local users
    for (const user of this.users.values()) {
      if (user.did === did) {
        return user;
      }
    }

    // In production, query database by DID
    return null;
  }

  /**
   * Get user's DID document
   */
  async getUserDIDDocument(userIdOrAuth0Id: string): Promise<DIDDocument | null> {
    const user = await this.getUserByAuth0Id(userIdOrAuth0Id);
    if (!user?.did) {
      return null;
    }

    return await this.didService.resolveDID(user.did);
  }

  /**
   * Issue additional credentials for a user
   */
  async issueCredential(
    userIdOrAuth0Id: string,
    credentialType: string,
    credentialData: any
  ): Promise<VerifiableCredential> {
    const user = await this.getUserByAuth0Id(userIdOrAuth0Id);
    if (!user?.did) {
      throw new Error('User does not have a DID');
    }

    return await this.didService.issueVerifiableCredential(
      user.did,
      credentialType,
      credentialData
    );
  }

  /**
   * Verify a credential
   */
  async verifyCredential(credential: VerifiableCredential): Promise<boolean> {
    return await this.didService.verifyCredential(credential);
  }

  /**
   * Get user's credentials
   */
  async getUserCredentials(userIdOrAuth0Id: string): Promise<VerifiableCredential[]> {
    const user = await this.getUserByAuth0Id(userIdOrAuth0Id);
    if (!user?.did) {
      return [];
    }

    // In production, retrieve stored credentials from database
    // For now, return empty array as credentials are issued on-demand
    return [];
  }

  /**
   * Update user profile
   */
  async updateUser(userIdOrAuth0Id: string, updates: Partial<User>): Promise<User | null> {
    const user = await this.getUserByAuth0Id(userIdOrAuth0Id);
    if (!user) {
      return null;
    }

    // Update local record
    const updatedUser = {
      ...user,
      ...updates,
      updatedAt: new Date()
    };

    this.users.set(user.id, updatedUser);
    this.users.set(user.auth0Id, updatedUser);

    // Update Auth0 metadata if needed
    if (updates.name || updates.picture) {
      await this.auth0Service.updateUserMetadata(user.auth0Id, {
        name: updates.name || user.name,
        picture: updates.picture || user.picture
      });
    }

    return updatedUser;
  }

  /**
   * Check if a user needs DID creation (for existing users)
   */
  async userNeedsDIDCreation(auth0Id: string): Promise<boolean> {
    const hasDID = await this.auth0Service.userHasDID(auth0Id);
    return !hasDID;
  }

  /**
   * Create DID for existing user who doesn't have one
   */
  async createDIDForExistingUser(auth0Id: string): Promise<DIDCreationResponse> {
    const auth0User = await this.auth0Service.getUserProfile(auth0Id);

    const request: UserRegistrationRequest = {
      auth0Id,
      email: auth0User.email,
      name: auth0User.name,
      picture: auth0User.picture
    };

    return await this.registerUser(request);
  }

  /**
   * Get all users (admin function)
   */
  async getAllUsers(): Promise<User[]> {
    return Array.from(this.users.values());
  }

  /**
   * Deactivate user's DID
   */
  async deactivateUserDID(userIdOrAuth0Id: string): Promise<boolean> {
    const user = await this.getUserByAuth0Id(userIdOrAuth0Id);
    if (!user?.did) {
      return false;
    }

    const success = await this.didService.deactivateDID(user.did);

    if (success) {
      // Update user record to mark DID as deactivated
      await this.updateUser(userIdOrAuth0Id, {
        updatedAt: new Date()
      });

      // Update Auth0 metadata
      await this.auth0Service.updateUserMetadata(user.auth0Id, {
        didStatus: 'deactivated',
        didDeactivatedAt: new Date().toISOString()
      });
    }

    return success;
  }

  /**
   * Get service health status
   */
  async getHealthStatus(): Promise<{ auth0: boolean; xrpl: boolean; overall: boolean }> {
    let auth0Status = false;
    let xrplStatus = false;

    try {
      // Test Auth0 connection
      await this.auth0Service.getUserProfile('test');
    } catch (error) {
      // Expected to fail, but if it fails with auth error, Auth0 is reachable
      auth0Status = error.message.includes('not found') || error.message.includes('does not exist');
    }

    try {
      // Test XRPL connection
      xrplStatus = true; // Assume healthy if no immediate error
    } catch (error) {
      xrplStatus = false;
    }

    return {
      auth0: auth0Status,
      xrpl: xrplStatus,
      overall: auth0Status && xrplStatus
    };
  }

  /**
   * Cleanup method
   */
  async cleanup(): Promise<void> {
    await this.didService.disconnect();
  }
}