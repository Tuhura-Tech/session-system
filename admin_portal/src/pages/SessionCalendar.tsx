import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { adminApi } from '../services/api';
import type { Occurrence, Session } from '../types';

export default function SessionCalendar() {
	const { id } = useParams<{ id: string }>();
	const [session, setSession] = useState<Session | null>(null);
	const [occurrences, setOccurrences] = useState<Occurrence[]>([]);
	const [currentDate, setCurrentDate] = useState(new Date());
	const [loading, setLoading] = useState(true);
	const [selectedOccurrence, setSelectedOccurrence] = useState<Occurrence | null>(null);

	useEffect(() => {
		const loadData = async () => {
			try {
				if (!id) return;
				const [sessionData, occurrencesData] = await Promise.all([
					adminApi.getSession(id),
					adminApi.getSessionOccurrences(id),
				]);
				setSession(sessionData);
				setOccurrences(occurrencesData);
			} catch (err) {
				console.error('Failed to load data:', err);
			} finally {
				setLoading(false);
			}
		};
		loadData();
	}, [id]);

	const getDaysInMonth = (date: Date) => {
		return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
	};

	const getFirstDayOfMonth = (date: Date) => {
		return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
	};

	const formatDate = (date: Date) => date.toISOString().split('T')[0];

	const getOccurrencesForDay = (day: number) => {
		const dateStr = formatDate(new Date(currentDate.getFullYear(), currentDate.getMonth(), day));
		return occurrences.filter((occ) => {
			const occDate = occ.startsAt.split('T')[0];
			return occDate === dateStr;
		});
	};

	const handlePrevMonth = () => {
		setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1));
	};

	const handleNextMonth = () => {
		setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1));
	};

	if (loading) {
		return (
			<div className="flex h-screen items-center justify-center">
				<div className="text-center">
					<div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-blue-500" />
					<p className="text-gray-600">Loading calendar...</p>
				</div>
			</div>
		);
	}

	const daysInMonth = getDaysInMonth(currentDate);
	const firstDay = getFirstDayOfMonth(currentDate);
	const monthName = currentDate.toLocaleString('default', {
		month: 'long',
		year: 'numeric',
	});
	const dayLabels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
	const calendarDays: (number | null)[] = [
		...Array.from({ length: firstDay }, () => null),
		...Array.from({ length: daysInMonth }, (_, i) => i + 1),
	];

	return (
		<div className="min-h-screen bg-gray-50 px-4 py-8">
			<div className="mx-auto max-w-6xl">
				{/* Header */}
				<div className="mb-8">
					<h1 className="mb-2 text-3xl font-bold text-gray-900">{session?.name} - Calendar</h1>
					<p className="text-gray-600">{occurrences.length} occurrences scheduled</p>
				</div>

				<div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
					{/* Calendar */}
					<div className="lg:col-span-2">
						<div className="overflow-hidden rounded-lg bg-white shadow-md">
							{/* Calendar Header */}
							<div className="border-b border-gray-200 bg-blue-50 px-6 py-4">
								<div className="flex items-center justify-between">
									<button
										onClick={handlePrevMonth}
										className="rounded p-2 transition hover:bg-blue-100"
									>
										<ChevronLeft className="h-5 w-5" />
									</button>
									<h2 className="min-w-40 text-center text-lg font-semibold text-gray-900">
										{monthName}
									</h2>
									<button
										onClick={handleNextMonth}
										className="rounded p-2 transition hover:bg-blue-100"
									>
										<ChevronRight className="h-5 w-5" />
									</button>
								</div>
							</div>

							{/* Day Labels */}
							<div className="grid grid-cols-7 border-b border-gray-200 bg-gray-100">
								{dayLabels.map((day) => (
									<div key={day} className="p-3 text-center text-sm font-semibold text-gray-700">
										{day}
									</div>
								))}
							</div>

							{/* Calendar Grid */}
							<div className="grid grid-cols-7 gap-px bg-gray-200 p-px">
								{calendarDays.map((day, idx) => {
									const dayOccurrences = day ? getOccurrencesForDay(day as number) : [];
									const isCurrentMonth = day !== null;
									const isToday =
										isCurrentMonth &&
										new Date().getDate() === day &&
										new Date().getMonth() === currentDate.getMonth() &&
										new Date().getFullYear() === currentDate.getFullYear();

									return (
										<div
											key={idx}
											className={`min-h-24 p-2 text-sm ${
												isCurrentMonth
													? `bg-white ${isToday ? 'ring-2 ring-blue-400' : ''}`
													: 'bg-gray-50'
											} cursor-pointer transition hover:bg-blue-50`}
										>
											{isCurrentMonth && (
												<>
													<div
														className={`mb-1 font-semibold ${isToday ? 'text-blue-600' : 'text-gray-900'}`}
													>
														{day}
													</div>
													<div className="space-y-1">
														{dayOccurrences.slice(0, 2).map((occ) => (
															<div
																key={occ.id}
																onClick={() => setSelectedOccurrence(occ)}
																className="truncate rounded bg-blue-100 px-1 py-0.5 text-xs text-blue-800 hover:bg-blue-200"
															>
																{new Date(occ.startsAt).toLocaleTimeString([], {
																	hour: '2-digit',
																	minute: '2-digit',
																})}
															</div>
														))}
														{dayOccurrences.length > 2 && (
															<div className="px-1 text-xs text-gray-500">
																+{dayOccurrences.length - 2} more
															</div>
														)}
													</div>
												</>
											)}
										</div>
									);
								})}
							</div>
						</div>
					</div>

					{/* Sidebar - Details */}
					<div className="lg:col-span-1">
						{selectedOccurrence ? (
							<div className="sticky top-6 rounded-lg bg-white p-6 shadow-md">
								<h3 className="mb-4 text-lg font-semibold text-gray-900">Occurrence Details</h3>

								<div className="space-y-4">
									<div>
										<p className="text-sm font-medium text-gray-500">Date & Time</p>
										<p className="mt-1 text-gray-900">
											{new Date(selectedOccurrence.startsAt).toLocaleString()}
										</p>
									</div>

									<div>
										<p className="text-sm font-medium text-gray-500">Status</p>
										<p className="mt-1 text-gray-900 capitalize">
											{selectedOccurrence.cancelled ? (
												<span className="text-red-600">Cancelled</span>
											) : (
												'Scheduled'
											)}
										</p>
									</div>

									{selectedOccurrence.cancellationReason && (
										<div>
											<p className="text-sm font-medium text-gray-500">Cancellation Reason</p>
											<p className="mt-1 text-gray-900">{selectedOccurrence.cancellationReason}</p>
										</div>
									)}
								</div>

								<button
									onClick={() => setSelectedOccurrence(null)}
									className="mt-6 w-full rounded-md bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-200"
								>
									Close
								</button>
							</div>
						) : (
							<div className="rounded-lg bg-white p-6 shadow-md">
								<p className="text-center text-gray-500">Click an occurrence to view details</p>
							</div>
						)}
					</div>
				</div>
			</div>
		</div>
	);
}
