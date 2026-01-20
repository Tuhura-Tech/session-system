export type SignupStatus = 'pending' | 'confirmed' | 'waitlisted' | 'cancelled';

export type Signup = {
	id: string;
	sessionId: string;
	sessionName: string;
	location: string;
	studentName: string;
	studentAge: number;
	guardianName: string;
	email: string;
	phone: string;
	medical?: string;
	heardFrom?: string;
	consentMedia: boolean;
	subscribeNewsletter: boolean;
	status: SignupStatus;
	createdAt?: string;
};

export type AttendanceStatus = 'present' | 'absent' | 'excused';

export type AttendanceRecord = {
	id: string;
	signupId: string;
	sessionId: string;
	date: string;
	status: AttendanceStatus;
	notes?: string;
};

export const mockSignups: Signup[] = [
	{
		id: 'sg-001',
		sessionId: '11dd3daa-d45a-4ce4-b686-57470b42c483',
		sessionName: 'Wellington High School',
		location: 'Wellington',
		studentName: 'Ari Thompson',
		studentAge: 15,
		guardianName: 'Mere Thompson',
		email: 'mere@example.com',
		phone: '+64 21 555 0101',
		medical: 'Peanut allergy',
		heardFrom: 'School newsletter',
		consentMedia: true,
		subscribeNewsletter: true,
		status: 'confirmed',
		createdAt: '2026-01-05T10:30:00Z',
	},
	{
		id: 'sg-002',
		sessionId: '44qq6qnn-q78n-7pr7-o9l9-8k7k3p75p7l6',
		sessionName: 'Whitby Library',
		location: 'Porirua',
		studentName: 'Leo Faumuina',
		studentAge: 11,
		guardianName: 'Sala Faumuina',
		email: 'sala@example.com',
		phone: '+64 27 222 3030',
		medical: '',
		heardFrom: 'Friend',
		consentMedia: false,
		subscribeNewsletter: false,
		status: 'pending',
		createdAt: '2026-01-06T14:15:00Z',
	},
	{
		id: 'sg-003',
		sessionId: '22oo4oll-o56l-5np5-m7j7-6i5i1n53n5j4',
		sessionName: 'Wainuiomata Community Library',
		location: 'Lower Hutt',
		studentName: 'Isla Ngata',
		studentAge: 10,
		guardianName: 'Hana Ngata',
		email: 'hana@example.com',
		phone: '+64 22 444 7878',
		medical: 'Asthma inhaler',
		heardFrom: 'Facebook',
		consentMedia: true,
		subscribeNewsletter: true,
		status: 'waitlisted',
		createdAt: '2026-01-04T09:00:00Z',
	},
	{
		id: 'sg-004',
		sessionId: '11dd3daa-d45a-4ce4-b686-57470b42c483',
		sessionName: 'Wellington High School',
		location: 'Wellington',
		studentName: 'Emma Chen',
		studentAge: 14,
		guardianName: 'Mike Chen',
		email: 'mike.chen@example.com',
		phone: '+64 22 234 5678',
		medical: '',
		heardFrom: 'Website',
		consentMedia: true,
		subscribeNewsletter: true,
		status: 'waitlisted',
		createdAt: '2026-01-06T11:45:00Z',
	},
	{
		id: 'sg-005',
		sessionId: '66ii8iff-i90f-9hj9-g1d1-0c9c5h97h9d8',
		sessionName: 'Te Whare Pukapuka o Te Māhanga - Karori Library',
		location: 'Wellington',
		studentName: 'Olivia Williams',
		studentAge: 12,
		guardianName: 'Lisa Williams',
		email: 'lisa.w@example.com',
		phone: '+64 27 345 6789',
		medical: '',
		heardFrom: 'Community board',
		consentMedia: true,
		subscribeNewsletter: false,
		status: 'waitlisted',
		createdAt: '2026-01-07T13:00:00Z',
	},
	{
		id: 'sg-006',
		sessionId: '99ll1lii-l23i-2km2-j4g4-3f2f8k20k2g1',
		sessionName: 'Te Mako Naenae Community Centre',
		location: 'Lower Hutt',
		studentName: 'Noah Brown',
		studentAge: 11,
		guardianName: 'David Brown',
		email: 'david.b@example.com',
		phone: '+64 21 456 7890',
		medical: 'ADHD medication',
		heardFrom: 'School',
		consentMedia: false,
		subscribeNewsletter: true,
		status: 'waitlisted',
		createdAt: '2026-01-07T11:45:00Z',
	},
	{
		id: 'sg-007',
		sessionId: '33pp5pmm-p67m-6oq6-n8k8-7j6j2o64o6k5',
		sessionName: 'Mana College',
		location: 'Porirua',
		studentName: 'Sophia Wilson',
		studentAge: 16,
		guardianName: 'James Wilson',
		email: 'james.w@example.com',
		phone: '+64 27 678 9012',
		medical: '',
		heardFrom: 'Teacher',
		consentMedia: true,
		subscribeNewsletter: true,
		status: 'confirmed',
		createdAt: '2026-01-03T16:20:00Z',
	},
];

export const mockAttendance: AttendanceRecord[] = [
	{
		id: 'att-001',
		signupId: 'sg-001',
		sessionId: '11dd3daa-d45a-4ce4-b686-57470b42c483',
		date: '2026-01-07',
		status: 'present',
	},
	{
		id: 'att-002',
		signupId: 'sg-007',
		sessionId: '33pp5pmm-p67m-6oq6-n8k8-7j6j2o64o6k5',
		date: '2026-01-02',
		status: 'present',
	},
	{
		id: 'att-003',
		signupId: 'sg-007',
		sessionId: '33pp5pmm-p67m-6oq6-n8k8-7j6j2o64o6k5',
		date: '2026-01-09',
		status: 'absent',
		notes: 'Sick',
	},
];

// Helper functions
export function getSignupsBySession(sessionId: string): Signup[] {
	return mockSignups.filter((s) => s.sessionId === sessionId);
}

export function getWaitlistedSignups(): Signup[] {
	return mockSignups.filter((s) => s.status === 'waitlisted');
}

export function getConfirmedSignups(): Signup[] {
	return mockSignups.filter((s) => s.status === 'confirmed');
}

export function getPendingSignups(): Signup[] {
	return mockSignups.filter((s) => s.status === 'pending');
}

export function getAttendanceBySession(sessionId: string): AttendanceRecord[] {
	return mockAttendance.filter((a) => a.sessionId === sessionId);
}

export function getSignupById(id: string): Signup | undefined {
	return mockSignups.find((s) => s.id === id);
}
