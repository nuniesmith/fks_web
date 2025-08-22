import AuthentikService from './AuthentikService';
import PerformanceMonitor from './PerformanceMonitor';
import TailscaleService from './TailscaleService';
// Lazy-load GoogleOAuthService to avoid bundling googleapis into initial load
type GoogleOAuthService = import('../GoogleOAuthService').default;

interface SecurityConfig {
  enforceVPN: boolean;
  requirePasskeys: boolean;
  performanceMonitoring: boolean;
  secretRotation: boolean;
  auditLogging: boolean;
  googleOAuth: boolean;
  authProvider: 'authelia' | 'google' | 'both';
}

interface SecurityStatus {
  vpn: {
    connected: boolean;
    status: string;
  };
  authentication: {
    method: 'passkey' | 'oauth' | 'none';
    authenticated: boolean;
    user?: any;
  };
  performance: {
    monitoring: boolean;
    status: string;
  };
  secrets: {
    encrypted: boolean;
    rotationEnabled: boolean;
  };
  overall: 'secure' | 'warning' | 'critical';
}

interface SecurityEvent {
  type: 'authentication' | 'authorization' | 'vpn' | 'performance' | 'audit';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  timestamp: number;
  resolved: boolean;
  details?: Record<string, any>;
}

export class SecurityOrchestrator {
  private static instance: SecurityOrchestrator;
  private tailscaleService: TailscaleService;
  private autheliaService: AuthentikService;
  private performanceMonitor: PerformanceMonitor;
  private googleOAuthService?: GoogleOAuthService;
  private config: SecurityConfig;
  private initialized = false;
  private securityEvents: SecurityEvent[] = [];
  private eventListeners: ((event: SecurityEvent) => void)[] = [];

  private constructor() {
    this.tailscaleService = TailscaleService.getInstance();
    this.autheliaService = AuthentikService.getInstance();
    this.performanceMonitor = PerformanceMonitor.getInstance();
    // Runtime override for Google OAuth enablement via localStorage
    const googleOAuthOverride = localStorage.getItem('security.googleOAuth');
    const googleOAuthEnabled =
      googleOAuthOverride !== null
        ? googleOAuthOverride === 'true'
        : import.meta.env.VITE_GOOGLE_OAUTH === 'true';

    this.config = {
      enforceVPN: import.meta.env.VITE_ENFORCE_VPN !== 'false',
      requirePasskeys: import.meta.env.VITE_REQUIRE_PASSKEYS === 'true',
      performanceMonitoring: import.meta.env.VITE_PERFORMANCE_MONITORING !== 'false',
      secretRotation: import.meta.env.VITE_SECRET_ROTATION !== 'false',
      auditLogging: import.meta.env.VITE_AUDIT_LOGGING !== 'false',
      // Default Google OAuth to disabled unless explicitly enabled
      googleOAuth: googleOAuthEnabled,
      // Default to Authentik-first
      authProvider: (import.meta.env.VITE_AUTH_PROVIDER as 'authelia' | 'google' | 'both') || 'authelia'
    };
  }

  static getInstance(): SecurityOrchestrator {
    if (!SecurityOrchestrator.instance) {
      SecurityOrchestrator.instance = new SecurityOrchestrator();
    }
    return SecurityOrchestrator.instance;
  }

