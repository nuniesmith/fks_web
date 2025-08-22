import { useState, useEffect, useCallback } from 'react';

import { SecurityOrchestrator } from '../services/security';

interface SecurityState {
  initialized: boolean;
  vpnConnected: boolean;
  authenticated: boolean;
  user: any | null;
  loading: boolean;
  error: string | null;
  securityLevel: 'secure' | 'warning' | 'critical';
}

interface SecurityActions {
  initializeSecurity: () => Promise<void>;
  login: (preferPasskey?: boolean, provider?: 'authelia' | 'google') => Promise<string | void>;
  completeLogin: (code: string, state: string, provider?: 'authelia' | 'google') => Promise<any>;
  logout: () => Promise<void>;
  registerPasskey: (deviceName?: string) => Promise<any>;
  validateSecurity: () => Promise<void>;
  getSecurityDashboard: () => any;
}

const useSecurity = (): [SecurityState, SecurityActions] => {
  const [state, setState] = useState<SecurityState>({
    initialized: false,
    vpnConnected: false,
    authenticated: false,
    user: null,
    loading: false,
    error: null,
    securityLevel: 'critical'
  });

  const securityOrchestrator = SecurityOrchestrator.getInstance();

  // Initialize security services on mount
  useEffect(() => {
    const initSecurity = async () => {
      try {
        setState(prev => ({ ...prev, loading: true, error: null }));
        
        await securityOrchestrator.initialize();
        const status = await securityOrchestrator.validateSecurityPosture();
        
        setState(prev => ({
          ...prev,
          initialized: true,
          vpnConnected: status.vpn.connected,
          authenticated: status.authentication.authenticated,
          user: status.authentication.user || null,
          securityLevel: status.overall,
          loading: false
        }));

      } catch (error) {
        setState(prev => ({
          ...prev,
          loading: false,
          error: error instanceof Error ? error.message : 'Security initialization failed',
          securityLevel: 'critical'
        }));
      }
    };

    initSecurity();
  }, []);

  // Listen for security events
  useEffect(() => {
    const handleSecurityEvent = (event: any) => {
      if (event.type === 'vpn' && event.severity === 'critical') {
        setState(prev => ({ ...prev, vpnConnected: false, securityLevel: 'critical' }));
      } else if (event.type === 'authentication' && !event.resolved) {
        setState(prev => ({ ...prev, authenticated: false, user: null }));
      }
    };

    securityOrchestrator.onSecurityEvent(handleSecurityEvent);
  }, [securityOrchestrator]);

  const actions: SecurityActions = {
    initializeSecurity: useCallback(async () => {
      try {
        setState(prev => ({ ...prev, loading: true, error: null }));
        
        await securityOrchestrator.initialize();
        const status = await securityOrchestrator.validateSecurityPosture();
        
        setState(prev => ({
          ...prev,
          initialized: true,
          vpnConnected: status.vpn.connected,
          authenticated: status.authentication.authenticated,
          user: status.authentication.user || null,
          securityLevel: status.overall,
          loading: false
        }));

      } catch (error) {
        setState(prev => ({
          ...prev,
          loading: false,
          error: error instanceof Error ? error.message : 'Security initialization failed'
        }));
        throw error;
      }
    }, [securityOrchestrator]),

    login: useCallback(async (preferPasskey = true, provider: 'authelia' | 'google' = 'authelia') => {
      try {
        setState(prev => ({ ...prev, loading: true, error: null }));
        
        await securityOrchestrator.enforceSecurityPolicies();
        const result = await securityOrchestrator.initiateAuthentication(preferPasskey, provider);
        
        if (result === 'passkey') {
          // Passkey authentication completed
          const status = await securityOrchestrator.validateSecurityPosture();
          setState(prev => ({
            ...prev,
            authenticated: true,
            user: status.authentication.user,
            securityLevel: status.overall,
            loading: false
          }));
        } else {
          // OAuth URL returned - redirect needed
          setState(prev => ({ ...prev, loading: false }));
          return result;
        }

      } catch (error) {
        setState(prev => ({
          ...prev,
          loading: false,
          error: error instanceof Error ? error.message : 'Login failed'
        }));
        throw error;
      }
    }, [securityOrchestrator]),

    completeLogin: useCallback(async (code: string, state: string, provider: 'authelia' | 'google' = 'authelia') => {
      try {
        setState(prev => ({ ...prev, loading: true, error: null }));
        
        const user = await securityOrchestrator.completeAuthentication(code, state, provider);
        const securityStatus = await securityOrchestrator.validateSecurityPosture();
        
        setState(prev => ({
          ...prev,
          authenticated: true,
          user,
          securityLevel: securityStatus.overall,
          loading: false
        }));

        return user;

      } catch (error) {
        setState(prev => ({
          ...prev,
          loading: false,
          error: error instanceof Error ? error.message : 'Login completion failed'
        }));
        throw error;
      }
    }, [securityOrchestrator]),

    logout: useCallback(async () => {
      try {
        setState(prev => ({ ...prev, loading: true, error: null }));
        
        await securityOrchestrator.logout();
        
        setState(prev => ({
          ...prev,
          authenticated: false,
          user: null,
          securityLevel: 'critical',
          loading: false
        }));

      } catch (error) {
        setState(prev => ({
          ...prev,
          loading: false,
          error: error instanceof Error ? error.message : 'Logout failed'
        }));
      }
    }, [securityOrchestrator]),

    registerPasskey: useCallback(async (deviceName?: string) => {
      try {
        setState(prev => ({ ...prev, loading: true, error: null }));
        
        const passkey = await securityOrchestrator.registerPasskey(deviceName);
        
        setState(prev => ({ ...prev, loading: false }));
        return passkey;

      } catch (error) {
        setState(prev => ({
          ...prev,
          loading: false,
          error: error instanceof Error ? error.message : 'Passkey registration failed'
        }));
        throw error;
      }
    }, [securityOrchestrator]),

    validateSecurity: useCallback(async () => {
      try {
        await securityOrchestrator.enforceSecurityPolicies();
        const status = await securityOrchestrator.validateSecurityPosture();
        
        setState(prev => ({
          ...prev,
          vpnConnected: status.vpn.connected,
          authenticated: status.authentication.authenticated,
          user: status.authentication.user || null,
          securityLevel: status.overall
        }));

      } catch (error) {
        setState(prev => ({
          ...prev,
          error: error instanceof Error ? error.message : 'Security validation failed',
          securityLevel: 'critical'
        }));
        throw error;
      }
    }, [securityOrchestrator]),

    getSecurityDashboard: useCallback(() => {
      return securityOrchestrator.getSecurityDashboard();
    }, [securityOrchestrator])
  };

  return [state, actions];
};

export default useSecurity;
