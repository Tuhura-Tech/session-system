import { ChevronLeft, ChevronRight } from 'lucide-react';
import type React from 'react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminApi } from '../services/api';
import type { Occurrence, Session } from '../types';

interface CalendarViewProps {
	currentStaffId?: string;
}

interface CalendarDay {
	date: Date;
	isCurrentMonth: boolean;
	occurrences: Array<{
		id: string;
		sessionId: string;
		sessionName: string;
		startTime: string;
		endTime: string;
		isAssigned: boolean;
		cancelled: boolean;
	}>;
}

const CalendarView: React.FC<CalendarViewProps> = ({ currentStaffId }) => {
	const navigate = useNavigate();
	const [currentDate, setCurrentDate] = useState(new Date());
	const [calendarDays, setCalendarDays] = useState<CalendarDay[]>([]);
	const [isLoading, setIsLoading] = useState(true);

	useEffect(() => {
		loadCalendarData();
	}, [currentDate]);

	const loadCalendarData = async () => {
		try {
			setIsLoading(true);
			const year = currentDate.getFullYear();

			// Fetch all sessions for the year
			const allSessions = await adminApi.getSessions(year);

			// Fetch occurrences for each session
			const occurrencesPromises = allSessions.map((session) =>
				adminApi.getSessionOccurrences(session.id).catch(() => []),
			);
			const allOccurrences = await Promise.all(occurrencesPromises);

			// Build calendar grid
			const days = buildCalendarGrid(currentDate, allSessions, allOccurrences.flat());
			setCalendarDays(days);
		} catch (error) {
			console.error('Failed to load calendar data:', error);
		} finally {
			setIsLoading(false);
		}
	};

	const buildCalendarGrid = (
		date: Date,
		sessions: Session[],
		occurrences: Occurrence[],
	): CalendarDay[] => {
		const year = date.getFullYear();
		const month = date.getMonth();

		// First day of the month
		const firstDay = new Date(year, month, 1);

		// Start from the Monday before the first day of the month
		const startDate = new Date(firstDay);
		const dayOfWeek = firstDay.getDay();
		const daysToSubtract = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
		startDate.setDate(firstDay.getDate() - daysToSubtract);

		// Build 6 weeks (42 days) to cover all possible month layouts
		const days: CalendarDay[] = [];
		const currentDay = new Date(startDate);

		for (let i = 0; i < 42; i++) {
			const dateStr = currentDay.toISOString().split('T')[0];

			// Find occurrences for this day
			const dayOccurrences = occurrences
				.filter((occ) => occ.startsAt.split('T')[0] === dateStr)
				.map((occ) => {
					const session = sessions.find((s) => s.id === occ.sessionId);
					return {
						id: occ.id,
						sessionId: occ.sessionId,
						sessionName: session?.name || 'Unknown',
						startTime: session?.startTime || '',
						endTime: session?.endTime || '',
						isAssigned: false, // Staff assignments not included in calendar
						cancelled: occ.cancelled,
					};
				});

			days.push({
				date: new Date(currentDay),
				isCurrentMonth: currentDay.getMonth() === month,
				occurrences: dayOccurrences,
			});

			currentDay.setDate(currentDay.getDate() + 1);
		}

		return days;
	};

	const goToPreviousMonth = () => {
		setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
	};

	const goToNextMonth = () => {
		setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
	};

	const goToToday = () => {
		setCurrentDate(new Date());
	};

	const monthName = currentDate.toLocaleDateString('en-NZ', {
		month: 'long',
		year: 'numeric',
	});
	const weekDays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

	return (
		<div className="rounded-lg bg-white shadow">
			<div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
				<h2 className="text-lg font-semibold text-gray-900">Session Calendar</h2>
				<div className="flex items-center gap-2">
					<button
						onClick={goToToday}
						className="rounded-md bg-gray-100 px-3 py-1 text-sm hover:bg-gray-200"
					>
						Today
					</button>
					<button onClick={goToPreviousMonth} className="rounded p-1 hover:bg-gray-100">
						<ChevronLeft className="h-5 w-5" />
					</button>
					<span className="min-w-37.5 text-center text-sm font-medium">{monthName}</span>
					<button onClick={goToNextMonth} className="rounded p-1 hover:bg-gray-100">
						<ChevronRight className="h-5 w-5" />
					</button>
				</div>
			</div>

			<div className="p-4">
				{isLoading ? (
					<div className="py-12 text-center text-gray-500">Loading calendar...</div>
				) : (
					<div className="grid grid-cols-7 gap-1">
						{/* Week day headers */}
						{weekDays.map((day) => (
							<div key={day} className="py-2 text-center text-xs font-semibold text-gray-600">
								{day}
							</div>
						))}

						{/* Calendar days */}
						{calendarDays.map((day, index) => {
							const isToday = day.date.toDateString() === new Date().toDateString();

							return (
								<div
									key={index}
									className={`min-h-25 rounded border p-1 ${
										day.isCurrentMonth ? 'border-gray-200 bg-white' : 'border-gray-100 bg-gray-50'
									} ${isToday ? 'ring-2 ring-blue-500' : ''}`}
								>
									<div
										className={`mb-1 text-xs font-medium ${
											day.isCurrentMonth ? 'text-gray-900' : 'text-gray-400'
										} ${isToday ? 'font-bold text-blue-600' : ''}`}
									>
										{day.date.getDate()}
									</div>

									<div className="space-y-1">
										{day.occurrences.map((occ) => (
											<div
												key={occ.id}
												onClick={() => !occ.cancelled && navigate(`/attendance/${occ.id}`)}
												className={`truncate rounded p-1 text-xs ${
													occ.cancelled
														? 'cursor-not-allowed bg-gray-200 text-gray-500 line-through'
														: occ.isAssigned
															? 'cursor-pointer bg-blue-100 font-medium text-blue-800 hover:bg-blue-200'
															: 'cursor-pointer bg-green-100 text-green-800 hover:bg-green-200'
												}`}
												title={`${occ.sessionName} ${occ.startTime}-${occ.endTime}${occ.cancelled ? ' (Cancelled)' : ''}${!occ.cancelled ? ' - Click to view attendance' : ''}`}
											>
												{occ.startTime && `${occ.startTime} `}
												{occ.sessionName}
											</div>
										))}
									</div>
								</div>
							);
						})}
					</div>
				)}
			</div>

			{/* Legend */}
			<div className="flex gap-4 border-t border-gray-200 px-6 py-3 text-xs">
				{currentStaffId && (
					<div className="flex items-center gap-2">
						<div className="h-3 w-3 rounded bg-blue-100" />
						<span className="text-gray-600">Your sessions</span>
					</div>
				)}
				<div className="flex items-center gap-2">
					<div className="h-3 w-3 rounded bg-green-100" />
					<span className="text-gray-600">Other sessions</span>
				</div>
				<div className="flex items-center gap-2">
					<div className="h-3 w-3 rounded bg-gray-200" />
					<span className="text-gray-600">Cancelled</span>
				</div>
			</div>
		</div>
	);
};

export default CalendarView;
