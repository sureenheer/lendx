import { handleAuth, handleLogin, handleCallback, handleLogout } from '@auth0/nextjs-auth0';

export const GET = handleAuth({
  login: handleLogin({
    authorizationParams: {
      prompt: 'login',
      scope: 'openid profile email'
    }
  }),
  callback: handleCallback(),
  logout: handleLogout()
});