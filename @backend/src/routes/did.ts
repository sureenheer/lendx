import { Router, Response } from 'express';
import { Auth0Service } from '@/auth/auth0Service';
import { UserService } from '@/services/userService';
import { AuthenticatedRequest, ApiResponse, VerifiableCredential } from '@/types';

const router = Router();
const auth0Service = new Auth0Service();
const userService = new UserService();

// Middleware to validate JWT tokens
const requireAuth = auth0Service.validateJWT();

/**
 * GET /did/document/:did? - Get DID document for current user or specified DID
 */
router.get('/document/:did?', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userInfo = auth0Service.extractUserFromJWT(req);
    if (!userInfo) {
      return res.status(401).json({
        success: false,
        error: 'Invalid token'
      } as ApiResponse);
    }

    let targetDID = req.params.did;

    // If no DID specified, use current user's DID
    if (!targetDID) {
      const user = await userService.getUserByAuth0Id(userInfo.sub);
      if (!user?.did) {
        return res.status(404).json({
          success: false,
          error: 'User does not have a DID'
        } as ApiResponse);
      }
      targetDID = user.did;
    }

    const didDocument = await userService.getUserDIDDocument(userInfo.sub);
    if (!didDocument) {
      return res.status(404).json({
        success: false,
        error: 'DID document not found'
      } as ApiResponse);
    }

    res.json({
      success: true,
      data: didDocument
    } as ApiResponse);

  } catch (error) {
    console.error('Failed to get DID document:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve DID document'
    } as ApiResponse);
  }
});

/**
 * POST /did/credentials/issue - Issue a new verifiable credential
 */
router.post('/credentials/issue', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userInfo = auth0Service.extractUserFromJWT(req);
    if (!userInfo) {
      return res.status(401).json({
        success: false,
        error: 'Invalid token'
      } as ApiResponse);
    }

    const { credentialType, credentialData } = req.body;

    if (!credentialType || !credentialData) {
      return res.status(400).json({
        success: false,
        error: 'credentialType and credentialData are required'
      } as ApiResponse);
    }

    const credential = await userService.issueCredential(
      userInfo.sub,
      credentialType,
      credentialData
    );

    res.status(201).json({
      success: true,
      data: credential,
      message: 'Credential issued successfully'
    } as ApiResponse);

  } catch (error) {
    console.error('Failed to issue credential:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to issue credential'
    } as ApiResponse);
  }
});

/**
 * POST /did/credentials/verify - Verify a verifiable credential
 */
router.post('/credentials/verify', async (req: Request, res: Response) => {
  try {
    const { credential } = req.body;

    if (!credential) {
      return res.status(400).json({
        success: false,
        error: 'credential is required'
      } as ApiResponse);
    }

    const isValid = await userService.verifyCredential(credential as VerifiableCredential);

    res.json({
      success: true,
      data: {
        valid: isValid,
        credential
      }
    } as ApiResponse);

  } catch (error) {
    console.error('Failed to verify credential:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to verify credential'
    } as ApiResponse);
  }
});

/**
 * GET /did/credentials - Get all credentials for current user
 */
router.get('/credentials', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userInfo = auth0Service.extractUserFromJWT(req);
    if (!userInfo) {
      return res.status(401).json({
        success: false,
        error: 'Invalid token'
      } as ApiResponse);
    }

    const credentials = await userService.getUserCredentials(userInfo.sub);

    res.json({
      success: true,
      data: credentials
    } as ApiResponse);

  } catch (error) {
    console.error('Failed to get user credentials:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to retrieve credentials'
    } as ApiResponse);
  }
});

/**
 * POST /did/credentials/business - Issue business verification credential
 */
router.post('/credentials/business', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userInfo = auth0Service.extractUserFromJWT(req);
    if (!userInfo) {
      return res.status(401).json({
        success: false,
        error: 'Invalid token'
      } as ApiResponse);
    }

    const { businessName, businessType, registrationNumber, documents } = req.body;

    if (!businessName || !businessType) {
      return res.status(400).json({
        success: false,
        error: 'businessName and businessType are required'
      } as ApiResponse);
    }

    const credentialData = {
      businessName,
      businessType,
      registrationNumber,
      documents,
      verifiedAt: new Date().toISOString(),
      verificationLevel: 'business-verified'
    };

    const credential = await userService.issueCredential(
      userInfo.sub,
      'VerifiedBusiness',
      credentialData
    );

    res.status(201).json({
      success: true,
      data: credential,
      message: 'Business credential issued successfully'
    } as ApiResponse);

  } catch (error) {
    console.error('Failed to issue business credential:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to issue business credential'
    } as ApiResponse);
  }
});

/**
 * POST /did/credentials/income - Issue income verification credential
 */
router.post('/credentials/income', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userInfo = auth0Service.extractUserFromJWT(req);
    if (!userInfo) {
      return res.status(401).json({
        success: false,
        error: 'Invalid token'
      } as ApiResponse);
    }

    const { monthlyIncome, currency, source, documents } = req.body;

    if (!monthlyIncome || !currency || !source) {
      return res.status(400).json({
        success: false,
        error: 'monthlyIncome, currency, and source are required'
      } as ApiResponse);
    }

    const credentialData = {
      monthlyIncome,
      currency,
      source,
      documents,
      verifiedAt: new Date().toISOString(),
      verificationLevel: 'income-verified'
    };

    const credential = await userService.issueCredential(
      userInfo.sub,
      'VerifiedIncome',
      credentialData
    );

    res.status(201).json({
      success: true,
      data: credential,
      message: 'Income credential issued successfully'
    } as ApiResponse);

  } catch (error) {
    console.error('Failed to issue income credential:', error);
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to issue income credential'
    } as ApiResponse);
  }
});

/**
 * DELETE /did/deactivate - Deactivate user's DID
 */
router.delete('/deactivate', requireAuth, async (req: AuthenticatedRequest, res: Response) => {
  try {
    const userInfo = auth0Service.extractUserFromJWT(req);
    if (!userInfo) {
      return res.status(401).json({
        success: false,
        error: 'Invalid token'
      } as ApiResponse);
    }

    const success = await userService.deactivateUserDID(userInfo.sub);

    if (success) {
      res.json({
        success: true,
        message: 'DID deactivated successfully'
      } as ApiResponse);
    } else {
      res.status(400).json({
        success: false,
        error: 'Failed to deactivate DID'
      } as ApiResponse);
    }

  } catch (error) {
    console.error('Failed to deactivate DID:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to deactivate DID'
    } as ApiResponse);
  }
});

export default router;