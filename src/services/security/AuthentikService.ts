interface PasskeyCredential {
  id: string;
  type: 'public-key';
  rawId: ArrayBuffer;
  response: AuthenticatorAttestationResponse | AuthenticatorAssertionResponse;
}

interface UserPasskey {
  id: string;
  userId: string;
  credentialId: string;
  publicKey: string;
  counter: number;
  createdAt: string;
  lastUsed: string;
  deviceName?: string;
  deviceType?: string;
}

interface AuthentikUser {
  pk: number;
  username: string;
  email: string;
  name: string;
  is_active: boolean;
  groups: string[];
  attributes: Record<string, any>;
}

interface AuthentikTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  scope: string;
}

export class AuthentikService {
  private static instance: AuthentikService;
  private baseUrl: string;
  private clientId: string;
  private clientSecret: string;
  private realmName: string;
  private initialized = false;

  private constructor() {
  this.baseUrl = import.meta.env.VITE_AUTHELIA_URL || '';
  this.clientId = import.meta.env.VITE_AUTHELIA_CLIENT_ID || 'fks_trading-platform';
  this.clientSecret = import.meta.env.VITE_AUTHELIA_CLIENT_SECRET || '';
  this.realmName = import.meta.env.VITE_AUTHELIA_REALM || 'fks';
  }

  static getInstance(): AuthentikService {
    if (!AuthentikService.instance) {
      AuthentikService.instance = new AuthentikService();
    }
    return AuthentikService.instance;
  }

