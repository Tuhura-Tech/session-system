import { Calendar, MapPin, TrendingUp, Users } from 'lucide-react';
import type React from 'react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { LoadingSpinner } from '../components/Alert';
import CalendarView from '../components/CalendarView';
import Layout from '../components/Layout';
import Sidebar from '../components/Sidebar';
import { adminApi } from '../services/api';
import type { Session } from '../types';

const Dashboard: React.FC = () => {
	const [stats, setStats] = useState({
		totalSessions: 0,
		activeSessions: 0,
		totalLocations: 0,
		currentYear: new Date().getFullYear(),
	});
	const [recentSessions, setRecentSessions] = useState<Session[]>([]);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	useEffect(() => {
		loadDashboardData();
	}, []);

	const loadDashboardData = async () => {
		try {
			setIsLoading(true);
			setError(null);
			const currentYear = new Date().getFullYear();

			const [sessions, locations] = await Promise.all([
				adminApi.getSessions(currentYear),
				adminApi.getLocations(),
			]);

			const activeSessions = sessions.filter((s) => !s.archived);

			setStats({
				totalSessions: sessions.length,
				activeSessions: activeSessions.length,
				totalLocations: locations.length,
				currentYear,
			});

			setRecentSessions(activeSessions.slice(0, 5));
		} catch (err) {
			console.error('Failed to load dashboard data:', err);
			setError('Failed to load dashboard data. Please try again.');
		} finally {
			setIsLoading(false);
		}
	};

	return (
		<div className="flex min-h-screen">
			<Sidebar />

			<div className="flex-1">
				<Layout title="Dashboard">
					{error && (
						<div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-red-700">
							{error}
						</div>
					)}

					{isLoading ? (
						<LoadingSpinner />
					) : (
						<>
							{/* Stats Cards */}
							<div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-3">
								<div className="rounded-lg bg-white p-6 shadow transition-shadow hover:shadow-lg">
									<div className="flex items-center">
										<div className="rounded-full bg-blue-100 p-3 text-blue-600">
											<Calendar className="h-6 w-6" />
										</div>
										<div className="ml-4">
											<p className="text-sm font-medium text-gray-600">Total Sessions</p>
											<p className="text-2xl font-semibold text-gray-900">{stats.totalSessions}</p>
											<p className="mt-1 text-xs text-gray-500">{stats.currentYear}</p>
										</div>
									</div>
								</div>

								<div className="rounded-lg bg-white p-6 shadow transition-shadow hover:shadow-lg">
									<div className="flex items-center">
										<div className="rounded-full bg-green-100 p-3 text-green-600">
											<TrendingUp className="h-6 w-6" />
										</div>
										<div className="ml-4">
											<p className="text-sm font-medium text-gray-600">Active Sessions</p>
											<p className="text-2xl font-semibold text-gray-900">{stats.activeSessions}</p>
											<p className="mt-1 text-xs text-gray-500">
												{stats.totalSessions > 0
													? `${Math.round((stats.activeSessions / stats.totalSessions) * 100)}% of total`
													: 'N/A'}
											</p>
										</div>
									</div>
								</div>

								<div className="rounded-lg bg-white p-6 shadow transition-shadow hover:shadow-lg">
									<div className="flex items-center">
										<div className="rounded-full bg-purple-100 p-3 text-purple-600">
											<MapPin className="h-6 w-6" />
										</div>
										<div className="ml-4">
											<p className="text-sm font-medium text-gray-600">Locations</p>
											<p className="text-2xl font-semibold text-gray-900">{stats.totalLocations}</p>
											<p className="mt-1 text-xs text-gray-500">Available venues</p>
										</div>
									</div>
								</div>
							</div>

							{/* Quick Actions */}
							<div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-3">
								<Link
									to="/sessions/new"
									className="group flex items-center gap-4 rounded-lg bg-white p-6 shadow transition-shadow hover:shadow-lg"
								>
									<div className="rounded-full bg-blue-50 p-3 text-blue-600 group-hover:bg-blue-100">
										<Calendar className="h-6 w-6" />
									</div>
									<div>
										<h3 className="font-semibold text-gray-900 group-hover:text-blue-600">
											New Session
										</h3>
										<p className="text-sm text-gray-500">Create a new session</p>
									</div>
								</Link>

								<Link
									to="/locations"
									className="group flex items-center gap-4 rounded-lg bg-white p-6 shadow transition-shadow hover:shadow-lg"
								>
									<div className="rounded-full bg-purple-50 p-3 text-purple-600 group-hover:bg-purple-100">
										<MapPin className="h-6 w-6" />
									</div>
									<div>
										<h3 className="font-semibold text-gray-900 group-hover:text-purple-600">
											Locations
										</h3>
										<p className="text-sm text-gray-500">Manage venues</p>
									</div>
								</Link>

								<Link
									to="/terms"
									className="group flex items-center gap-4 rounded-lg bg-white p-6 shadow transition-shadow hover:shadow-lg"
								>
									<div className="rounded-full bg-green-50 p-3 text-green-600 group-hover:bg-green-100">
										<Users className="h-6 w-6" />
									</div>
									<div>
										<h3 className="font-semibold text-gray-900 group-hover:text-green-600">
											Terms
										</h3>
										<p className="text-sm text-gray-500">Manage school terms</p>
									</div>
								</Link>
							</div>

							{/* Calendar View */}
							<div className="mb-8">
								<CalendarView />
							</div>

							{/* Recent Sessions */}
							<div className="rounded-lg bg-white shadow">
								<div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
									<h2 className="text-lg font-semibold text-gray-900">Recent Sessions</h2>
									<Link
										to="/sessions"
										className="text-sm font-medium text-blue-600 hover:text-blue-700"
									>
										View all →
									</Link>
								</div>
								<div className="p-6">
									{recentSessions.length === 0 ? (
										<div className="py-8 text-center">
											<p className="mb-4 text-gray-500">No sessions yet</p>
											<Link
												to="/sessions/new"
												className="inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
											>
												Create First Session
											</Link>
										</div>
									) : (
										<div className="space-y-3">
											{recentSessions.map((session) => (
												<Link
													key={session.id}
													to={`/sessions/${session.id}`}
													className="block rounded-lg border border-gray-200 p-4 transition-colors hover:border-blue-500 hover:bg-blue-50"
												>
													<div className="flex items-start justify-between">
														<div>
															<h3 className="font-semibold text-gray-900">{session.name}</h3>
															<p className="mt-1 text-sm text-gray-600">
																{session.dayOfWeek} {session.startTime} - {session.endTime}
															</p>
															{session.location && (
																<p className="mt-1 text-xs text-gray-500">
																	📍 {session.location.name}
																</p>
															)}
														</div>
														<div className="text-right">
															<span
																className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
																	session.waitlist
																		? 'bg-yellow-100 text-yellow-800'
																		: 'bg-green-100 text-green-800'
																}`}
															>
																{session.waitlist ? 'Waitlist' : 'Active'}
															</span>
														</div>
													</div>
												</Link>
											))}
										</div>
									)}
								</div>
							</div>
						</>
					)}
				</Layout>
			</div>
		</div>
	);
};

export default Dashboard;
