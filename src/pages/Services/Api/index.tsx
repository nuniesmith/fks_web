import React from 'react';

import ServiceContractTestPanel from '../../../components/ServiceMonitoring/ServiceContractTestPanel';
import ServicePageLayout from '../../../components/ServiceMonitoring/ServicePageLayout';

const apiBase = 'http://localhost:8000';

const contractSpecs = [
  { id: 'health', label: 'Health', endpoint: '/health', expectedStatus: 200, maxLatencyMs: 800, hardLatencyBudgetMs: 2000, jsonSchema: { status: 'string', uptime: 'number' } as const },
  { id: 'openapi', label: 'OpenAPI', endpoint: '/openapi.json', expectedStatus: 200, requiredKeys: ['openapi'], maxLatencyMs: 1500, hardLatencyBudgetMs: 4000, jsonSchema: { openapi: 'string', paths: 'object' } as const },
  { id: 'metrics', label: 'Metrics', endpoint: '/metrics', expectedStatus: [200, 404], enabled: true, maxLatencyMs: 2500 },
  { id: 'auth-unauth', label: 'Auth Guard (unauth)', endpoint: '/private/ping', expectedStatus: [401, 403], maxLatencyMs: 600, hardLatencyBudgetMs: 1500 },
  { id: 'version', label: 'Version Header', endpoint: '/health', expectedStatus: 200, headers: { 'Accept': 'application/json' }, requiredKeys: ['status'], jsonSchema: { status: 'string' } as const, maxLatencyMs: 800 },
];

const ApiServicePage: React.FC = () => (
  <ServicePageLayout serviceId="api" title="Core API Service" description="Primary backend API: authentication, data orchestration, and strategy interfaces.">
    <div className="grid md:grid-cols-2 gap-4">
      <div className="glass-card p-6">
        <h3 className="font-semibold mb-2">Planned API Tests</h3>
        <ul className="list-disc list-inside text-sm text-white/70 space-y-1">
          <li>Schema validation for critical endpoints</li>
          <li>Auth header propagation checks</li>
          <li>Rate-limit / 429 behavior simulation</li>
        </ul>
      </div>
      <ServiceContractTestPanel serviceId="api" baseUrl={apiBase} specs={contractSpecs} />
    </div>
  </ServicePageLayout>
);

export default ApiServicePage;
