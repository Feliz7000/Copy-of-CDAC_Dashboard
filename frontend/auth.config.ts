import type { NextAuthConfig } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"
import { TOKEN_REFRESH_PATHS } from "./lib/auth-urls"

// Extracted configuration so it can be used in Edge runtime (Middleware)
export const authConfig = {
  providers: [],
  pages: {
    signIn: '/login',
    error: '/login', // Error code passed in query string as ?error=
  },
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user;
      const isAuthRoute = nextUrl.pathname.startsWith('/login');
      
      // If user is accessing login page while authenticated, redirect to role dashboard
      if (isLoggedIn && isAuthRoute) {
        const role = auth.user.role as string;
        if (role === 'admin') return Response.redirect(new URL('/admin/dashboard', nextUrl));
        if (role === 'hod') return Response.redirect(new URL('/hod/dashboard', nextUrl));
        if (role === 'faculty') return Response.redirect(new URL('/faculty/dashboard', nextUrl));
        if (role === 'student') return Response.redirect(new URL('/student/dashboard', nextUrl));
        return Response.redirect(new URL('/', nextUrl));
      }

      // If user is not authenticated and trying to access a protected route
      if (!isLoggedIn && !isAuthRoute && nextUrl.pathname !== '/') {
        return false;
      }
      
      // Role-based protection
      if (isLoggedIn) {
        const role = auth.user.role as string;
        const path = nextUrl.pathname;
        
        if (path.startsWith('/admin')) {
          if (path.startsWith('/admin/data-management')) {
            if (!['admin', 'faculty', 'hod'].includes(role)) return false;
          } else if (role !== 'admin') {
            return false;
          }
        }
        if (path.startsWith('/hod') && role !== 'hod') return false;
        if (path.startsWith('/faculty') && role !== 'faculty') return false;
        if (path.startsWith('/student') && role !== 'student') return false;
      }

      return true;
    },
    async jwt({ token, user, account }) {
      // Initial sign in
      if (user && account) {
        return {
          ...token,
          accessToken: user.accessToken,
          refreshToken: user.refreshToken,
          accessTokenExpires: Date.now() + 60 * 60 * 1000, // 60 minutes
          id: user.id,
          role: user.role,
          prn: user.prn,
        }
      }
      
      // Return previous token if the access token has not expired yet
      if (Date.now() < (token.accessTokenExpires as number)) {
        return token
      }

      // Access token has expired — try each backend URL (Docker, then local)
      let lastError: unknown = null
      for (const refreshUrl of TOKEN_REFRESH_PATHS) {
        try {
          const response = await fetch(refreshUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh: token.refreshToken }),
          })

          const refreshedTokens = await response.json()
          if (!response.ok) {
            throw refreshedTokens
          }

          return {
            ...token,
            accessToken: refreshedTokens.access,
            accessTokenExpires: Date.now() + 60 * 60 * 1000,
            refreshToken: refreshedTokens.refresh ?? token.refreshToken,
          }
        } catch (error) {
          lastError = error
        }
      }

      console.error("Error refreshing access token", lastError)
      return { ...token, error: "RefreshAccessTokenError" }
    },
    async session({ session, token }) {
      if (token) {
        session.user.id = token.id as string;
        session.user.role = token.role as string;
        session.user.prn = token.prn as string | undefined;
        session.accessToken = token.accessToken as string;
        session.error = token.error as string | undefined;
      }
      return session
    }
  },
} satisfies NextAuthConfig
