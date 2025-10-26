import { Router, Response } from 'express';
import { Auth0Service } from '@/auth/auth0Service';
import { UserService } from '@/services/userService';
import { AuthenticatedRequest, ApiResponse, UserRegistrationRequest } from '@/types';

const router = Router();
const auth0Service = new Auth0Service();
const userService = new UserService();

// Middleware to validate JWT tokens
const requireAuth = auth0Service.validateJWT();

/**
 * GET /auth/me - Get current user profile
 */
router.get('/me', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userInfo = auth0Service.extractUserFromJWT(req);
    if (!userInfo) {
      return res.status(401).json({
        success: false,
        error: 'Invalid token'
      } as ApiResponse);
    }

    const user = await userService.getUserByAuth0Id(userInfo.sub);

    res.json({
      success: true,
      data: {
        user,
        needsDIDCreation: !user?.did
      }
    } as ApiResponse);

  } catch (error) {
    console.error('Failed to get user profile:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error'
    } as ApiResponse);
  }
});

/**
 * POST /auth/register - Register new user with DID creation
 */
router.post('/register', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userInfo = auth0Service.extractUserFromJWT(req);
    if (!userInfo) {
      return res.status(401).json({
        success: false,
        error: 'Invalid token'
      } as ApiResponse);
    }

    // Check if user already has DID
    const existingUser = await userService.getUserByAuth0Id(userInfo.sub);
    if (existingUser?.did) {
      return res.status(400).json({
        success: false,
        error: 'User already has a DID',
        data: existingUser
      } as ApiResponse);
    }

    const registrationRequest: UserRegistrationRequest = {
      auth0Id: userInfo.sub,
      email: userInfo.email,
      name: userInfo.name,
      picture: userInfo.picture
    };

    const didCreationResult = await userService.registerUser(registrationRequest);

    res.status(201).json({
      success: true,
      data: didCreationResult,
      message: 'User registered successfully with DID and XRPL wallet'
    } as ApiResponse);

  } catch (error) {
    console.error('User registration failed:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Registration failed'
    } as ApiResponse);
  }
});

/**
 * POST /auth/create-did - Create DID for existing user
 */
router.post('/create-did', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userInfo = auth0Service.extractUserFromJWT(req);
    if (!userInfo) {
      return res.status(401).json({
        success: false,
        error: 'Invalid token'
      } as ApiResponse);
    }

    const needsDID = await userService.userNeedsDIDCreation(userInfo.sub);
    if (!needsDID) {
      return res.status(400).json({
        success: false,
        error: 'User already has a DID'
      } as ApiResponse);
    }

    const didCreationResult = await userService.createDIDForExistingUser(userInfo.sub);

    res.json({
      success: true,
      data: didCreationResult,
      message: 'DID created successfully'
    } as ApiResponse);

  } catch (error) {
    console.error('DID creation failed:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'DID creation failed'
    } as ApiResponse);
  }
});

/**
 * GET /auth/status - Check authentication and DID status
 */
router.get('/status', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userInfo = auth0Service.extractUserFromJWT(req);
    if (!userInfo) {
      return res.status(401).json({
        success: false,
        error: 'Invalid token'
      } as ApiResponse);
    }

    const user = await userService.getUserByAuth0Id(userInfo.sub);
    const needsDIDCreation = await userService.userNeedsDIDCreation(userInfo.sub);

    res.json({
      success: true,
      data: {
        authenticated: true,
        user: userInfo,
        hasStoredProfile: !!user,
        hasDID: !!user?.did,
        needsDIDCreation,
        xrplAddress: user?.xrplAddress
      }
    } as ApiResponse);

  } catch (error) {
    console.error('Status check failed:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to check status'
    } as ApiResponse);
  }
});

export default router;