  /**
   * Initialize all security services
   */
  async initialize(): Promise<void> {
    if (this.initialized) return;

    console.log('Initializing Security Orchestrator...');

    try {
      // If Google OAuth is disabled, sanitize any stale client-side Google auth state
      if (!this.config.googleOAuth) {
        const prev = localStorage.getItem('auth_provider');
        if (prev === 'google') {
          localStorage.removeItem('current_user_id');
          localStorage.removeItem('auth_provider');
          this.logSecurityEvent({
            type: 'authentication',
            severity: 'low',
            message: 'Google OAuth disabled; cleared stale Google session state',
            timestamp: Date.now(),
            resolved: true,
            details: { cleared: ['current_user_id', 'auth_provider'] }
          });
        }
      }

      // Initialize services in order of priority
      
      // 1. Tailscale (highest priority)
      if (this.config.enforceVPN) {
        await this.tailscaleService.initialize();
        this.logSecurityEvent({
          type: 'vpn',
          severity: 'low',
          message: 'Tailscale VPN initialized successfully',
          timestamp: Date.now(),
          resolved: true
        });
      }

      // 2. Authentication service
      if (this.config.authProvider === 'authelia' || this.config.authProvider === 'both') {
        await this.autheliaService.initialize();
        this.logSecurityEvent({
          type: 'authentication',
          severity: 'low',
          message: 'Authentik service initialized successfully',
          timestamp: Date.now(),
          resolved: true
        });
      }

      if (this.config.googleOAuth && (this.config.authProvider === 'google' || this.config.authProvider === 'both')) {
        try {
          if (!this.googleOAuthService) {
            const mod = await import('../GoogleOAuthService');
            this.googleOAuthService = mod.default.getInstance();
          }
          await this.googleOAuthService!.initialize();
          this.logSecurityEvent({
            type: 'authentication',
            severity: 'low',
            message: 'Google OAuth service initialized successfully',
            timestamp: Date.now(),
            resolved: true
          });
        } catch (err: any) {
          // If the browser shim throws (googleapis not available), downgrade severity and continue
          const msg = err?.message || String(err);
          this.logSecurityEvent({
            type: 'authentication',
            severity: 'medium',
            message: `Google OAuth init skipped: ${msg}`,
            timestamp: Date.now(),
            resolved: false,
            details: { provider: 'google', skipped: true }
          });
          // Disable Google for this session to avoid further attempts
          this.config.googleOAuth = false;
        }
      }

      // 3. Performance monitoring
      if (this.config.performanceMonitoring) {
        this.performanceMonitor.startMonitoring();
        this.logSecurityEvent({
          type: 'performance',
          severity: 'low',
          message: 'Performance monitoring started',
          timestamp: Date.now(),
          resolved: true
        });
      }

      // 4. Setup security validation middleware
      await this.setupSecurityMiddleware();

      this.initialized = true;
      console.log('Security Orchestrator initialized successfully');

  } catch (error: any) {
      this.logSecurityEvent({
        type: 'audit',
        severity: 'critical',
        message: `Security initialization failed: ${error.message}`,
        timestamp: Date.now(),
        resolved: false,
        details: { error: error.message }
      });
      throw error;
    }
  }

  /**
   * Validate complete security posture before allowing access
   */
  async validateSecurityPosture(): Promise<SecurityStatus> {
    const status: SecurityStatus = {
      vpn: { connected: false, status: 'unknown' },
      authentication: { method: 'none', authenticated: false },
      performance: { monitoring: false, status: 'unknown' },
      secrets: { encrypted: false, rotationEnabled: false },
      overall: 'critical'
    };

    try {
      // Check VPN status
      if (this.config.enforceVPN) {
        const vpnConnected = await this.tailscaleService.isConnectedViaTailscale();
        status.vpn = {
          connected: vpnConnected,
          status: vpnConnected ? 'connected' : 'disconnected'
        };

        if (!vpnConnected) {
          this.logSecurityEvent({
            type: 'vpn',
            severity: 'critical',
            message: 'VPN connection required but not detected',
            timestamp: Date.now(),
            resolved: false
          });
        }
      } else {
        status.vpn = { connected: true, status: 'bypassed' };
      }

      // Check authentication status
      const authToken = localStorage.getItem('auth_tokens');
      if (authToken) {
        try {
          const tokens = JSON.parse(authToken);
          const userInfo = await this.autheliaService.getUserInfo(tokens.access_token);
          status.authentication = {
            method: 'oauth',
            authenticated: true,
            user: userInfo
          };
        } catch (error) {
          status.authentication = {
            method: 'none',
            authenticated: false
          };
        }
      }

      // Check performance monitoring
      const perfHealth = this.performanceMonitor.healthCheck();
      status.performance = {
        monitoring: perfHealth.status === 'monitoring',
        status: perfHealth.status
      };

      // Check secrets management
      status.secrets = {
        encrypted: true, // SecretManager always encrypts
        rotationEnabled: this.config.secretRotation
      };

      // Determine overall status
      status.overall = this.calculateOverallStatus(status);

      return status;

    } catch (error) {
      this.logSecurityEvent({
        type: 'audit',
        severity: 'high',
        message: `Security validation failed: ${error.message}`,
        timestamp: Date.now(),
        resolved: false,
        details: { error: error.message }
      });

      status.overall = 'critical';
      return status;
    }
  }

