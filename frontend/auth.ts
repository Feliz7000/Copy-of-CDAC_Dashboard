import NextAuth, { type DefaultSession } from "next-auth"
import CredentialsProvider from "next-auth/providers/credentials"
import { authConfig } from "./auth.config"
import { API_BASE_URLS } from "./lib/auth-urls"
import axios from "axios"

declare module "next-auth" {
  interface Session {
    accessToken?: string
    error?: string
    user: {
      id: string
      role: string
      prn?: string
    } & DefaultSession["user"]
  }

  interface User {
    accessToken?: string
    refreshToken?: string
    id: string
    role: string
    prn?: string
  }
}

export const { handlers, auth, signIn, signOut } = NextAuth({
  ...authConfig,
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials?.password) {
          return null
        }

        let lastError = null;
        
        for (const url of API_BASE_URLS) {
          try {
            console.log(`🔑 Trying login at ${url}/token/`);
            const response = await axios.post(`${url}/token/`, {
              username: credentials.username,
              password: credentials.password,
            }, { timeout: 3000 });

            const { access, refresh } = response.data;
            if (!access) continue;

            console.log(`✅ Success at ${url}`);
            
            const payloadBase64 = access.split('.')[1];
            const payloadJson = Buffer.from(payloadBase64, 'base64').toString('utf8');
            const payload = JSON.parse(payloadJson);
            
            let role = "student"; 
            let prn = undefined;
            
            try {
              const userProfileRes = await axios.get(`${url}/users/profile/`, {
                headers: { Authorization: `Bearer ${access}` },
                timeout: 2000
              });
              role = userProfileRes.data.role;
              prn = userProfileRes.data.prn;
            } catch(e) {
               console.warn(`⚠️ Profile fetch failed at ${url}`);
            }

            return {
              id: payload.user_id.toString(),
              name: credentials.username as string,
              accessToken: access,
              refreshToken: refresh,
              role: role,
              prn: prn
            }
          } catch (error: any) {
            lastError = error;
            console.error(`❌ Failed at ${url}: ${error.message}`);
          }
        }

        if (lastError) {
          console.error("❌ ALL AUTH PATHS FAILED", lastError.message);
        }
        return null;
      }
    })
  ],
  session: { strategy: "jwt" },
})
