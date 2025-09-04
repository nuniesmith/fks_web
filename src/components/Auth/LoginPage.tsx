import React, { useState, useCallback } from 'react';
import { Shield, Chrome, Key, Loader, AlertCircle, CheckCircle, Lock, User, Eye, EyeOff } from 'lucide-react';
import { useSecurityContext } from '../../context/SecurityContext';
import AuthenticationSelector from './AuthenticationSelector';

/**
 * Unified Login Page
 * - Rust (fks_auth) username/password JWT flow
 * - Primary (passkey / rust redirect) via existing AuthenticationSelector
 * - Optional Google OAuth (if enabled via localStorage security.googleOAuth || VITE_GOOGLE_OAUTH)
 */
const LoginPage: React.FC = () => {
	const {
		authenticated,
		user,
		loading,
		error: securityError,
		validateSecurity
	} = useSecurityContext();

	const [username, setUsername] = useState('');
	const [password, setPassword] = useState('');
	const [showPassword, setShowPassword] = useState(false);
	const [formError, setFormError] = useState<string | null>(null);
	const [formLoading, setFormLoading] = useState(false);
	const [jwtPreview, setJwtPreview] = useState<string | null>(null);
	const [activeTab, setActiveTab] = useState<'primary' | 'credentials' | 'google'>('credentials');

	const googleEnabled = (localStorage.getItem('security.googleOAuth') ?? (import.meta as any).env?.VITE_GOOGLE_OAUTH) === 'true';

	const rustAuthBase = (import.meta as any).env?.VITE_RUST_AUTH_URL || 'http://localhost:8001';

	const decodeJwt = (token: string): any | null => {
		try {
			const [, payload] = token.split('.');
			if (!payload) return null;
			const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
			return JSON.parse(decodeURIComponent(escape(json)));
		} catch { return null; }
	};

	const loginWithCredentials = useCallback(async () => {
		setFormError(null);
		setJwtPreview(null);
		setFormLoading(true);
		try {
			if (!username || !password) {
				throw new Error('Username & password required');
			}

			const resp = await fetch(`${rustAuthBase}/login`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ username, password })
			});

			if (!resp.ok) {
				const text = await resp.text();
				throw new Error(text || `Login failed (${resp.status})`);
			}
			const data = await resp.json();
			// Expect shape: { access_token, refresh_token?, expires_in? }
			if (!data.access_token) {
				throw new Error('Invalid response: no access_token');
			}
			localStorage.setItem('auth_tokens', JSON.stringify(data));
			localStorage.setItem('auth_provider', 'rust');
			const decoded = decodeJwt(data.access_token);
			setJwtPreview(decoded ? JSON.stringify({ sub: decoded.sub, exp: decoded.exp }, null, 2) : 'Token decoded (preview unavailable)');

			// Trigger security posture refresh
			await validateSecurity();
		} catch (e: any) {
			setFormError(e.message || 'Credential login failed');
		} finally {
			setFormLoading(false);
		}
	}, [username, password, rustAuthBase, validateSecurity]);

	if (authenticated && user) {
		return (
			<div className="max-w-lg mx-auto mt-16 p-8 bg-white dark:bg-gray-900 rounded-xl shadow-md border border-gray-200 dark:border-gray-700">
				<div className="flex items-center space-x-3 mb-4">
					<CheckCircle className="h-8 w-8 text-green-600" />
					<h2 className="text-xl font-semibold text-gray-900 dark:text-white">Authenticated</h2>
				</div>
				<p className="text-gray-600 dark:text-gray-300 mb-2">You are signed in as <span className="font-medium">{user.name || user.username}</span>.</p>
				<pre className="text-xs bg-gray-100 dark:bg-gray-800 p-3 rounded-md overflow-auto max-h-40">{jwtPreview || 'Session established.'}</pre>
				<p className="mt-4 text-sm text-gray-500 dark:text-gray-400">Navigate to the application dashboard.</p>
			</div>
		);
	}

	return (
		<div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900 px-4 py-10">
			<div className="w-full max-w-5xl grid md:grid-cols-2 gap-10">
				{/* Left: Credentials + Tabs */}
				<div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm p-8 relative overflow-hidden">
					<div className="absolute -top-6 -right-6 h-24 w-24 bg-blue-500/10 rounded-full" />
					<div className="absolute -bottom-8 -left-8 h-32 w-32 bg-indigo-500/10 rounded-full" />
					<div className="relative">
						<div className="flex items-center space-x-2 mb-6">
							<Shield className="h-8 w-8 text-blue-600" />
							<h1 className="text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">Secure Login</h1>
						</div>

						{/* Tabs */}
						<div className="flex space-x-2 mb-6">
							<button
								onClick={() => setActiveTab('credentials')}
								className={`px-4 py-2 rounded-md text-sm font-medium border transition-colors ${activeTab === 'credentials' ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'}`}
							>Credentials</button>
							<button
								onClick={() => setActiveTab('primary')}
								className={`px-4 py-2 rounded-md text-sm font-medium border transition-colors ${activeTab === 'primary' ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'}`}
							>Primary</button>
							{googleEnabled && (
								<button
									onClick={() => setActiveTab('google')}
									className={`px-4 py-2 rounded-md text-sm font-medium border transition-colors ${activeTab === 'google' ? 'bg-blue-600 text-white border-blue-600' : 'border-gray-300 dark:border-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'}`}
								>Google</button>
							)}
						</div>

						{activeTab === 'credentials' && (
							<div>
								<h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4 flex items-center"><Lock className="h-5 w-5 mr-2" /> Username & Password</h2>
								{formError && (
									<div className="mb-4 p-3 rounded-md border border-red-300 dark:border-red-700 bg-red-50 dark:bg-red-900/20 flex items-start space-x-2 text-sm text-red-700 dark:text-red-300">
										<AlertCircle className="h-4 w-4 mt-0.5" />
										<span>{formError}</span>
									</div>
								)}
								{securityError && !formError && (
									<div className="mb-4 p-3 rounded-md border border-yellow-300 dark:border-yellow-700 bg-yellow-50 dark:bg-yellow-900/20 flex items-start space-x-2 text-sm text-yellow-700 dark:text-yellow-300">
										<AlertCircle className="h-4 w-4 mt-0.5" />
										<span>{securityError}</span>
									</div>
								)}

								<div className="space-y-4">
									<div>
										<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username</label>
										<div className="relative">
											<User className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
											<input
												type="text"
												autoComplete="username"
												className="w-full pl-9 pr-3 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 dark:text-gray-100"
												value={username}
												onChange={e => setUsername(e.target.value)}
											/>
										</div>
									</div>
									<div>
										<label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
										<div className="relative">
											<Key className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
											<input
												type={showPassword ? 'text' : 'password'}
												autoComplete="current-password"
												className="w-full pl-9 pr-9 py-2 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 dark:text-gray-100"
												value={password}
												onChange={e => setPassword(e.target.value)}
											/>
											<button
												type="button"
												onClick={() => setShowPassword(p => !p)}
												className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
											>{showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button>
										</div>
									</div>
									<button
										onClick={loginWithCredentials}
										disabled={formLoading || !username || !password}
										className="w-full flex items-center justify-center px-4 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
									>
										{formLoading ? <Loader className="h-4 w-4 animate-spin mr-2" /> : <Shield className="h-4 w-4 mr-2" />}
										Sign In
									</button>
									<p className="text-xs text-gray-500 dark:text-gray-400">Credentials sent securely to Rust auth service. JWT stored locally.</p>
									{jwtPreview && (
										<pre className="text-[10px] bg-gray-100 dark:bg-gray-800 p-2 rounded-md overflow-auto max-h-24 border border-gray-200 dark:border-gray-700">{jwtPreview}</pre>
									)}
								</div>
							</div>
						)}

						{activeTab === 'primary' && (
							<div className="mt-2">
								<AuthenticationSelector className="shadow-none p-0" />
							</div>
						)}

						{activeTab === 'google' && googleEnabled && (
							<div className="mt-2 space-y-4">
								<h2 className="text-lg font-medium text-gray-900 dark:text-white flex items-center"><Chrome className="h-5 w-5 mr-2" /> Google OAuth</h2>
								<p className="text-sm text-gray-600 dark:text-gray-400">Use your approved Google account for access.</p>
								<AuthenticationSelector className="shadow-none p-0" />
							</div>
						)}
					</div>
				</div>

				{/* Right: Marketing / Context */}
				<div className="space-y-6 self-center">
					<div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm">
						<h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 flex items-center"><Shield className="h-5 w-5 mr-2 text-blue-600" /> Security Layers</h3>
						<ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1 list-disc list-inside">
							<li>Rust JWT auth (primary)</li>
							<li>Optional Google OAuth (federated)</li>
							<li>Passkey placeholder (future)</li>
							<li>VPN awareness (Tailscale)</li>
							<li>Performance & audit instrumentation</li>
						</ul>
					</div>
					<div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm">
						<h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">How Credential Flow Works</h3>
						<ol className="list-decimal list-inside text-sm text-gray-600 dark:text-gray-400 space-y-1">
							<li>POST /login to Rust auth</li>
							<li>Store access/refresh tokens in localStorage</li>
							<li>Update security posture via context</li>
							<li>Subsequent protected requests enforce policies</li>
						</ol>
						<p className="mt-3 text-xs text-gray-500 dark:text-gray-500">Ensure VITE_RUST_AUTH_URL points at fks_auth service.</p>
					</div>
				</div>
			</div>
		</div>
	);
};

export default LoginPage;