  /**
   * Enforce security policies before API calls
   */
  async enforceSecurityPolicies(): Promise<void> {
    // 1. Enforce VPN connection (highest priority)
    if (this.config.enforceVPN) {
      await this.tailscaleService.enforceVPNConnection();
    }

    // 2. Validate authentication
    const isAuthenticated = await this.validateAuthentication();
    if (!isAuthenticated) {
      throw new Error('Authentication required');
    }

    // 3. Record security validation
    this.performanceMonitor.recordSecurityMetric({
      type: 'authorization',
      event: 'policy_enforcement',
      success: true,
      duration: 0
    });
  }

  /**
   * Initiate secure authentication flow
   */
  async initiateAuthentication(preferPasskey: boolean = true, provider: 'authelia' | 'google' = 'authelia'): Promise<string> {
    try {
      // Try passkey first if supported and preferred (Authentik only)
      if (preferPasskey && provider === 'authelia' && this.autheliaService.isPasskeySupported()) {
        try {
          const tokens = await this.autheliaService.authenticateWithPasskey();
          localStorage.setItem('auth_tokens', JSON.stringify(tokens));
          
          this.logSecurityEvent({
            type: 'authentication',
            severity: 'low',
            message: 'Passkey authentication successful',
            timestamp: Date.now(),
            resolved: true
          });

          return 'passkey';
        } catch (passkeyError) {
          console.warn('Passkey authentication failed, falling back to OAuth:', passkeyError);
        }
      }

      // Google OAuth flow
      if (provider === 'google') {
        if (!this.config.googleOAuth) {
          throw new Error('Google OAuth disabled in client (enable VITE_GOOGLE_OAUTH=true)');
        }
        try {
          if (!this.googleOAuthService) {
            const mod = await import('../GoogleOAuthService');
            this.googleOAuthService = mod.default.getInstance();
          }
          const authUrl = this.googleOAuthService!.getAuthUrl();
          return authUrl;
        } catch (err: any) {
          throw new Error(`Google OAuth not available in browser: ${err?.message || err}`);
        }
      }

      // Authentik OAuth flow
      if (provider === 'authelia') {
        const authUrl = await this.autheliaService.initiateOAuthFlow();
        return authUrl;
      }

      throw new Error('No valid authentication provider configured');

  } catch (error: any) {
      this.logSecurityEvent({
        type: 'authentication',
        severity: 'high',
        message: `Authentication initiation failed: ${error.message}`,
        timestamp: Date.now(),
        resolved: false,
        details: { error: error.message, provider }
      });
      throw error;
    }
  }

  /**
   * Complete OAuth authentication
   */
  async completeAuthentication(code: string, state: string, provider: 'authelia' | 'google' = 'authelia'): Promise<any> {
    try {
      let user: any;

      if (provider === 'google') {
        if (!this.config.googleOAuth) {
          throw new Error('Google OAuth disabled in client');
        }
        try {
          if (!this.googleOAuthService) {
            const mod = await import('../GoogleOAuthService');
            this.googleOAuthService = mod.default.getInstance();
          }
          user = await this.googleOAuthService!.handleOAuthCallback(code, state);
          localStorage.setItem('current_user_id', user.id);
          localStorage.setItem('auth_provider', 'google');
        } catch (err: any) {
          throw new Error(`Google OAuth not available in browser: ${err?.message || err}`);
        }
      } else if (provider === 'authelia') {
        const tokens = await this.autheliaService.completeOAuthFlow(code, state);
        localStorage.setItem('auth_tokens', JSON.stringify(tokens));
        user = await this.autheliaService.getUserInfo(tokens.access_token);
        localStorage.setItem('auth_provider', 'authelia');
      } else {
        throw new Error('Invalid authentication provider');
      }
      
      this.logSecurityEvent({
        type: 'authentication',
        severity: 'low',
        message: `${provider} authentication successful for user: ${user.email || user.username}`,
        timestamp: Date.now(),
        resolved: true,
        details: { 
          userId: user.id || user.pk, 
          email: user.email || user.username,
          provider,
          role: user.role
        }
      });

      return user;

  } catch (error: any) {
      this.logSecurityEvent({
        type: 'authentication',
        severity: 'high',
        message: `OAuth completion failed: ${error.message}`,
        timestamp: Date.now(),
        resolved: false,
        details: { error: error.message }
      });
      throw error;
    }
  }