  async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      // Allow explicit disable (build-time or runtime localStorage) to silence warnings entirely
      const disabled = (import.meta as any).env?.VITE_DISABLE_AUTH === 'true' || (() => { try { return localStorage.getItem('fks.disable.auth') === 'true' } catch { return false } })()
      if (disabled) {
        console.info('AuthentikService disabled via VITE_DISABLE_AUTH / fks.disable.auth flag.')
        this.initialized = true
        return
      }
      // In dev, allow running without Authentik configured
      if (!this.baseUrl) {
        console.warn('Authentik URL not configured (VITE_AUTHELIA_URL). Security will run in local mode.');
        this.initialized = true;
        return;
      }
      await this.validateAuthentikConnection();
      await this.initializePasskeySupport();
      this.initialized = true;
      console.log('AuthentikService initialized successfully');
    } catch (error) {
      console.error('Failed to initialize AuthentikService:', error);
      // Do not hard-fail the entire app in dev if Authentik is unreachable
      if (import.meta.env.DEV) {
        console.warn('Proceeding without Authentik (DEV mode). Auth features disabled.');
        this.initialized = true;
        return;
      }
      throw error;
    }
  }

  /**
   * Initialize OAuth 2.0 flow with PKCE
   */
  async initiateOAuthFlow(): Promise<string> {
    const codeVerifier = this.generateCodeVerifier();
    const codeChallenge = await this.generateCodeChallenge(codeVerifier);
    const state = this.generateState();
    
    // Store verifier and state in session storage
    sessionStorage.setItem('oauth_code_verifier', codeVerifier);
    sessionStorage.setItem('oauth_state', state);

    const params = new URLSearchParams({
      response_type: 'code',
      client_id: this.clientId,
      redirect_uri: this.getRedirectUri(),
      scope: 'openid profile email groups',
      code_challenge: codeChallenge,
      code_challenge_method: 'S256',
      state: state
    });

    return `${this.baseUrl}/application/o/authorize/?${params.toString()}`;
  }

  /**
   * Complete OAuth flow and get tokens
   */
  async completeOAuthFlow(code: string, state: string): Promise<AuthentikTokenResponse> {
    const storedState = sessionStorage.getItem('oauth_state');
    const codeVerifier = sessionStorage.getItem('oauth_code_verifier');

    if (state !== storedState) {
      throw new Error('Invalid state parameter');
    }

    if (!codeVerifier) {
      throw new Error('Code verifier not found');
    }

    const response = await fetch(`${this.baseUrl}/application/o/token/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        client_id: this.clientId,
        client_secret: this.clientSecret,
        code: code,
        redirect_uri: this.getRedirectUri(),
        code_verifier: codeVerifier
      })
    });

    if (!response.ok) {
      throw new Error(`OAuth token exchange failed: ${response.statusText}`);
    }

    const tokens = await response.json();
    
    // Clean up session storage
    sessionStorage.removeItem('oauth_code_verifier');
    sessionStorage.removeItem('oauth_state');

    return tokens;
  }

  /**
   * Get user info from Authentik
   */
  async getUserInfo(accessToken: string): Promise<AuthentikUser> {
    const response = await fetch(`${this.baseUrl}/application/o/userinfo/`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Failed to get user info: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Register a new passkey for user
   */
  async registerPasskey(userId: string, deviceName?: string): Promise<UserPasskey> {
    if (!this.isPasskeySupported()) {
      throw new Error('Passkeys are not supported in this browser');
    }

    try {
      // Step 1: Get registration options from Authentik
      const optionsResponse = await fetch(`${this.baseUrl}/api/v3/authenticators/webauthn/registration-challenge/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getStoredToken()}`
        },
        body: JSON.stringify({
          user_id: userId,
          username: await this.getUsernameById(userId)
        })
      });

      if (!optionsResponse.ok) {
        throw new Error('Failed to get registration options');
      }

      const options = await optionsResponse.json();

      // Step 2: Create credential using WebAuthn API
      const credential = await navigator.credentials.create({
        publicKey: {
          challenge: this.base64UrlDecode(options.challenge),
          rp: {
            name: 'FKS Trading Platform',
            id: window.location.hostname
          },
          user: {
            id: this.stringToArrayBuffer(userId),
            name: options.user.name,
            displayName: options.user.displayName
          },
          pubKeyCredParams: [
            { alg: -7, type: 'public-key' }, // ES256
            { alg: -257, type: 'public-key' } // RS256
          ],
          authenticatorSelection: {
            authenticatorAttachment: 'platform',
            userVerification: 'required',
            residentKey: 'preferred'
          },
          timeout: 60000,
          attestation: 'direct'
        }
      }) as PublicKeyCredential;

      if (!credential) {
        throw new Error('Failed to create passkey');
      }

      // Step 3: Send registration result to Authentik
      const registrationData = {
        id: credential.id,
        rawId: this.arrayBufferToBase64Url(credential.rawId),
        response: {
          attestationObject: this.arrayBufferToBase64Url(
            (credential.response as AuthenticatorAttestationResponse).attestationObject
          ),
          clientDataJSON: this.arrayBufferToBase64Url(
            credential.response.clientDataJSON
          )
        },
        type: credential.type
      };

      const registrationResponse = await fetch(`${this.baseUrl}/api/v3/authenticators/webauthn/registration-challenge/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getStoredToken()}`
        },
        body: JSON.stringify({
          challenge_id: options.challenge_id,
          credential: registrationData,
          device_name: deviceName || 'Unknown Device'
        })
      });

      if (!registrationResponse.ok) {
        throw new Error('Failed to complete passkey registration');
      }

      const result = await registrationResponse.json();

      return {
        id: result.id,
        userId: userId,
        credentialId: credential.id,
        publicKey: result.public_key,
        counter: 0,
        createdAt: new Date().toISOString(),
        lastUsed: new Date().toISOString(),
        deviceName: deviceName,
        deviceType: this.detectDeviceType()
      };

    } catch (error) {
      console.error('Passkey registration failed:', error);
      throw new Error(`Passkey registration failed: ${error.message}`);
    }
  }

  /**
   * Authenticate using passkey
   */
  async authenticateWithPasskey(username?: string): Promise<AuthentikTokenResponse> {
    if (!this.isPasskeySupported()) {
      throw new Error('Passkeys are not supported in this browser');
    }

    try {
      // Step 1: Get authentication options
      const optionsResponse = await fetch(`${this.baseUrl}/api/v3/authenticators/webauthn/authentication-challenge/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          username: username
        })
      });

      if (!optionsResponse.ok) {
        throw new Error('Failed to get authentication options');
      }

      const options = await optionsResponse.json();

      // Step 2: Get assertion using WebAuthn API
      const assertion = await navigator.credentials.get({
        publicKey: {
          challenge: this.base64UrlDecode(options.challenge),
          allowCredentials: options.allowCredentials?.map((cred: any) => ({
            id: this.base64UrlDecode(cred.id),
            type: 'public-key'
          })),
          userVerification: 'required',
          timeout: 60000
        }
      }) as PublicKeyCredential;

      if (!assertion) {
        throw new Error('Passkey authentication failed');
      }

      // Step 3: Send assertion to Authentik
      const authenticationData = {
        id: assertion.id,
        rawId: this.arrayBufferToBase64Url(assertion.rawId),
        response: {
          authenticatorData: this.arrayBufferToBase64Url(
            (assertion.response as AuthenticatorAssertionResponse).authenticatorData
          ),
          clientDataJSON: this.arrayBufferToBase64Url(
            assertion.response.clientDataJSON
          ),
          signature: this.arrayBufferToBase64Url(
            (assertion.response as AuthenticatorAssertionResponse).signature
          ),
          userHandle: (assertion.response as AuthenticatorAssertionResponse).userHandle ? 
            this.arrayBufferToBase64Url((assertion.response as AuthenticatorAssertionResponse).userHandle!) : null
        },
        type: assertion.type
      };

      const authResponse = await fetch(`${this.baseUrl}/api/v3/authenticators/webauthn/authentication-challenge/`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          challenge_id: options.challenge_id,
          credential: authenticationData
        })
      });

      if (!authResponse.ok) {
        throw new Error('Passkey authentication failed');
      }

      return await authResponse.json();

    } catch (error) {
      console.error('Passkey authentication failed:', error);
      throw new Error(`Passkey authentication failed: ${error.message}`);
    }
  }

  /**
   * List user's registered passkeys
   */
  async getUserPasskeys(userId: string): Promise<UserPasskey[]> {
    const response = await fetch(`${this.baseUrl}/api/v3/authenticators/webauthn/`, {
      headers: {
        'Authorization': `Bearer ${this.getStoredToken()}`
      }
    });

    if (!response.ok) {
      throw new Error('Failed to get user passkeys');
    }

    const passkeys = await response.json();
    
    return passkeys.results?.map((pk: any) => ({
      id: pk.pk,
      userId: pk.user,
      credentialId: pk.credential_id,
      publicKey: pk.public_key,
      counter: pk.sign_count,
      createdAt: pk.created,
      lastUsed: pk.last_used,
      deviceName: pk.name,
      deviceType: this.detectDeviceType()
    })) || [];
  }

  /**
   * Delete a passkey
   */
  async deletePasskey(passkeyId: string): Promise<boolean> {
    const response = await fetch(`${this.baseUrl}/api/v3/authenticators/webauthn/${passkeyId}/`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${this.getStoredToken()}`
      }
    });

    return response.ok;
  }

  /**
   * Check if passkeys are supported
   */
  isPasskeySupported(): boolean {
    return !!(
      window.PublicKeyCredential &&
      navigator.credentials &&
      navigator.credentials.create &&
      navigator.credentials.get
    );
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshToken(refreshToken: string): Promise<AuthentikTokenResponse> {
    const response = await fetch(`${this.baseUrl}/application/o/token/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'refresh_token',
        client_id: this.clientId,
        client_secret: this.clientSecret,
        refresh_token: refreshToken
      })
    });

    if (!response.ok) {
      throw new Error('Failed to refresh token');
    }

    return await response.json();
  }

  /**
   * Logout user and revoke tokens
   */
  async logout(refreshToken: string): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/application/o/revoke/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          client_id: this.clientId,
          client_secret: this.clientSecret,
          token: refreshToken,
          token_type_hint: 'refresh_token'
        })
      });
    } catch (error) {
      console.error('Failed to revoke token:', error);
    }

    // Clear local storage
    localStorage.removeItem('auth_tokens');
    sessionStorage.clear();
  }

  // Utility methods
  private generateCodeVerifier(): string {
    const array = new Uint8Array(32);
    crypto.getRandomValues(array);
    return this.arrayBufferToBase64Url(array.buffer);
  }

  private async generateCodeChallenge(verifier: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(verifier);
    const hash = await crypto.subtle.digest('SHA-256', data);
    return this.arrayBufferToBase64Url(hash);
  }

  private generateState(): string {
    const array = new Uint8Array(16);
    crypto.getRandomValues(array);
    return this.arrayBufferToBase64Url(array.buffer);
  }

  private getRedirectUri(): string {
    return `${window.location.origin}/auth/callback`;
  }

  private arrayBufferToBase64Url(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (const byte of bytes) {
      binary += String.fromCharCode(byte);
    }
    return btoa(binary)
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  }

  private base64UrlDecode(str: string): ArrayBuffer {
    const padding = '='.repeat((4 - (str.length % 4)) % 4);
    const base64 = str.replace(/-/g, '+').replace(/_/g, '/') + padding;
    const binary = atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }

  private stringToArrayBuffer(str: string): ArrayBuffer {
    const encoder = new TextEncoder();
    return encoder.encode(str).buffer;
  }

  private detectDeviceType(): string {
    const userAgent = navigator.userAgent.toLowerCase();
    if (userAgent.includes('mobile')) return 'mobile';
    if (userAgent.includes('tablet')) return 'tablet';
    return 'desktop';
  }

  private async validateAuthentikConnection(): Promise<void> {
    try {
      // Prefer OIDC discovery when available, try multiple base URLs and locations
      const provider = import.meta.env.VITE_AUTHELIA_PROVIDER_SLUG || 'application';
      const host = window.location.hostname;
      const baseCandidates = Array.from(new Set([
        this.baseUrl?.replace(/\/$/, ''),
        `http://auth.${host}`,
        `https://auth.${host}`,
      ].filter(Boolean)));

      let connectedBase: string | null = null;
      for (const base of baseCandidates) {
        const endpoints = [
          `${base}/${provider}/o/.well-known/openid-configuration`,
          `${base}/o/.well-known/openid-configuration`,
          `${base}/-/health/live`,
        ];
        for (const ep of endpoints) {
          try {
            const res = await fetch(ep);
            if (res.ok) {
              connectedBase = base;
              break;
            }
          } catch {}
        }
        if (connectedBase) break;
      }

      if (!connectedBase) throw new Error('Authentik server not reachable');
      // Update baseUrl to the verified working candidate for subsequent flows
      this.baseUrl = connectedBase;
    } catch (error) {
      throw new Error(`Cannot connect to Authentik: ${error.message}`);
    }
  }

  private async initializePasskeySupport(): Promise<void> {
    if (!this.isPasskeySupported()) {
      console.warn('Passkeys not supported in this browser');
    }
  }

  private getStoredToken(): string {
    const tokens = JSON.parse(localStorage.getItem('auth_tokens') || '{}');
    return tokens.access_token || '';
  }

  private async getUsernameById(userId: string): Promise<string> {
    // This would fetch username from user ID
    return `user_${userId}`;
  }

  /**
   * Health check for Authentik service
   */
  async healthCheck(): Promise<{ status: string; details: any }> {
    try {
      const provider = import.meta.env.VITE_AUTHELIA_PROVIDER_SLUG || 'application';
      const discovery = `${this.baseUrl}/${provider}/o/.well-known/openid-configuration`;
      const response = await fetch(discovery);
      let serverReachable = response.ok;
      if (!serverReachable) {
        const live = await fetch(`${this.baseUrl}/-/health/live/`);
        serverReachable = live.ok;
      }
      const passkeySupported = this.isPasskeySupported();
      
      return {
        status: serverReachable ? (response.ok ? 'healthy' : 'degraded') : 'unhealthy',
        details: {
          serverReachable,
          passkeySupported,
          baseUrl: this.baseUrl,
          clientId: this.clientId,
          initialized: this.initialized
        }
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        details: {
          error: error.message,
          baseUrl: this.baseUrl
        }
      };
    }
  }
}

export default AuthentikService;
