/**
 * Utility functions for date and time formatting
 */

export const formatDate = (date: string | Date): string => {
	const d = typeof date === 'string' ? new Date(date) : date;
	return d.toLocaleDateString('en-NZ', {
		year: 'numeric',
		month: 'long',
		day: 'numeric',
	});
};

export const formatDateTime = (date: string | Date): string => {
	const d = typeof date === 'string' ? new Date(date) : date;
	return d.toLocaleDateString('en-NZ', {
		year: 'numeric',
		month: 'short',
		day: 'numeric',
		hour: '2-digit',
		minute: '2-digit',
	});
};

export const formatTime = (timeString: string): string => {
	// Assuming time is in HH:MM format
	if (!timeString) return '-';
	return timeString;
};

export const formatAgeRange = (lower: number | null, upper: number | null): string => {
	if (!lower && !upper) return 'All ages';
	if (lower && !upper) return `${lower}+ years`;
	if (!lower && upper) return `Up to ${upper} years`;
	return `${lower}-${upper} years`;
};

export const getStatusColor = (status: string): string => {
	switch (status) {
		case 'confirmed':
			return 'bg-green-100 text-green-800';
		case 'waitlisted':
			return 'bg-yellow-100 text-yellow-800';
		case 'withdrawn':
			return 'bg-red-100 text-red-800';
		case 'pending':
			return 'bg-gray-100 text-gray-800';
		case 'present':
			return 'bg-green-100 text-green-800';
		case 'absent':
			return 'bg-red-100 text-red-800';
		case 'excused':
			return 'bg-yellow-100 text-yellow-800';
		default:
			return 'bg-gray-100 text-gray-800';
	}
};

export const getStatusLabel = (status: string): string => {
	return status.charAt(0).toUpperCase() + status.slice(1);
};
