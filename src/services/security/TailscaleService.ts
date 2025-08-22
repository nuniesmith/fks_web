interface TailscaleNode {
  id: string;
  name: string;
  ipv4: string;
  ipv6: string;
  online: boolean;
  lastSeen: string;
  machineKey: string;
  nodeKey: string;
  user: string;
  tags: string[];
}

interface TailscaleStatus {
  connected: boolean;
  nodeId: string;
  tailnetName: string;
  magicDNSSuffix: string;
  currentTailnetIP: string;
  peers: TailscaleNode[];
}

interface NetworkPolicy {
  id: string;
  name: string;
  sourceNodes: string[];
  destinationNodes: string[];
  allowedPorts: number[];
  protocol: 'tcp' | 'udp' | 'icmp';
  action: 'allow' | 'deny';
  priority: number;
}

export class TailscaleService {
  private static instance: TailscaleService;
  private baseUrl: string;
  private apiKey: string;
  private tailnet: string;
  private enforceVPN: boolean = true;
  private statusCheckInterval: NodeJS.Timeout | null = null;

  private constructor() {
    this.baseUrl = 'https://api.tailscale.com/api/v2';
    this.apiKey = import.meta.env.VITE_TAILSCALE_API_KEY || '';
    this.tailnet = import.meta.env.VITE_TAILSCALE_TAILNET || '';
    // Allow runtime override from SecurityProvider/localStorage
    const stored = typeof window !== 'undefined' ? localStorage.getItem('security.enforceVPN') : null;
    if (stored !== null) {
      this.enforceVPN = stored === 'true';
    } else {
      this.enforceVPN = import.meta.env.VITE_TAILSCALE_ENFORCE_VPN !== 'false';
    }
  }

  static getInstance(): TailscaleService {
    if (!TailscaleService.instance) {
      TailscaleService.instance = new TailscaleService();
    }
    return TailscaleService.instance;
  }

  /**
   * Initialize Tailscale service and start monitoring
   */
  async initialize(): Promise<void> {
    try {
      if (this.enforceVPN) {
        await this.validateTailscaleConnection();
        this.startStatusMonitoring();
      }
      console.log('TailscaleService initialized successfully');
    } catch (error) {
      console.error('Failed to initialize TailscaleService:', error);
      if (this.enforceVPN) {
        throw new Error('Tailscale VPN is required but not available');
      }
    }
  }

  /**
   * Check if current connection is through Tailscale
   */
  async isConnectedViaTailscale(): Promise<boolean> {
    try {
      // Check if we're on a Tailscale IP range
      const response = await fetch('/api/network/status', {
        headers: this.getHeaders()
      });
      
      if (!response.ok) {
  // In development without a backend endpoint, gracefully bypass (even if enforce is on)
  if (response.status === 404 && import.meta.env.DEV) return true;
        return false;
      }
      
      const status = await response.json();
      return this.isTailscaleIP(status.clientIP);
    } catch (error) {
      console.error('Failed to check Tailscale connection:', error);
      return false;
    }
  }

