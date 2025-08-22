import React, { createContext, useContext, useEffect } from 'react';

import useSecurity from '../hooks/useSecurity';

import type { ReactNode} from 'react';

interface SecurityContextType {
  // Security state
  initialized: boolean;
  vpnConnected: boolean;
  authenticated: boolean;
  user: any | null;
  loading: boolean;
  error: string | null;
  securityLevel: 'secure' | 'warning' | 'critical';
  
  // Security actions
  initializeSecurity: () => Promise<void>;
  login: (preferPasskey?: boolean, provider?: 'authelia' | 'google') => Promise<string | void>;
  completeLogin: (code: string, state: string, provider?: 'authelia' | 'google') => Promise<any>;
  logout: () => Promise<void>;
  registerPasskey: (deviceName?: string) => Promise<any>;
  validateSecurity: () => Promise<void>;
  getSecurityDashboard: () => any;
}

const SecurityContext = createContext<SecurityContextType | undefined>(undefined);

interface SecurityProviderProps {
  children: ReactNode;
  enforceVPN?: boolean;
  requirePasskeys?: boolean;
}

export const SecurityProvider: React.FC<SecurityProviderProps> = ({
  children,
  enforceVPN = true,
  requirePasskeys = false
}) => {
  const [securityState, securityActions] = useSecurity();

  // Persist runtime override for VPN enforcement so lower-level services can honor it
  useEffect(() => {
    try {
      localStorage.setItem('security.enforceVPN', enforceVPN ? 'true' : 'false');
    } catch {
      // ignore storage errors in restricted environments
    }
  }, [enforceVPN]);

  // Auto-redirect to login if not authenticated
  useEffect(() => {
    if (securityState.initialized && !securityState.authenticated && !securityState.loading) {
      const currentPath = window.location.pathname;
      
      // Don't redirect if already on auth pages
      if (!currentPath.includes('/auth') && !currentPath.includes('/login')) {
        console.log('User not authenticated, security enforcement required');
        
        // You could implement automatic redirect here
        // window.location.href = '/login';
      }
    }
  }, [securityState.initialized, securityState.authenticated, securityState.loading]);

  // Show VPN warning if not connected and enforced
  useEffect(() => {
    if (enforceVPN && securityState.initialized && !securityState.vpnConnected) {
      console.warn('VPN connection required but not detected');
      
      // You could show a modal or notification here
      const notification = document.createElement('div');
      notification.innerHTML = `
        <div style="position: fixed; top: 0; left: 0; right: 0; background: #dc2626; color: white; padding: 1rem; text-align: center; z-index: 9999;">
          <strong>Security Warning:</strong> VPN connection required. Please connect to Tailscale.
        </div>
      `;
      document.body.appendChild(notification);
      
      // Auto-remove after 10 seconds
      setTimeout(() => {
        if (document.body.contains(notification)) {
          document.body.removeChild(notification);
        }
      }, 10000);
    }
  }, [enforceVPN, securityState.initialized, securityState.vpnConnected]);

  // Show passkey registration prompt if required
  useEffect(() => {
    if (requirePasskeys && securityState.authenticated && securityState.user) {
      // Check if user has passkeys registered
      // This would require additional API call to check user's passkeys
      console.log('Passkey registration may be required');
    }
  }, [requirePasskeys, securityState.authenticated, securityState.user]);

  const contextValue: SecurityContextType = {
    ...securityState,
    ...securityActions
  };

  return (
    <SecurityContext.Provider value={contextValue}>
      {children}
    </SecurityContext.Provider>
  );
};

export const useSecurityContext = (): SecurityContextType => {
  const context = useContext(SecurityContext);
  if (context === undefined) {
    throw new Error('useSecurityContext must be used within a SecurityProvider');
  }
  return context;
};

export default SecurityContext;
