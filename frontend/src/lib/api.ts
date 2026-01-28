export type ApiLatLng = { lat: number; lng: number };

export type ApiSessionLocationDetails = {
	id: string;
	name: string;
	address: string;
	region: string;
	latlong: ApiLatLng;
};

// Matches backend SessionPublic.
export type ApiSession = {
	id: string;
	name: string;
	age: string;
	time: string;
	term_summary?: string | null;
	blocks?: string[];
	public_instructions?: string | null;
	arrival_instructions?: string | null;
	what_to_bring?: string | null;
	prerequisites?: string | null;
	waitlist: boolean;
	locationDetails?: ApiSessionLocationDetails | null;
};

export type ApiSessionOccurrence = {
	starts_at: string;
	ends_at: string;
	cancelled?: boolean;
};

export type ApiBlockOccurrences = {
	block_id: string;
	block_name: string;
	block_type: string;
	occurrences: ApiSessionOccurrence[];
};

export type ApiSessionDetail = ApiSession & {
	occurrences_by_block?: ApiBlockOccurrences[];
};

export type ApiSessionLocation = {
	name: string;
	sessions: ApiSession[];
};

export type ApiCaregiverMe = {
	id: string;
	email: string;
	name?: string | null;
	phone?: string | null;
	email_verified: boolean;
};

export type ApiChild = {
	id: string;
	name: string;
	dateOfBirth?: string | null;
	mediaConsent?: boolean;
	medicalInfo?: string | null;
	otherInfo?: string | null;
};

export type ApiCaregiverSignup = {
	id: string;
	status: string;
	sessionId: string;
	sessionName: string;
	childId: string;
	childName: string;
};

export type UiSession = {
	id: string;
	name: string;
	address: string;
	latlong: [number, number];
	age: string;
	time: string;
	term_summary?: string | null;
	blocks?: string[];
	location: string;
	waitlist?: boolean;
	signupLink?: string;
	venueName?: string | null;

	// Optional detail fields (used on session detail pages)
	public_instructions?: string | null;
	arrival_instructions?: string | null;
	what_to_bring?: string | null;
	prerequisites?: string | null;

	occurrences_by_block?: ApiBlockOccurrences[];
};

export type UiSessionLocation = {
	name: string;
	sessions: UiSession[];
};

const defaultApiBaseUrl = 'https://sessions-api.tuhuratech.org.nz';
const internalApiBaseUrl = 'http://backend:8000'; // Internal Docker network URL

export function getApiBaseUrl(): string {
	// For server-side rendering, use internal Docker URL or environment variable
	// In Node.js/Astro SSR, globalThis is available but window is not
	if (typeof window === 'undefined') {
		// Server-side: use internal Docker URL
		return internalApiBaseUrl;
	}

	// For client-side, use the public API URL from environment
	const envUrl = import.meta.env?.PUBLIC_BASE_URL || import.meta.env?.PUBLIC_API_BASE_URL;
	return envUrl || defaultApiBaseUrl;
}

export async function fetchSessionLocations(): Promise<UiSessionLocation[]> {
	const baseUrl = getApiBaseUrl();
	const res = await fetch(`${baseUrl}/api/v1/sessions`);
	if (!res.ok) throw new Error(`Failed to fetch sessions: ${res.status}`);
	const data = (await res.json()) as ApiSessionLocation[];

	return data.map((loc) => ({
		name: loc.name,
		sessions: loc.sessions.map((s) => {
			const details = s.locationDetails ?? null;
			return {
				id: s.id,
				name: s.name,
				address: details?.address ?? '',
				latlong: [details?.latlong.lat ?? 0, details?.latlong.lng ?? 0],
				age: s.age,
				time: s.time,
				term_summary: s.term_summary ?? null,
				blocks: s.blocks ?? [],
				location: details?.region ?? loc.name,
				waitlist: s.waitlist,
				signupLink: `/signup?session=${s.id}`,
				venueName: details?.name ?? null,
				public_instructions: s.public_instructions ?? null,
				arrival_instructions: s.arrival_instructions ?? null,
				what_to_bring: s.what_to_bring ?? null,
				prerequisites: s.prerequisites ?? null,
			};
		}),
	}));
}

async function apiFetch(path: string, init?: RequestInit, cookies?: string): Promise<Response> {
	const baseUrl = getApiBaseUrl();
	const fullUrl = `${baseUrl}${path}`;
	return fetch(fullUrl, {
		...init,
		credentials: 'include',
		headers: {
			'Content-Type': 'application/json',
			...(init?.headers || {}),
			...(cookies ? { cookie: cookies } : {}),
		},
	});
}

export async function fetchMe(cookies?: string): Promise<ApiCaregiverMe | null> {
	const res = await apiFetch('/api/v1/me', undefined, cookies);
	if (res.status === 401) return null;
	if (!res.ok) throw new Error(`Failed to fetch me: ${res.status}`);
	return (await res.json()) as ApiCaregiverMe;
}