  /**
   * Get current Tailscale status
   */
  async getStatus(): Promise<TailscaleStatus | null> {
    try {
      const response = await fetch(`${this.baseUrl}/tailnet/${this.tailnet}/devices`, {
        headers: this.getHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to get Tailscale status: ${response.statusText}`);
      }

      const data = await response.json();
      
      return {
        connected: true,
        nodeId: data.devices?.[0]?.id || '',
        tailnetName: this.tailnet,
        magicDNSSuffix: '.ts.net',
        currentTailnetIP: data.devices?.[0]?.addresses?.[0] || '',
        peers: data.devices?.map((device: any) => ({
          id: device.id,
          name: device.name,
          ipv4: device.addresses?.[0] || '',
          ipv6: device.addresses?.[1] || '',
          online: device.online,
          lastSeen: device.lastSeen,
          machineKey: device.machineKey,
          nodeKey: device.nodeKey,
          user: device.user,
          tags: device.tags || []
        })) || []
      };
    } catch (error) {
      console.error('Failed to get Tailscale status:', error);
      return null;
    }
  }

  /**
   * Enforce VPN connection for all requests
   */
  async enforceVPNConnection(): Promise<void> {
    if (!this.enforceVPN) return;

    const isConnected = await this.isConnectedViaTailscale();
    
    if (!isConnected) {
      throw new Error('VPN connection required. Please connect to Tailscale.');
    }
  }

  /**
   * Get network policies for current node
   */
  async getNetworkPolicies(): Promise<NetworkPolicy[]> {
    try {
      const response = await fetch(`${this.baseUrl}/tailnet/${this.tailnet}/acl`, {
        headers: this.getHeaders()
      });

      if (!response.ok) {
        throw new Error(`Failed to get network policies: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Transform ACL rules to network policies
      return this.transformACLToPolicies(data.acls || []);
    } catch (error) {
      console.error('Failed to get network policies:', error);
      return [];
    }
  }

  /**
   * Update network access control list
   */
  async updateNetworkACL(policies: NetworkPolicy[]): Promise<boolean> {
    try {
      const acl = this.transformPoliciesToACL(policies);
      
      const response = await fetch(`${this.baseUrl}/tailnet/${this.tailnet}/acl`, {
        method: 'POST',
        headers: {
          ...this.getHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ acls: acl })
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to update network ACL:', error);
      return false;
    }
  }

  /**
   * Get secure tunnel URL for internal services
   */
  getTunnelUrl(service: string, port: number): string {
    const status = this.getLocalStatus();
    if (!status?.currentTailnetIP) {
      throw new Error('Tailscale not connected');
    }
    
    return `https://${service}.${status.currentTailnetIP}:${port}`;
  }

  /**
   * Create a secure service endpoint
   */
  async createSecureEndpoint(serviceName: string, port: number, tags: string[] = []): Promise<string> {
    const status = await this.getStatus();
    if (!status?.currentTailnetIP) {
      throw new Error('Cannot create endpoint: Tailscale not connected');
    }

    // Register service with Tailscale
    const endpoint = `${serviceName}.${status.tailnetName}`;
    
    // Add service tags for access control
    await this.addServiceTags(serviceName, [...tags, 'fks-service']);
    
    return `https://${endpoint}:${port}`;
  }

  /**
   * Monitor connection health and reconnect if needed
   */
  private startStatusMonitoring(): void {
    if (this.statusCheckInterval) {
      clearInterval(this.statusCheckInterval);
    }

    this.statusCheckInterval = setInterval(async () => {
      try {
        const isConnected = await this.isConnectedViaTailscale();
        
        if (!isConnected && this.enforceVPN) {
          console.warn('Tailscale connection lost, attempting to reconnect...');
          await this.attemptReconnection();
        }
      } catch (error) {
        console.error('Tailscale status check failed:', error);
      }
    }, 30000); // Check every 30 seconds
  }

  /**
   * Validate Tailscale connection on startup
   */
  private async validateTailscaleConnection(): Promise<void> {
    const isConnected = await this.isConnectedViaTailscale();
    
    if (!isConnected) {
      if (import.meta.env.DEV) {
        // Developer mode with no TS config: do not block startup
        console.warn('Tailscale bypassed in development environment.');
        return;
      }
      throw new Error('Tailscale VPN connection is required but not detected');
    }
  }

  /**
   * Check if IP address is in Tailscale range
   */
  private isTailscaleIP(ip: string): boolean {
    // Tailscale uses 100.x.x.x range (CGNAT)
    return ip.startsWith('100.') || 
           ip.startsWith('fd7a:115c:a1e0:'); // IPv6 range
  }

  /**
   * Get request headers with authentication
   */
  private getHeaders(): Record<string, string> {
    return {
      'Authorization': `Bearer ${this.apiKey}`,
      'Accept': 'application/json'
    };
  }

  /**
   * Transform ACL rules to network policies
   */
  private transformACLToPolicies(acls: any[]): NetworkPolicy[] {
    return acls.map((acl: any, index: number) => ({
      id: `policy-${index}`,
      name: acl.action || 'unnamed',
      sourceNodes: acl.src || [],
      destinationNodes: acl.dst || [],
      allowedPorts: this.extractPorts(acl.dst),
      protocol: this.extractProtocol(acl.proto) || 'tcp',
      action: acl.action === 'accept' ? 'allow' : 'deny',
      priority: index
    }));
  }

  /**
   * Transform network policies to ACL rules
   */
  private transformPoliciesToACL(policies: NetworkPolicy[]): any[] {
    return policies.map(policy => ({
      action: policy.action === 'allow' ? 'accept' : 'deny',
      src: policy.sourceNodes,
      dst: policy.destinationNodes.map(node => 
        `${node}:${policy.allowedPorts.join(',')}`
      ),
      proto: policy.protocol
    }));
  }

  /**
   * Extract ports from destination string
   */
  private extractPorts(destinations: string[]): number[] {
    const ports: number[] = [];
    
    destinations.forEach(dest => {
      const portMatch = dest.match(/:(\d+)/);
      if (portMatch) {
        ports.push(parseInt(portMatch[1]));
      }
    });
    
    return ports;
  }

  /**
   * Extract protocol from proto field
   */
  private extractProtocol(proto: string): 'tcp' | 'udp' | 'icmp' {
    if (proto?.toLowerCase().includes('udp')) return 'udp';
    if (proto?.toLowerCase().includes('icmp')) return 'icmp';
    return 'tcp';
  }

  /**
   * Get local status (cached)
   */
  private getLocalStatus(): TailscaleStatus | null {
    // This would be implemented with local caching
    return null;
  }

  /**
   * Attempt to reconnect to Tailscale
   */
  private async attemptReconnection(): Promise<void> {
    // This would trigger a reconnection attempt
    console.log('Attempting Tailscale reconnection...');
  }

  /**
   * Add service tags for access control
   */
  private async addServiceTags(serviceName: string, tags: string[]): Promise<void> {
    // Implementation would add tags to service for ACL
    console.log(`Adding tags ${tags.join(', ')} to service ${serviceName}`);
  }

  /**
   * Cleanup monitoring when service shuts down
   */
  destroy(): void {
    if (this.statusCheckInterval) {
      clearInterval(this.statusCheckInterval);
      this.statusCheckInterval = null;
    }
  }

  /**
   * Health check for Tailscale service
   */
  async healthCheck(): Promise<{ status: string; details: any }> {
    try {
      const isConnected = await this.isConnectedViaTailscale();
      const status = await this.getStatus();
      
      return {
        status: isConnected ? 'healthy' : 'degraded',
        details: {
          connected: isConnected,
          enforceVPN: this.enforceVPN,
          tailnet: this.tailnet,
          nodeCount: status?.peers?.length || 0,
          monitoring: this.statusCheckInterval !== null
        }
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        details: {
          error: error.message,
          enforceVPN: this.enforceVPN
        }
      };
    }
  }
}

export default TailscaleService;
