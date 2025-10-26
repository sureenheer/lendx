"use client";

import { initAuth0 } from '@auth0/nextjs-auth0';

export const auth0 = initAuth0({
  domain: process.env.AUTH0_ISSUER_BASE_URL!,
  clientId: process.env.AUTH0_CLIENT_ID!,
  clientSecret: process.env.AUTH0_CLIENT_SECRET!,
  baseURL: process.env.AUTH0_BASE_URL!,
  issuerBaseURL: process.env.AUTH0_ISSUER_BASE_URL!,
  secret: process.env.AUTH0_SECRET!,
  audience: process.env.AUTH0_AUDIENCE,
  scope: 'openid profile email'
});

export default auth0;