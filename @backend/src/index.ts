import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import dotenv from 'dotenv';
import { UserService } from '@/services/userService';
import authRoutes from '@/routes/auth';
import didRoutes from '@/routes/did';
import { ApiResponse } from '@/types';

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3001;

// Global services
let userService: UserService;

// Middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", "https://api.auth0.com", "https://*.auth0.com", "wss://s.altnet.rippletest.net", "wss://s1.ripple.com"],
      fontSrc: ["'self'"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
      frameSrc: ["'none'"],
    },
  },
}));

app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    const healthStatus = userService
      ? await userService.getHealthStatus()
      : { auth0: false, xrpl: false, overall: false };

    res.json({
      success: true,
      data: {
        status: 'ok',
        timestamp: new Date().toISOString(),
        services: healthStatus,
        version: '1.0.0'
      }
    } as ApiResponse);
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Health check failed',
      data: {
        status: 'error',
        timestamp: new Date().toISOString()
      }
    } as ApiResponse);
  }
});

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/did', didRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    success: true,
    message: 'LendX XRPL DID Backend API',
    version: '1.0.0',
    endpoints: {
      health: '/health',
      auth: '/api/auth',
      did: '/api/did'
    }
  } as ApiResponse);
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Endpoint not found',
    message: `${req.method} ${req.originalUrl} not found`
  } as ApiResponse);
});

// Global error handler
app.use((error: any, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error('Unhandled error:', error);

  // Handle JWT errors
  if (error.name === 'UnauthorizedError') {
    return res.status(401).json({
      success: false,
      error: 'Invalid or expired token',
      message: 'Authentication failed'
    } as ApiResponse);
  }

  // Handle validation errors
  if (error.name === 'ValidationError') {
    return res.status(400).json({
      success: false,
      error: 'Validation failed',
      message: error.message
    } as ApiResponse);
  }

  // Default error response
  res.status(500).json({
    success: false,
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'production'
      ? 'Something went wrong'
      : error.message
  } as ApiResponse);
});

// Graceful shutdown handler
const gracefulShutdown = async (signal: string) => {
  console.log(`Received ${signal}. Starting graceful shutdown...`);

  if (userService) {
    try {
      await userService.cleanup();
      console.log('User service cleanup completed');
    } catch (error) {
      console.error('Error during user service cleanup:', error);
    }
  }

  process.exit(0);
};

// Handle shutdown signals
process.on('SIGTERM', () => gracefulShutdown('SIGTERM'));
process.on('SIGINT', () => gracefulShutdown('SIGINT'));

// Initialize and start server
async function startServer() {
  try {
    // Validate environment variables
    const requiredEnvVars = [
      'AUTH0_DOMAIN',
      'AUTH0_CLIENT_ID',
      'AUTH0_CLIENT_SECRET',
      'AUTH0_AUDIENCE'
    ];

    const missingEnvVars = requiredEnvVars.filter(varName => !process.env[varName]);
    if (missingEnvVars.length > 0) {
      throw new Error(`Missing required environment variables: ${missingEnvVars.join(', ')}`);
    }

    // Initialize services
    console.log('Initializing user service...');
    userService = new UserService();
    await userService.initialize();
    console.log('User service initialized successfully');

    // Start server
    app.listen(PORT, () => {
      console.log(`🚀 LendX XRPL DID Backend running on port ${PORT}`);
      console.log(`📚 API Documentation available at http://localhost:${PORT}`);
      console.log(`🏥 Health check available at http://localhost:${PORT}/health`);
      console.log(`🔐 Auth endpoints available at http://localhost:${PORT}/api/auth`);
      console.log(`🆔 DID endpoints available at http://localhost:${PORT}/api/did`);
      console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
      console.log(`🔗 XRPL Network: ${process.env.XRPL_NETWORK || 'testnet'}`);
    });

  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

startServer();

export default app;