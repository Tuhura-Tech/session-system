import { BadgeCheck, Ban, Plus, RefreshCcw, Users } from 'lucide-react';
import type React from 'react';
import { useEffect, useMemo, useState } from 'react';
import { FormCheckbox, FormInput } from '../components/FormComponents';
import Layout from '../components/Layout';
import Modal from '../components/Modal';
import Sidebar from '../components/Sidebar';
import { adminApi } from '../services/api';
import type { Staff, StaffListItem, StaffSessionSummary } from '../types';

const StaffPage: React.FC = () => {
	const [staff, setStaff] = useState<StaffListItem[]>([]);
	const [activeOnly, setActiveOnly] = useState(true);
	const [isLoading, setIsLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const [selectedStaff, setSelectedStaff] = useState<Staff | null>(null);
	const [staffSessions, setStaffSessions] = useState<StaffSessionSummary[]>([]);
	const [isLoadingDetails, setIsLoadingDetails] = useState(false);

	const [showCreateModal, setShowCreateModal] = useState(false);
	const [showEditModal, setShowEditModal] = useState(false);

	const [createForm, setCreateForm] = useState({
		name: '',
		email: '',
		ssoId: '',
	});
	const [editForm, setEditForm] = useState<Partial<Staff>>({});

	useEffect(() => {
		loadStaff();
	}, [activeOnly]);

	const loadStaff = async () => {
		try {
			setIsLoading(true);
			setError(null);
			const data = await adminApi.getStaff(activeOnly);
			setStaff(data);
		} catch (err) {
			console.error(err);
			setError('Failed to load staff list');
		} finally {
			setIsLoading(false);
		}
	};

	const loadStaffDetails = async (staffId: string) => {
		try {
			setIsLoadingDetails(true);
			const [details, sessions] = await Promise.all([
				adminApi.getStaffMember(staffId),
				adminApi.getStaffSessions(staffId),
			]);
			setSelectedStaff(details);
			setEditForm({
				name: details.name,
				email: details.email,
				active: details.active,
			});
			setStaffSessions(sessions);
		} catch (err) {
			console.error(err);
			alert('Failed to load staff details');
		} finally {
			setIsLoadingDetails(false);
		}
	};

	const handleCreate = async () => {
		if (!createForm.name || !createForm.email || !createForm.ssoId) {
			alert('Name, email, and SSO ID are required');
			return;
		}
		try {
			await adminApi.createStaff(createForm);
			setShowCreateModal(false);
			setCreateForm({ name: '', email: '', ssoId: '' });
			await loadStaff();
		} catch (err) {
			console.error(err);
			alert('Failed to create staff member');
		}
	};

	const handleUpdate = async () => {
		if (!selectedStaff) return;
		try {
			await adminApi.updateStaff(selectedStaff.id, {
				name: editForm.name,
				email: editForm.email,
				active: editForm.active,
			});
			setShowEditModal(false);
			await Promise.all([loadStaff(), loadStaffDetails(selectedStaff.id)]);
		} catch (err) {
			console.error(err);
			alert('Failed to update staff member');
		}
	};

	const activeCount = useMemo(() => staff.filter((s) => s.active).length, [staff]);

	return (
		<div className="flex min-h-screen">
			<Sidebar />
			<div className="flex-1">
				<Layout
					title="Staff"
					actions={
						<div className="flex items-center gap-3">
							<label className="inline-flex items-center text-sm text-gray-700">
								<FormCheckbox
									checked={activeOnly}
									onChange={(e) => setActiveOnly(e.target.checked)}
								/>
								<span className="ml-2">Show active only</span>
							</label>
							<button
								onClick={() => setShowCreateModal(true)}
								className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
							>
								<Plus className="mr-2 h-4 w-4" />
								New Staff
							</button>
							<button
								onClick={loadStaff}
								className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
							>
								<RefreshCcw className="mr-2 h-4 w-4" />
								Refresh
							</button>
						</div>
					}
				>
					{error && (
						<div className="mb-4 rounded-md bg-red-50 p-4 text-sm text-red-700">{error}</div>
					)}

					<div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
						<div className="rounded-lg bg-white shadow lg:col-span-2">
							<div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
								<div>
									<h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
										<Users className="h-5 w-5" /> Staff
									</h2>
									<p className="text-sm text-gray-500">
										{activeCount} active / {staff.length} shown
									</p>
								</div>
							</div>
							<div className="overflow-x-auto">
								<table className="min-w-full divide-y divide-gray-200">
									<thead className="bg-gray-50">
										<tr>
											<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
												Name
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
										{isLoading ? (
											<tr>
												<td colSpan={4} className="px-6 py-6 text-center text-gray-500">
													Loading staff...
												</td>
											</tr>
										) : staff.length === 0 ? (
											<tr>
												<td colSpan={4} className="px-6 py-6 text-center text-gray-500">
													No staff found
												</td>
											</tr>
										) : (
											staff.map((s) => (
												<tr key={s.id} className="hover:bg-gray-50">
													<td className="px-6 py-4 text-sm font-medium whitespace-nowrap text-gray-900">
														{s.name}
													</td>
													<td className="px-6 py-4 text-sm whitespace-nowrap text-gray-600">
														{s.email}
													</td>
													<td className="px-6 py-4 text-sm whitespace-nowrap">
														{s.active ? (
															<span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-1 text-xs font-semibold text-green-800">
																<BadgeCheck className="h-4 w-4" /> Active
															</span>
														) : (
															<span className="inline-flex items-center gap-1 rounded-full bg-gray-200 px-2 py-1 text-xs font-semibold text-gray-700">
																<Ban className="h-4 w-4" /> Inactive
															</span>
														)}
													</td>
													<td className="px-6 py-4 text-sm whitespace-nowrap">
														<button
															onClick={() => loadStaffDetails(s.id)}
															className="text-blue-600 hover:text-blue-800"
														>
															View
														</button>
													</td>
												</tr>
											))
										)}
									</tbody>
								</table>
							</div>
						</div>

						<div className="rounded-lg bg-white p-6 shadow">
							<h3 className="mb-3 text-lg font-semibold text-gray-900">Details</h3>
							{!selectedStaff && (
								<p className="text-sm text-gray-500">Select a staff member to view details.</p>
							)}
							{selectedStaff && (
								<div className="space-y-4">
									<div>
										<p className="text-sm text-gray-500">Name</p>
										<p className="text-base font-semibold text-gray-900">{selectedStaff.name}</p>
									</div>
									<div>
										<p className="text-sm text-gray-500">Email</p>
										<p className="text-base text-gray-800">{selectedStaff.email}</p>
									</div>
									<div className="flex items-center gap-2">
										{selectedStaff.active ? (
											<span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-1 text-xs font-semibold text-green-800">
												<BadgeCheck className="h-4 w-4" /> Active
											</span>
										) : (
											<span className="inline-flex items-center gap-1 rounded-full bg-gray-200 px-2 py-1 text-xs font-semibold text-gray-700">
												<Ban className="h-4 w-4" /> Inactive
											</span>
										)}
										{isLoadingDetails && <span className="text-xs text-gray-500">Refreshing…</span>}
									</div>

									<div className="flex gap-3">
										<button
											onClick={() => setShowEditModal(true)}
											className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700"
										>
											Edit
										</button>
										<button
											onClick={() => loadStaffDetails(selectedStaff.id)}
											className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
										>
											Refresh
										</button>
									</div>

									<div>
										<p className="mb-2 text-sm font-semibold text-gray-900">Assigned sessions</p>
										{staffSessions.length === 0 ? (
											<p className="text-sm text-gray-500">No assignments</p>
										) : (
											<ul className="space-y-2">
												{staffSessions.map((sess) => (
													<li key={sess.id} className="text-sm text-gray-800">
														<span className="font-medium">{sess.name}</span> · {sess.year}
														{sess.location ? ` · ${sess.location}` : ''}
													</li>
												))}
											</ul>
										)}
									</div>
								</div>
							)}
						</div>
					</div>
				</Layout>
			</div>

			<Modal
				isOpen={showCreateModal}
				onClose={() => setShowCreateModal(false)}
				title="Create staff member"
			>
				<div className="space-y-4">
					<FormInput
						label="Full name"
						value={createForm.name}
						onChange={(e) => setCreateForm((p) => ({ ...p, name: e.target.value }))}
						required
					/>
					<FormInput
						label="Email"
						type="email"
						value={createForm.email}
						onChange={(e) => setCreateForm((p) => ({ ...p, email: e.target.value }))}
						required
					/>
					<FormInput
						label="SSO ID"
						value={createForm.ssoId}
						onChange={(e) => setCreateForm((p) => ({ ...p, ssoId: e.target.value }))}
						required
						placeholder="e.g. OIDC sub"
					/>
					<div className="flex justify-end gap-3 pt-2">
						<button
							onClick={() => setShowCreateModal(false)}
							className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
						>
							Cancel
						</button>
						<button
							onClick={handleCreate}
							className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
						>
							Create
						</button>
					</div>
				</div>
			</Modal>

			<Modal
				isOpen={showEditModal}
				onClose={() => setShowEditModal(false)}
				title="Edit staff member"
			>
				<div className="space-y-4">
					<FormInput
						label="Full name"
						value={editForm.name || ''}
						onChange={(e) => setEditForm((p) => ({ ...p, name: e.target.value }))}
					/>
					<FormInput
						label="Email"
						type="email"
						value={editForm.email || ''}
						onChange={(e) => setEditForm((p) => ({ ...p, email: e.target.value }))}
					/>
					<FormCheckbox
						label="Active"
						checked={editForm.active ?? true}
						onChange={(e) => setEditForm((p) => ({ ...p, active: e.target.checked }))}
					/>
					<div className="flex justify-end gap-3 pt-2">
						<button
							onClick={() => setShowEditModal(false)}
							className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
						>
							Cancel
						</button>
						<button
							onClick={handleUpdate}
							className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
						>
							Save
						</button>
					</div>
				</div>
			</Modal>
		</div>
	);
};

export default StaffPage;