  /**
   * Register a new passkey for the current user
   */
  async registerPasskey(deviceName?: string): Promise<any> {
    try {
      const tokens = JSON.parse(localStorage.getItem('auth_tokens') || '{}');
      const userInfo = await this.autheliaService.getUserInfo(tokens.access_token);
      
      const passkey = await this.autheliaService.registerPasskey(
        userInfo.pk.toString(),
        deviceName
      );

      this.logSecurityEvent({
        type: 'authentication',
        severity: 'low',
        message: `Passkey registered successfully for user: ${userInfo.username}`,
        timestamp: Date.now(),
        resolved: true,
        details: { userId: userInfo.pk, deviceName }
      });

      return passkey;

    } catch (error) {
      this.logSecurityEvent({
        type: 'authentication',
        severity: 'medium',
        message: `Passkey registration failed: ${error.message}`,
        timestamp: Date.now(),
        resolved: false,
        details: { error: error.message }
      });
      throw error;
    }
  }

  /**
   * Logout and clean up all security contexts
   */
  async logout(): Promise<void> {
    try {
      const authProvider = localStorage.getItem('auth_provider') || 'google';
      
      if (authProvider === 'google') {
        const userId = localStorage.getItem('current_user_id');
        if (userId) {
          if (!this.googleOAuthService) {
            const mod = await import('../GoogleOAuthService');
            this.googleOAuthService = mod.default.getInstance();
          }
          await this.googleOAuthService!.signOut(userId);
        }
      } else if (authProvider === 'authelia') {
        const tokens = JSON.parse(localStorage.getItem('auth_tokens') || '{}');
        if (tokens.refresh_token) {
          await this.autheliaService.logout(tokens.refresh_token);
        }
      }

      // Clear all stored tokens and session data
      localStorage.removeItem('auth_tokens');
      localStorage.removeItem('current_user_id');
      localStorage.removeItem('auth_provider');
      sessionStorage.clear();

      this.logSecurityEvent({
        type: 'authentication',
        severity: 'low',
        message: `User logged out successfully (${authProvider})`,
        timestamp: Date.now(),
        resolved: true
      });

    } catch (error) {
      this.logSecurityEvent({
        type: 'authentication',
        severity: 'medium',
        message: `Logout failed: ${error.message}`,
        timestamp: Date.now(),
        resolved: false,
        details: { error: error.message }
      });
    }
  }

  /**
   * Get security dashboard data
   */
  getSecurityDashboard(): {
    status: SecurityStatus;
    recentEvents: SecurityEvent[];
    performance: any;
    insights: string[];
  } {
    const recentEvents = this.securityEvents.slice(-20);
    const performance = this.performanceMonitor.generatePerformanceReport();
    const insights = this.performanceMonitor.getPerformanceInsights();

    return {
      status: this.getLastStatus(),
      recentEvents,
      performance,
      insights
    };
  }

  /**
   * Subscribe to security events
   */
  onSecurityEvent(callback: (event: SecurityEvent) => void): void {
    this.eventListeners.push(callback);
  }

  /**
   * Setup security middleware for all requests
   */
  private async setupSecurityMiddleware(): Promise<void> {
    // This would integrate with the application's request interceptors
    console.log('Security middleware configured');
  }

