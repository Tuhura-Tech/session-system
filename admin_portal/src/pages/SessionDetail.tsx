import { ArrowLeft, Copy, Download, Edit, Mail, Megaphone, Trash2, Users } from 'lucide-react';
import type React from 'react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import Layout from '../components/Layout';
import Sidebar from '../components/Sidebar';
import { downloadBlob } from '../lib/export';
import { getStatusColor } from '../lib/utils';
import { adminApi } from '../services/api';
import type { Occurrence, Session, Signup, StaffListItem } from '../types';

const SessionDetail: React.FC = () => {
	const { id } = useParams<{ id: string }>();
	const navigate = useNavigate();
	const [session, setSession] = useState<Session | null>(null);
	const [signups, setSignups] = useState<Signup[]>([]);
	const [occurrences, setOccurrences] = useState<Occurrence[]>([]);
	const [isLoading, setIsLoading] = useState(true);
	const [activeTab, setActiveTab] = useState<'signups' | 'occurrences' | 'staff' | 'comms'>(
		'signups',
	);
	const [statusFilter, setStatusFilter] = useState<string>('');

	const [sessionStaff, setSessionStaff] = useState<StaffListItem[]>([]);
	const [allStaff, setAllStaff] = useState<StaffListItem[]>([]);
	const [selectedStaffIds, setSelectedStaffIds] = useState<string[]>([]);
	const [isSavingStaff, setIsSavingStaff] = useState(false);

	const [bulkSubject, setBulkSubject] = useState('');
	const [bulkMessage, setBulkMessage] = useState('');
	const [notifyTitle, setNotifyTitle] = useState('');
	const [notifyMessage, setNotifyMessage] = useState('');
	const [notifyDate, setNotifyDate] = useState('');
	const [commsStatus, setCommsStatus] = useState<string | null>(null);

	useEffect(() => {
		if (id) {
			loadSessionData(id);
		}
	}, [id]);

	const loadSessionData = async (sessionId: string) => {
		try {
			setIsLoading(true);
			const [sessionData, signupsData, occurrencesData] = await Promise.all([
				adminApi.getSession(sessionId),
				adminApi.getSessionSignups(sessionId),
				adminApi.getSessionOccurrences(sessionId),
			]);
			setSession(sessionData);
			setSignups(signupsData);
			setOccurrences(occurrencesData);
			await loadStaffData(sessionId);
		} catch (error) {
			console.error('Failed to load session data:', error);
		} finally {
			setIsLoading(false);
		}
	};

	const loadStaffData = async (sessionId: string) => {
		try {
			const [assigned, staffList] = await Promise.all([
				adminApi.getSessionStaff(sessionId),
				adminApi.getStaff(false),
			]);
			setSessionStaff(assigned);
			setAllStaff(staffList);
			setSelectedStaffIds(assigned.map((s) => s.id));
		} catch (error) {
			console.error('Failed to load staff data:', error);
		}
	};

	const handleStatusChange = async (signupId: string, newStatus: string) => {
		try {
			await adminApi.updateSignupStatus(signupId, newStatus);
			if (id) {
				const updatedSignups = await adminApi.getSessionSignups(id);
				setSignups(updatedSignups);
			}
		} catch (error) {
			console.error('Failed to update signup status:', error);
			alert('Failed to update signup status');
		}
	};

	const handleExportSignups = async () => {
		if (!id || !session) return;
		try {
			const blob = await adminApi.exportSignupsCSV(id, statusFilter || undefined);
			downloadBlob(blob, `signups-${session.name}.csv`);
		} catch (error) {
			console.error('Failed to export signups:', error);
			alert('Failed to export signups');
		}
	};

	const handleGenerateOccurrences = async () => {
		if (!id) return;
		if (!confirm('This will generate occurrences based on the session schedule. Continue?')) return;

		try {
			const result = await adminApi.generateOccurrences(id);
			alert(`Generated ${result.created} occurrences`);
			const updatedOccurrences = await adminApi.getSessionOccurrences(id);
			setOccurrences(updatedOccurrences);
		} catch (error) {
			console.error('Failed to generate occurrences:', error);
			alert('Failed to generate occurrences');
		}
	};

	const handleSaveStaff = async () => {
		if (!id) return;
		try {
			setIsSavingStaff(true);
			await adminApi.assignSessionStaff(id, selectedStaffIds);
			await loadStaffData(id);
		} catch (error) {
			console.error('Failed to update staff assignments:', error);
			alert('Failed to update staff assignments');
		} finally {
			setIsSavingStaff(false);
		}
	};

	const handleCancelOccurrence = async (occurrenceId: string) => {
		const reason = prompt('Enter cancellation reason (optional):');
		if (reason === null) return;

		try {
			await adminApi.cancelOccurrence(occurrenceId, reason || undefined);
			if (id) {
				const updated = await adminApi.getSessionOccurrences(id);
				setOccurrences(updated);
				alert('Occurrence cancelled');
			}
		} catch (error) {
			console.error('Failed to cancel occurrence:', error);
			alert('Failed to cancel occurrence');
		}
	};

	const handleReinstateOccurrence = async (occurrenceId: string) => {
		try {
			await adminApi.reinstateOccurrence(occurrenceId);
			if (id) {
				const updated = await adminApi.getSessionOccurrences(id);
				setOccurrences(updated);
				alert('Occurrence reinstated');
			}
		} catch (error) {
			console.error('Failed to reinstate occurrence:', error);
			alert('Failed to reinstate occurrence');
		}
	};

	const handleBulkEmail = async () => {
		if (!id) return;
		if (!bulkSubject.trim() || !bulkMessage.trim()) {
			alert('Subject and message are required');
			return;
		}
		try {
			setCommsStatus('Sending bulk email...');
			const res = await adminApi.bulkEmailSession(id, {
				subject: bulkSubject,
				message: bulkMessage,
			});
			setCommsStatus(`Enqueued ${res.enqueued} emails`);
			setBulkSubject('');
			setBulkMessage('');
		} catch (error) {
			console.error('Failed to send bulk email:', error);
			setCommsStatus('Failed to send bulk email');
		}
	};

	const handleNotify = async () => {
		if (!id) return;
		if (!notifyTitle.trim()) {
			alert('Update title is required');
			return;
		}
		try {
			setCommsStatus('Sending notification...');
			const res = await adminApi.notifySession(id, {
				updateTitle: notifyTitle,
				updateMessage: notifyMessage || null,
				affectedDate: notifyDate || null,
			});
			setCommsStatus(`Enqueued ${res.enqueued} notifications`);
			setNotifyTitle('');
			setNotifyMessage('');
			setNotifyDate('');
		} catch (error) {
			console.error('Failed to send notification:', error);
			setCommsStatus('Failed to send notification');
		}
	};

	const handleDeleteSession = async () => {
		if (!id) return;
		if (!confirm('Are you sure you want to delete this session? This cannot be undone.')) return;

		try {
			await adminApi.deleteSession(id);
			alert('Session deleted successfully');
			navigate('/sessions');
		} catch (error) {
			console.error('Failed to delete session:', error);
			alert('Failed to delete session');
		}
	};

	const handleDuplicateSession = async () => {
		if (!id) return;
		if (!confirm('This will create a copy of this session. Continue?')) return;

		try {
			const duplicated = await adminApi.duplicateSession(id);
			alert('Session duplicated successfully');
			navigate(`/sessions/${duplicated.id}`);
		} catch (error) {
			console.error('Failed to duplicate session:', error);
			alert('Failed to duplicate session');
		}
	};

	const filteredSignups = statusFilter ? signups.filter((s) => s.status === statusFilter) : signups;

	if (isLoading) {
		return (
			<div className="flex min-h-screen">
				<Sidebar />
				<div className="flex flex-1 items-center justify-center">
					<div className="h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600" />
				</div>
			</div>
		);
	}

	if (!session) {
		return (
			<div className="flex min-h-screen">
				<Sidebar />
				<div className="flex-1">
					<Layout>
						<div className="py-12 text-center">
							<p className="text-gray-500">Session not found</p>
							<button
								onClick={() => navigate('/sessions')}
								className="mt-4 inline-block text-blue-600 hover:text-blue-700"
							>
								Back to Sessions
							</button>
						</div>
					</Layout>
				</div>
			</div>
		);
	}

	return (
		<div className="flex min-h-screen">
			<Sidebar />

			<div className="flex-1">
				<Layout>
					{/* Header */}
					<div className="mb-6">
						<button
							onClick={() => navigate('/sessions')}
							className="mb-4 flex items-center text-gray-600 hover:text-gray-900"
						>
							<ArrowLeft className="mr-2 h-4 w-4" />
							Back to Sessions
						</button>

						<div className="flex items-start justify-between">
							<div>
								<h1 className="text-3xl font-bold text-gray-900">{session.name}</h1>
								{session.description && <p className="mt-2 text-gray-600">{session.description}</p>}
							</div>
							<div className="flex gap-2">
								<button
									onClick={handleDuplicateSession}
									className="inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
								>
									<Copy className="mr-2 h-4 w-4" />
									Duplicate
								</button>
								<button
									onClick={() => navigate(`/sessions/${id}/edit`)}
									className="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
								>
									<Edit className="mr-2 h-4 w-4" />
									Edit
								</button>
								<button
									onClick={handleDeleteSession}
									className="inline-flex items-center rounded-md border border-transparent bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-red-700"
								>
									<Trash2 className="mr-2 h-4 w-4" />
									Delete
								</button>
							</div>
						</div>
					</div>

					{/* Session Info */}
					<div className="mb-6 rounded-lg bg-white p-6 shadow">
						<div className="grid grid-cols-1 gap-6 md:grid-cols-3">
							<div className="flex items-start">
								<div className="mt-0.5 mr-3 text-gray-400">📅</div>
								<div>
									<p className="text-sm font-medium text-gray-500">Schedule</p>
									<p className="mt-1 text-sm text-gray-900">
										{session.dayOfWeek} {session.startTime} - {session.endTime}
									</p>
								</div>
							</div>

							<div className="flex items-start">
								<div className="mt-0.5 mr-3 text-gray-400">📍</div>
								<div>
									<p className="text-sm font-medium text-gray-500">Location</p>
									<p className="mt-1 text-sm text-gray-900">
										{session.location?.name || 'No location set'}
									</p>
								</div>
							</div>

							<div className="flex items-start">
								<div className="mt-0.5 mr-3 text-gray-400">👥</div>
								<div>
									<p className="text-sm font-medium text-gray-500">Capacity</p>
									<p className="mt-1 text-sm text-gray-900">
										{signups.filter((s) => s.status === 'confirmed').length} /{' '}
										{session.capacity || 'Unlimited'}
									</p>
								</div>
							</div>
						</div>
					</div>

					{/* Tabs */}
					<div className="mb-6 border-b border-gray-200">
						<nav className="-mb-px flex space-x-8">
							<button
								onClick={() => setActiveTab('signups')}
								className={`border-b-2 px-1 py-4 text-sm font-medium ${
									activeTab === 'signups'
										? 'border-blue-500 text-blue-600'
										: 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
								}`}
							>
								Signups ({signups.length})
							</button>
							<button
								onClick={() => setActiveTab('occurrences')}
								className={`border-b-2 px-1 py-4 text-sm font-medium ${
									activeTab === 'occurrences'
										? 'border-blue-500 text-blue-600'
										: 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
								}`}
							>
								Occurrences ({occurrences.length})
							</button>
							<button
								onClick={() => setActiveTab('staff')}
								className={`border-b-2 px-1 py-4 text-sm font-medium ${
									activeTab === 'staff'
										? 'border-blue-500 text-blue-600'
										: 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
								}`}
							>
								Staff ({sessionStaff.length})
							</button>
							<button
								onClick={() => setActiveTab('comms')}
								className={`border-b-2 px-1 py-4 text-sm font-medium ${
									activeTab === 'comms'
										? 'border-blue-500 text-blue-600'
										: 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
								}`}
							>
								Communications
							</button>
						</nav>
					</div>

					{/* Signups Tab */}
					{activeTab === 'signups' && (
						<div className="rounded-lg bg-white shadow">
							<div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
								<div className="flex items-center gap-4">
									<h2 className="text-lg font-semibold text-gray-900">Signups</h2>
									<select
										value={statusFilter}
										onChange={(e) => setStatusFilter(e.target.value)}
										className="rounded-md border-gray-300 px-3 py-1 text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500"
									>
										<option value="">All statuses</option>
										<option value="confirmed">Confirmed</option>
										<option value="waitlisted">Waitlisted</option>
										<option value="pending">Pending</option>
										<option value="withdrawn">Withdrawn</option>
									</select>
								</div>
								<button
									onClick={handleExportSignups}
									className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
								>
									<Download className="mr-2 h-4 w-4" />
									Export CSV
								</button>
							</div>

							<div className="overflow-x-auto">
								<table className="min-w-full divide-y divide-gray-200">
									<thead className="bg-gray-50">
										<tr>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
												Student
											</th>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
												Age
											</th>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
												Guardian
											</th>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
												Email
											</th>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
												Status
											</th>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
												Actions
											</th>
										</tr>
									</thead>
									<tbody className="divide-y divide-gray-200 bg-white">
										{filteredSignups.map((signup) => (
											<tr key={signup.id}>
												<td className="px-6 py-4 text-sm font-medium whitespace-nowrap text-gray-900">
													<button
														onClick={() => navigate(`/children/${signup.childId}`)}
														className="text-blue-600 hover:text-blue-800"
													>
														{signup.studentName}
													</button>
												</td>
												<td className="px-6 py-4 text-sm whitespace-nowrap text-gray-500">
													\n {signup.guardianName}\n{' '}
												</td>
												<td className="px-6 py-4 text-sm whitespace-nowrap text-gray-500">
													{signup.email}
												</td>
												<td className="px-6 py-4 whitespace-nowrap">
													<span
														className={`inline-flex rounded-full px-2 py-1 text-xs leading-5 font-semibold ${getStatusColor(
															signup.status,
														)}`}
													>
														{signup.status}
													</span>
												</td>
												<td className="px-6 py-4 text-sm whitespace-nowrap">
													<select
														value={signup.status}
														onChange={(e) => handleStatusChange(signup.id, e.target.value)}
														className="rounded-md border-gray-300 px-2 py-1 text-sm shadow-sm focus:border-blue-500 focus:ring-blue-500"
													>
														<option value="confirmed">Confirmed</option>
														<option value="waitlisted">Waitlisted</option>
														<option value="pending">Pending</option>
														<option value="withdrawn">Withdrawn</option>
													</select>
												</td>
											</tr>
										))}
									</tbody>
								</table>
								{filteredSignups.length === 0 && (
									<div className="py-12 text-center text-gray-500">No signups matching filter</div>
								)}
							</div>
						</div>
					)}

					{/* Occurrences Tab */}
					{activeTab === 'occurrences' && (
						<div className="rounded-lg bg-white shadow">
							<div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
								<h2 className="text-lg font-semibold text-gray-900">Occurrences</h2>
								<button
									onClick={handleGenerateOccurrences}
									className="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
								>
									Generate Occurrences
								</button>
							</div>

							<div className="overflow-x-auto">
								<table className="min-w-full divide-y divide-gray-200">
									<thead className="bg-gray-50">
										<tr>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
												Date
											</th>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
												Status
											</th>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
												Actions
											</th>
										</tr>
									</thead>
									<tbody className="divide-y divide-gray-200 bg-white">
										{occurrences.map((occurrence) => (
											<tr key={occurrence.id}>
												<td className="px-6 py-4 text-sm whitespace-nowrap text-gray-900">
													{new Date(occurrence.startsAt).toLocaleDateString('en-NZ', {
														day: '2-digit',
														month: '2-digit',
														year: 'numeric',
													})}
												</td>
												<td className="px-6 py-4 whitespace-nowrap">
													{occurrence.cancelled ? (
														<span className="inline-flex rounded-full bg-red-100 px-2 py-1 text-xs leading-5 font-semibold text-red-800">
															Cancelled
														</span>
													) : (
														<span className="inline-flex rounded-full bg-green-100 px-2 py-1 text-xs leading-5 font-semibold text-green-800">
															Active
														</span>
													)}
												</td>
												<td className="px-6 py-4 text-sm whitespace-nowrap">
													<button
														onClick={() => navigate(`/attendance/${occurrence.id}`)}
														className="mr-4 text-blue-600 hover:text-blue-900"
													>
														Attendance
													</button>
													{occurrence.cancelled ? (
														<button
															onClick={() => handleReinstateOccurrence(occurrence.id)}
															className="text-green-600 hover:text-green-900"
														>
															Reinstate
														</button>
													) : (
														<button
															onClick={() => handleCancelOccurrence(occurrence.id)}
															className="text-red-600 hover:text-red-900"
														>
															Cancel
														</button>
													)}
												</td>
											</tr>
										))}
									</tbody>
								</table>
								{occurrences.length === 0 && (
									<div className="py-12 text-center text-gray-500">
										No occurrences yet. Generate occurrences to get started.
									</div>
								)}
							</div>
						</div>
					)}

					{/* Staff Tab */}
					{activeTab === 'staff' && (
						<div className="rounded-lg bg-white shadow">
							<div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
								<div className="flex items-center gap-2">
									<Users className="h-5 w-5 text-gray-600" />
									<h2 className="text-lg font-semibold text-gray-900">Staff assignments</h2>
								</div>
								<button
									onClick={handleSaveStaff}
									disabled={isSavingStaff}
									className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
								>
									{isSavingStaff ? 'Saving...' : 'Save assignments'}
								</button>
							</div>
							<div className="grid grid-cols-1 gap-6 p-6 md:grid-cols-2">
								<div>
									<h3 className="mb-3 text-sm font-semibold text-gray-700">All staff</h3>
									<div className="max-h-80 space-y-2 overflow-y-auto rounded-lg border border-gray-200 p-3">
										{allStaff.length === 0 && (
											<p className="text-sm text-gray-500">No staff found</p>
										)}
										{allStaff.map((staffMember) => {
											const checked = selectedStaffIds.includes(staffMember.id);
											return (
												<label
													key={staffMember.id}
													className="flex cursor-pointer items-center justify-between rounded-md px-3 py-2 hover:bg-gray-50"
												>
													<div className="flex items-center gap-2">
														<input
															type="checkbox"
															checked={checked}
															onChange={(e) => {
																const isChecked = e.target.checked;
																setSelectedStaffIds((prev) =>
																	isChecked
																		? [...prev, staffMember.id]
																		: prev.filter((id) => id !== staffMember.id),
																);
															}}
															className="h-4 w-4 rounded border-gray-300 text-blue-600"
														/>
														<div>
															<p className="text-sm font-medium text-gray-900">
																{staffMember.name}
															</p>
															<p className="text-xs text-gray-500">{staffMember.email}</p>
														</div>
													</div>
													<span
														className={`rounded-full px-2 py-1 text-xs font-semibold ${
															staffMember.active
																? 'bg-green-100 text-green-800'
																: 'bg-gray-200 text-gray-700'
														}`}
													>
														{staffMember.active ? 'Active' : 'Inactive'}
													</span>
												</label>
											);
										})}
									</div>
								</div>

								<div>
									<h3 className="mb-3 text-sm font-semibold text-gray-700">
										Assigned to this session
									</h3>
									<div className="space-y-3">
										{sessionStaff.length === 0 && (
											<p className="text-sm text-gray-500">No staff assigned</p>
										)}
										{sessionStaff.map((staffMember) => (
											<div
												key={staffMember.id}
												className="flex items-center justify-between rounded-lg border border-gray-200 px-4 py-3"
											>
												<div>
													<p className="text-sm font-semibold text-gray-900">{staffMember.name}</p>
													<p className="text-xs text-gray-500">{staffMember.email}</p>
												</div>
												<button
													onClick={() => {
														setSelectedStaffIds((prev) =>
															prev.filter((id) => id !== staffMember.id),
														);
														setSessionStaff((prev) => prev.filter((s) => s.id !== staffMember.id));
													}}
													className="text-sm text-red-600 hover:text-red-800"
												>
													Remove
												</button>
											</div>
										))}
									</div>
								</div>
							</div>
						</div>
					)}

					{/* Communications Tab */}
					{activeTab === 'comms' && (
						<div className="rounded-lg bg-white shadow">
							<div className="border-b border-gray-200 px-6 py-4">
								<h2 className="text-lg font-semibold text-gray-900">Communications</h2>
								{commsStatus && <p className="mt-1 text-sm text-gray-500">{commsStatus}</p>}
							</div>
							<div className="grid grid-cols-1 gap-6 p-6 md:grid-cols-2">
								<div className="rounded-lg border border-gray-200 p-4">
									<div className="mb-3 flex items-center gap-2">
										<Mail className="h-4 w-4 text-gray-600" />
										<h3 className="text-base font-semibold text-gray-900">Bulk email</h3>
									</div>
									<div className="space-y-3">
										<input
											type="text"
											value={bulkSubject}
											onChange={(e) => setBulkSubject(e.target.value)}
											placeholder="Subject"
											className="w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:ring-blue-500"
										/>
										<textarea
											rows={6}
											value={bulkMessage}
											onChange={(e) => setBulkMessage(e.target.value)}
											placeholder="Message to caregivers"
											className="w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:ring-blue-500"
										/>
										<button
											onClick={handleBulkEmail}
											className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
										>
											Send bulk email
										</button>
									</div>
								</div>

								<div className="rounded-lg border border-gray-200 p-4">
									<div className="mb-3 flex items-center gap-2">
										<Megaphone className="h-4 w-4 text-gray-600" />
										<h3 className="text-base font-semibold text-gray-900">
											Notify confirmed signups
										</h3>
									</div>
									<div className="space-y-3">
										<input
											type="text"
											value={notifyTitle}
											onChange={(e) => setNotifyTitle(e.target.value)}
											placeholder="Update title"
											className="w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:ring-blue-500"
										/>
										<textarea
											rows={4}
											value={notifyMessage}
											onChange={(e) => setNotifyMessage(e.target.value)}
											placeholder="Optional message"
											className="w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:ring-blue-500"
										/>
										<div>
											<label className="mb-1 block text-sm font-medium text-gray-700">
												Affected date (optional)
											</label>
											<input
												type="date"
												value={notifyDate}
												onChange={(e) => setNotifyDate(e.target.value)}
												className="w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:ring-blue-500"
											/>
										</div>
										<button
											onClick={handleNotify}
											className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
										>
											Send notification
										</button>
									</div>
								</div>
							</div>
						</div>
					)}
				</Layout>
			</div>
		</div>
	);
};

export default SessionDetail;
