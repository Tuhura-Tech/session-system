import { ArrowLeft, Mail, MapPin, Phone } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { adminApi } from '../services/api';
import type { Session, SessionLocation } from '../types';

export default function LocationDetail() {
	const { id } = useParams<{ id: string }>();
	const navigate = useNavigate();
	const mapRef = useRef<HTMLDivElement>(null);
	const [location, setLocation] = useState<SessionLocation | null>(null);
	const [sessions, setSessions] = useState<Session[]>([]);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const mapInstanceRef = useRef<any>(null);

	useEffect(() => {
		const fetchLocation = async () => {
			try {
				if (!id) {
					setError('Location ID not provided');
					return;
				}
				const data = await adminApi.getLocation(id);
				setLocation(data);
				// Load sessions at this location
				const sess = await adminApi.getLocationSessions(id);
				setSessions(sess);
			} catch (err) {
				setError('Failed to load location');
				console.error(err);
			} finally {
				setLoading(false);
			}
		};

		fetchLocation();
	}, [id]);

	useEffect(() => {
		if (!location || !mapRef.current) return;

		// Dynamically import Leaflet
		const initMap = async () => {
			try {
				const L = await import('leaflet');

				// Clean up existing map instance
				if (mapInstanceRef.current) {
					mapInstanceRef.current.remove();
				}

				if (!mapRef.current) return;

				// Create map
				const map = L.map(mapRef.current).setView([location.lat || 0, location.lng || 0], 15);

				// Add tile layer (OpenStreetMap)
				L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
					attribution: '© OpenStreetMap contributors',
					maxZoom: 19,
				}).addTo(map);

				// Create custom marker icon
				const markerIcon = L.icon({
					iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
					iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
					shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
					iconSize: [25, 41],
					iconAnchor: [12, 41],
					popupAnchor: [1, -34],
					shadowSize: [41, 41],
				});

				// Add marker with popup
				if (location.lat && location.lng) {
					const popup = L.popup().setLatLng([location.lat, location.lng]).setContent(`
              <div class="p-3 w-full max-w-xs">
                <h3 class="font-bold text-lg mb-2">${location.name}</h3>
                ${location.address ? `<p class="text-sm text-gray-700 mb-2">${location.address}</p>` : ''}
                ${location.contactName ? `<p class="text-sm"><strong>Contact:</strong> ${location.contactName}</p>` : ''}
                ${location.contactPhone ? `<p class="text-sm"><strong>Phone:</strong> <a href="tel:${location.contactPhone}" class="text-blue-500 hover:underline">${location.contactPhone}</a></p>` : ''}
                ${location.contactEmail ? `<p class="text-sm"><strong>Email:</strong> <a href="mailto:${location.contactEmail}" class="text-blue-500 hover:underline">${location.contactEmail}</a></p>` : ''}
                ${location.lat && location.lng ? `<a href="https://maps.google.com/?q=${location.lat},${location.lng}" target="_blank" class="text-blue-500 hover:underline text-sm mt-2 block">View on Google Maps</a>` : ''}
              </div>
            `);

					L.marker([location.lat, location.lng], {
						icon: markerIcon,
					})
						.bindPopup(popup)
						.addTo(map)
						.openPopup();

					// Fit map to marker
					map.fitBounds([[location.lat, location.lng]], { padding: [50, 50] });
				}

				mapInstanceRef.current = map;
			} catch (err) {
				console.error('Failed to initialize map:', err);
			}
		};

		initMap();

		return () => {
			if (mapInstanceRef.current) {
				mapInstanceRef.current.remove();
				mapInstanceRef.current = null;
			}
		};
	}, [location]);

	if (loading) {
		return (
			<div className="flex h-screen items-center justify-center">
				<div className="text-center">
					<div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-blue-500" />
					<p className="text-gray-600">Loading location...</p>
				</div>
			</div>
		);
	}

	if (error || !location) {
		return (
			<div className="flex h-screen items-center justify-center">
				<div className="text-center">
					<p className="mb-4 text-red-600">{error || 'Location not found'}</p>
					<button
						onClick={() => navigate('/locations')}
						className="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
					>
						Back to Locations
					</button>
				</div>
			</div>
		);
	}

	return (
		<div className="min-h-screen bg-gray-50 px-4 py-6 sm:px-6 lg:px-8">
			<div className="mx-auto max-w-4xl">
				{/* Header */}
				<div className="mb-6 flex items-center gap-4">
					<button
						onClick={() => navigate('/locations')}
						className="rounded-lg p-2 transition hover:bg-gray-200"
						title="Back"
					>
						<ArrowLeft className="h-5 w-5 text-gray-600" />
					</button>
					<h1 className="text-3xl font-bold text-gray-900">{location.name}</h1>
				</div>

				{/* Map Section */}
				<div className="mb-6 overflow-hidden rounded-lg bg-white shadow-md">
					<div ref={mapRef} style={{ height: '400px', width: '100%' }} className="relative" />
				</div>

				{/* Details Section */}
				<div className="grid grid-cols-1 gap-6 md:grid-cols-2">
					{/* Address & Location Info */}
					<div className="rounded-lg bg-white p-6 shadow-md">
						<h2 className="mb-4 text-xl font-bold text-gray-900">Location Info</h2>
						<div className="space-y-3">
							{location.address && (
								<div className="flex gap-3">
									<MapPin className="mt-1 h-5 w-5 shrink-0 text-gray-500" />
									<div>
										<p className="text-sm font-medium text-gray-500">Address</p>
										<p className="text-gray-900">{location.address}</p>
									</div>
								</div>
							)}
							{location.lat && location.lng && (
								<div className="flex gap-3 border-t pt-3">
									<MapPin className="mt-1 h-5 w-5 shrink-0 text-gray-500" />
									<div>
										<p className="text-sm font-medium text-gray-500">Coordinates</p>
										<p className="text-gray-900">
											{location.lat.toFixed(6)}, {location.lng.toFixed(6)}
										</p>
									</div>
								</div>
							)}
						</div>
					</div>

					{/* Contact Info */}
					<div className="rounded-lg bg-white p-6 shadow-md">
						<h2 className="mb-4 text-xl font-bold text-gray-900">Contact Info</h2>
						<div className="space-y-3">
							{location.contactName && (
								<div>
									<p className="text-sm font-medium text-gray-500">Contact Name</p>
									<p className="text-gray-900">{location.contactName}</p>
								</div>
							)}
							{location.contactPhone && (
								<div className="flex gap-3 border-t pt-2">
									<Phone className="mt-1 h-5 w-5 shrink-0 text-gray-500" />
									<div>
										<p className="text-sm font-medium text-gray-500">Phone</p>
										<a
											href={`tel:${location.contactPhone}`}
											className="text-blue-600 hover:underline"
										>
											{location.contactPhone}
										</a>
									</div>
								</div>
							)}
							{location.contactEmail && (
								<div className="flex gap-3 border-t pt-2">
									<Mail className="mt-1 h-5 w-5 shrink-0 text-gray-500" />
									<div>
										<p className="text-sm font-medium text-gray-500">Email</p>
										<a
											href={`mailto:${location.contactEmail}`}
											className="text-blue-600 hover:underline"
										>
											{location.contactEmail}
										</a>
									</div>
								</div>
							)}
						</div>
					</div>
				</div>

				{/* Sessions at this Location */}
				<div className="mt-6 rounded-lg bg-white p-6 shadow-md">
					<h2 className="mb-4 text-xl font-bold text-gray-900">Sessions at this Location</h2>
					{sessions.length === 0 ? (
						<p className="text-gray-600">No sessions found.</p>
					) : (
						<ul className="divide-y">
							{sessions.map((s) => (
								<li key={s.id} className="flex items-center justify-between py-3">
									<div>
										<p className="font-medium text-gray-900">{s.name}</p>
										<p className="text-sm text-gray-600">
											Year {s.year} · {s.dayOfWeek ?? '—'} · {s.startTime ?? '—'} -{' '}
											{s.endTime ?? '—'}
										</p>
									</div>
									<button
										onClick={() => navigate(`/sessions/${s.id}`)}
										className="text-sm text-blue-600 hover:underline"
									>
										View
									</button>
								</li>
							))}
						</ul>
					)}
				</div>
			</div>
		</div>
	);
}