  /**
   * Validate current authentication
   */
  private async validateAuthentication(): Promise<boolean> {
    try {
      const authProvider = localStorage.getItem('auth_provider') || 'google';
      
      if (authProvider === 'google') {
        if (!this.config.googleOAuth) return false;
        const userId = localStorage.getItem('current_user_id');
        if (!userId) return false;
        
        // Check if user exists and tokens are valid
        if (!this.googleOAuthService) {
          const mod = await import('../GoogleOAuthService');
          this.googleOAuthService = mod.default.getInstance();
        }
        const user = await this.googleOAuthService!.getCurrentUser();
        return !!user;
        
      } else if (authProvider === 'authelia') {
        const tokens = JSON.parse(localStorage.getItem('auth_tokens') || '{}');
        if (!tokens.access_token) return false;

        // Try to get user info to validate token
        await this.autheliaService.getUserInfo(tokens.access_token);
        return true;
      }
      
      return false;

  } catch (error) {
      // Try to refresh token for Authentik
      const authProvider = localStorage.getItem('auth_provider');
      if (authProvider === 'authelia') {
        try {
          const tokens = JSON.parse(localStorage.getItem('auth_tokens') || '{}');
          if (tokens.refresh_token) {
            const newTokens = await this.autheliaService.refreshToken(tokens.refresh_token);
            localStorage.setItem('auth_tokens', JSON.stringify(newTokens));
            return true;
          }
        } catch (refreshError) {
          // Both access and refresh failed
          localStorage.removeItem('auth_tokens');
        }
      }
      
      // Clear invalid authentication
      localStorage.removeItem('current_user_id');
      localStorage.removeItem('auth_tokens');
      localStorage.removeItem('auth_provider');
      
      return false;
    }
  }

  /**
   * Calculate overall security status
   */
  private calculateOverallStatus(status: SecurityStatus): 'secure' | 'warning' | 'critical' {
    // VPN connection is critical if enforced
    if (this.config.enforceVPN && !status.vpn.connected) {
      return 'critical';
    }

    // Authentication is required
    if (!status.authentication.authenticated) {
      return 'critical';
    }

    // Check for warnings
    if (!status.performance.monitoring || !status.secrets.rotationEnabled) {
      return 'warning';
    }

    return 'secure';
  }

  /**
   * Log security events
   */
  private logSecurityEvent(event: SecurityEvent): void {
    this.securityEvents.push(event);
    
    // Trim old events
    if (this.securityEvents.length > 1000) {
      this.securityEvents = this.securityEvents.slice(-500);
    }

    // Notify listeners
    this.eventListeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('Security event listener error:', error);
      }
    });

    // Log critical events to console
    if (event.severity === 'critical') {
      console.error('CRITICAL SECURITY EVENT:', event);
    }
  }

  /**
   * Get last known security status
   */
  private getLastStatus(): SecurityStatus {
    // This would return cached status or trigger validation
    return {
      vpn: { connected: false, status: 'unknown' },
      authentication: { method: 'none', authenticated: false },
      performance: { monitoring: false, status: 'unknown' },
      secrets: { encrypted: false, rotationEnabled: false },
      overall: 'critical'
    };
  }

  /**
   * Health check for all security services
   */
  async healthCheck(): Promise<{
    status: string;
    services: Record<string, any>;
    config: SecurityConfig;
    initialized: boolean;
  }> {
    const services = {
      tailscale: await this.tailscaleService.healthCheck(),
      authelia: await this.autheliaService.healthCheck(),
      performance: this.performanceMonitor.healthCheck()
    };

    const allHealthy = Object.values(services).every(service => 
      service.status === 'healthy' || service.status === 'monitoring'
    );

    return {
      status: allHealthy ? 'healthy' : 'degraded',
      services,
      config: this.config,
      initialized: this.initialized
    };
  }

  /**
   * Emergency shutdown of all security services
   */
  emergencyShutdown(): void {
    console.warn('EMERGENCY SECURITY SHUTDOWN INITIATED');
    
    try {
      this.performanceMonitor.stopMonitoring();
      this.tailscaleService.destroy();
      localStorage.clear();
      sessionStorage.clear();
      
      this.logSecurityEvent({
        type: 'audit',
        severity: 'critical',
        message: 'Emergency security shutdown completed',
        timestamp: Date.now(),
        resolved: true
      });
    } catch (error) {
      console.error('Emergency shutdown error:', error);
    }
  }
}

export default SecurityOrchestrator;
