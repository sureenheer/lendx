import { expressjwt } from 'express-jwt';
import { expressJwtSecret } from 'jwks-rsa';
import axios from 'axios';
import { AuthenticatedRequest, User } from '@/types';

export interface Auth0User {
  sub: string;
  email: string;
  name?: string;
  picture?: string;
  email_verified?: boolean;
  created_at?: string;
  updated_at?: string;
}

export class Auth0Service {
  private domain: string;
  private clientId: string;
  private clientSecret: string;
  private audience: string;
  private managementToken?: string;
  private tokenExpiry?: number;

  constructor() {
    this.domain = process.env.AUTH0_DOMAIN!;
    this.clientId = process.env.AUTH0_CLIENT_ID!;
    this.clientSecret = process.env.AUTH0_CLIENT_SECRET!;
    this.audience = process.env.AUTH0_AUDIENCE!;

    if (!this.domain || !this.clientId || !this.clientSecret || !this.audience) {
      throw new Error('Auth0 configuration is incomplete. Check environment variables.');
    }
  }

  /**
   * Express middleware for JWT validation
   */
  validateJWT() {
    return expressjwt({
      secret: expressJwtSecret({
        cache: true,
        rateLimit: true,
        jwksRequestsPerMinute: 5,
        jwksUri: `https://${this.domain}/.well-known/jwks.json`
      }),
      audience: this.audience,
      issuer: `https://${this.domain}/`,
      algorithms: ['RS256'],
      credentialsRequired: true
    });
  }

  /**
   * Get Management API token
   */
  private async getManagementToken(): Promise<string> {
    // Return cached token if still valid
    if (this.managementToken && this.tokenExpiry && Date.now() < this.tokenExpiry) {
      return this.managementToken;
    }

    try {
      const response = await axios.post(`https://${this.domain}/oauth/token`, {
        client_id: this.clientId,
        client_secret: this.clientSecret,
        audience: `https://${this.domain}/api/v2/`,
        grant_type: 'client_credentials'
      });

      this.managementToken = response.data.access_token;
      // Set expiry to 5 minutes before actual expiry
      this.tokenExpiry = Date.now() + (response.data.expires_in - 300) * 1000;

      return this.managementToken;
    } catch (error) {
      console.error('Failed to get Auth0 management token:', error);
      throw new Error('Failed to authenticate with Auth0 Management API');
    }
  }

  /**
   * Get user profile from Auth0
   */
  async getUserProfile(auth0Id: string): Promise<Auth0User> {
    const token = await this.getManagementToken();

    try {
      const response = await axios.get(
        `https://${this.domain}/api/v2/users/${encodeURIComponent(auth0Id)}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      return response.data;
    } catch (error) {
      console.error('Failed to get user profile from Auth0:', error);
      throw new Error('Failed to retrieve user profile');
    }
  }

  /**
   * Update user metadata in Auth0
   */
  async updateUserMetadata(auth0Id: string, metadata: any): Promise<void> {
    const token = await this.getManagementToken();

    try {
      await axios.patch(
        `https://${this.domain}/api/v2/users/${encodeURIComponent(auth0Id)}`,
        {
          user_metadata: metadata
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );
    } catch (error) {
      console.error('Failed to update user metadata in Auth0:', error);
      throw new Error('Failed to update user metadata');
    }
  }

  /**
   * Add DID information to Auth0 user metadata
   */
  async associateDIDWithUser(auth0Id: string, did: string, xrplAddress: string): Promise<void> {
    const metadata = {
      did,
      xrplAddress,
      didCreatedAt: new Date().toISOString()
    };

    await this.updateUserMetadata(auth0Id, metadata);
  }

  /**
   * Extract user information from JWT payload
   */
  extractUserFromJWT(req: AuthenticatedRequest): { sub: string; email: string; name?: string; picture?: string } | null {
    if (!req.auth) {
      return null;
    }

    return {
      sub: req.auth.sub as string,
      email: req.auth.email as string,
      name: req.auth.name as string,
      picture: req.auth.picture as string
    };
  }

  /**
   * Validate Auth0 token and return user info
   */
  async validateToken(token: string): Promise<Auth0User | null> {
    try {
      const response = await axios.get(`https://${this.domain}/userinfo`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      return response.data;
    } catch (error) {
      console.error('Token validation failed:', error);
      return null;
    }
  }

  /**
   * Get users by email
   */
  async getUserByEmail(email: string): Promise<Auth0User[]> {
    const token = await this.getManagementToken();

    try {
      const response = await axios.get(
        `https://${this.domain}/api/v2/users-by-email`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          },
          params: {
            email: email
          }
        }
      );

      return response.data;
    } catch (error) {
      console.error('Failed to get user by email:', error);
      throw new Error('Failed to retrieve user by email');
    }
  }

  /**
   * Check if user has DID associated
   */
  async userHasDID(auth0Id: string): Promise<boolean> {
    try {
      const user = await this.getUserProfile(auth0Id);
      return !!(user as any).user_metadata?.did;
    } catch (error) {
      console.error('Failed to check if user has DID:', error);
      return false;
    }
  }

  /**
   * Get user's DID from Auth0 metadata
   */
  async getUserDID(auth0Id: string): Promise<string | null> {
    try {
      const user = await this.getUserProfile(auth0Id);
      return (user as any).user_metadata?.did || null;
    } catch (error) {
      console.error('Failed to get user DID:', error);
      return null;
    }
  }
}