export async function updateMe(input: {
	name: string;
	phone: string;
	newsletter?: boolean;
	referralSource?: string;
}): Promise<ApiCaregiverMe> {
	const res = await apiFetch('/api/v1/me', { method: 'PATCH', body: JSON.stringify(input) });
	if (!res.ok) throw new Error(`Failed to update me: ${res.status}`);
	return (await res.json()) as ApiCaregiverMe;
}

export async function requestMagicLink(
	email: string,
	returnTo?: string,
): Promise<{ ok: boolean; debugToken?: string | null }> {
	const res = await apiFetch('/api/v1/auth/magic-link', {
		method: 'POST',
		body: JSON.stringify({ email, return_to: returnTo }),
	});
	if (!res.ok) throw new Error(`Failed to request magic link: ${res.status}`);
	return (await res.json()) as { ok: boolean; debugToken?: string | null };
}

export function redirectToAuth(returnTo?: string): void {
	const url = new URL('/auth/magic-url', window.location.origin);
	if (returnTo) {
		url.searchParams.set('returnTo', returnTo);
	}
	window.location.href = url.toString();
}

export async function logout(): Promise<{ ok: boolean }> {
	const res = await apiFetch('/api/v1/auth/logout', { method: 'POST' });
	if (!res.ok) throw new Error(`Failed to logout: ${res.status}`);
	return (await res.json()) as { ok: boolean };
}

export async function listChildren(cookies?: string): Promise<ApiChild[]> {
	const res = await apiFetch('/api/v1/students', undefined, cookies);
	if (!res.ok) throw new Error(`Failed to list children: ${res.status}`);
	return (await res.json()) as ApiChild[];
}

export async function createChild(input: {
	name: string;
	dateOfBirth: string;
	mediaConsent?: boolean;
	medicalInfo?: string;
	otherInfo?: string;
	region?: string;
	ethnicity?: string;
	gender?: string;
	schoolName?: string;
}): Promise<ApiChild> {
	const res = await apiFetch('/api/v1/students', { method: 'POST', body: JSON.stringify(input) });
	if (!res.ok) throw new Error(`Failed to create child: ${res.status}`);
	return (await res.json()) as ApiChild;
}

export async function updateChild(
	childId: string,
	input: { name?: string | null; dateOfBirth?: string | null },
): Promise<ApiChild> {
	const res = await apiFetch(`/api/v1/students/${childId}`, {
		method: 'PATCH',
		body: JSON.stringify(input),
	});
	if (!res.ok) throw new Error(`Failed to update child: ${res.status}`);
	return (await res.json()) as ApiChild;
}

export async function listMySignups(): Promise<ApiCaregiverSignup[]> {
	const res = await apiFetch('/api/v1/signups');
	if (!res.ok) throw new Error(`Failed to list signups: ${res.status}`);
	return (await res.json()) as ApiCaregiverSignup[];
}

export async function createAuthenticatedSignup(
	sessionId: string,
	input: {
		childId: string;
		pickupDropoff?: string;
		pairingPreference?: string;
	},
): Promise<{ id: string; status: string }> {
	const res = await apiFetch(`/api/v1/session/${sessionId}/signup`, {
		method: 'POST',
		body: JSON.stringify(input),
	});
	if (!res.ok) throw new Error(`Failed to create signup: ${res.status}`);
	return (await res.json()) as { id: string; status: string };
}

export async function fetchFlatSessions(): Promise<UiSession[]> {
	const locations = await fetchSessionLocations();
	return locations.flatMap((location) => location.sessions);
}

export async function fetchSessionById(id: string): Promise<UiSession | null> {
	const baseUrl = getApiBaseUrl();
	const res = await fetch(`${baseUrl}/api/v1/session/${id}`);
	if (res.status === 404) return null;
	if (!res.ok) throw new Error(`Failed to fetch session: ${res.status}`);
	const s = (await res.json()) as ApiSessionDetail;
	const details = s.locationDetails ?? null;
	return {
		id: s.id,
		name: s.name,
		address: details?.address ?? '',
		latlong: [details?.latlong.lat ?? 0, details?.latlong.lng ?? 0],
		age: s.age,
		time: s.time,
		term_summary: s.term_summary ?? null,
		blocks: s.blocks ?? [],
		location: details?.region ?? '',
		waitlist: s.waitlist,
		signupLink: `/signup?session=${s.id}`,
		venueName: details?.name ?? null,
		public_instructions: s.public_instructions ?? null,
		arrival_instructions: s.arrival_instructions ?? null,
		what_to_bring: s.what_to_bring ?? null,
		prerequisites: s.prerequisites ?? null,
		occurrences_by_block: s.occurrences_by_block ?? [],
	};
}
