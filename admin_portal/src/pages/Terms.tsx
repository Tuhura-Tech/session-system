import { Edit2, Save, X } from 'lucide-react';
import type React from 'react';
import { useEffect, useMemo, useState } from 'react';
import Layout from '../components/Layout';
import Sidebar from '../components/Sidebar';
import { adminApi } from '../services/api';
import type { SessionBlock } from '../types';

const Terms: React.FC = () => {
	const [blocks, setBlocks] = useState<SessionBlock[]>([]);
	const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
	const [isLoading, setIsLoading] = useState(false);
	const [editingId, setEditingId] = useState<string | null>(null);
	const [editForm, setEditForm] = useState<Partial<SessionBlock>>({});
	const [isSaving, setIsSaving] = useState(false);

	useEffect(() => {
		loadBlocks();
	}, [selectedYear]);

	const loadBlocks = async () => {
		try {
			setIsLoading(true);
			const data = await adminApi.getBlocks(selectedYear);
			setBlocks(data);
		} catch (error) {
			console.error('Failed to load blocks', error);
		} finally {
			setIsLoading(false);
		}
	};

	const termBlocks = useMemo(
		() =>
			blocks
				.filter((b) => b.blockType.startsWith('term_'))
				.sort((a, b) => a.blockType.localeCompare(b.blockType)),
		[blocks],
	);
	const specialBlock = useMemo(() => blocks.find((b) => b.blockType === 'special'), [blocks]);

	const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 1 + i);

	const handleEdit = (block: SessionBlock) => {
		setEditingId(block.id);
		setEditForm({
			name: block.name,
			startDate: block.startDate,
			endDate: block.endDate,
			timezone: block.timezone,
		});
	};

	const handleCancelEdit = () => {
		setEditingId(null);
		setEditForm({});
	};

	const handleSaveEdit = async () => {
		if (!editingId) return;

		try {
			setIsSaving(true);
			await adminApi.updateBlock(editingId, editForm);
			await loadBlocks();
			setEditingId(null);
			setEditForm({});
		} catch (error) {
			console.error('Failed to update block', error);
			alert('Failed to update block');
		} finally {
			setIsSaving(false);
		}
	};

	return (
		<div className="flex min-h-screen">
			<Sidebar />
			<div className="flex-1">
				<Layout title="School Terms & Special">
					<div className="mb-6 rounded-lg bg-white p-4 shadow">
						<label className="mb-2 block text-sm font-medium text-gray-700">Year</label>
						<select
							value={selectedYear}
							onChange={(e) => setSelectedYear(Number(e.target.value))}
							className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
						>
							{years.map((year) => (
								<option key={year} value={year}>
									{year}
								</option>
							))}
						</select>
					</div>

					<div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
						<div className="overflow-hidden rounded-lg bg-white shadow">
							<div className="border-b border-gray-200 px-6 py-4">
								<h2 className="text-lg font-semibold text-gray-900">Terms</h2>
								<p className="text-sm text-gray-500">Click Edit to update term dates.</p>
							</div>
							{isLoading ? (
								<div className="flex h-48 items-center justify-center">
									<div className="h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600" />
								</div>
							) : termBlocks.length === 0 ? (
								<div className="py-10 text-center text-gray-500">
									No term blocks for {selectedYear}.
								</div>
							) : (
								<div className="overflow-x-auto">
									<table className="min-w-full divide-y divide-gray-200">
										<thead className="bg-gray-50">
											<tr>
												<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
													Term
												</th>
												<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
													Name
												</th>
												<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
													Start
												</th>
												<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
													End
												</th>
												<th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
													Actions
												</th>
											</tr>
										</thead>
										<tbody className="divide-y divide-gray-200 bg-white">
											{termBlocks.map((block) => (
												<tr key={block.id}>
													<td className="px-6 py-4 text-sm font-medium whitespace-nowrap text-gray-900">
														{block.blockType.replace('term_', 'Term ')}
													</td>
													{editingId === block.id ? (
														<>
															<td className="px-6 py-4 whitespace-nowrap">
																<input
																	type="text"
																	value={editForm.name || ''}
																	onChange={(e) =>
																		setEditForm({
																			...editForm,
																			name: e.target.value,
																		})
																	}
																	className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
																/>
															</td>
															<td className="px-6 py-4 whitespace-nowrap">
																<input
																	type="date"
																	value={editForm.startDate || ''}
																	onChange={(e) =>
																		setEditForm({
																			...editForm,
																			startDate: e.target.value,
																		})
																	}
																	className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
																/>
															</td>
															<td className="px-6 py-4 whitespace-nowrap">
																<input
																	type="date"
																	value={editForm.endDate || ''}
																	onChange={(e) =>
																		setEditForm({
																			...editForm,
																			endDate: e.target.value,
																		})
																	}
																	className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
																/>
															</td>
															<td className="px-6 py-4 whitespace-nowrap">
																<div className="flex gap-2">
																	<button
																		onClick={handleSaveEdit}
																		disabled={isSaving}
																		className="text-green-600 hover:text-green-900"
																	>
																		<Save className="h-4 w-4" />
																	</button>
																	<button
																		onClick={handleCancelEdit}
																		disabled={isSaving}
																		className="text-gray-600 hover:text-gray-900"
																	>
																		<X className="h-4 w-4" />
																	</button>
																</div>
															</td>
														</>
													) : (
														<>
															<td className="px-6 py-4 text-sm whitespace-nowrap text-gray-600">
																{block.name}
															</td>
															<td className="px-6 py-4 text-sm whitespace-nowrap text-gray-600">
																{new Date(block.startDate).toLocaleDateString('en-NZ', {
																	day: '2-digit',
																	month: '2-digit',
																	year: 'numeric',
																})}
															</td>
															<td className="px-6 py-4 text-sm whitespace-nowrap text-gray-600">
																{new Date(block.endDate).toLocaleDateString('en-NZ', {
																	day: '2-digit',
																	month: '2-digit',
																	year: 'numeric',
																})}
															</td>
															<td className="px-6 py-4 whitespace-nowrap">
																<button
																	onClick={() => handleEdit(block)}
																	className="text-blue-600 hover:text-blue-900"
																>
																	<Edit2 className="h-4 w-4" />
																</button>
															</td>
														</>
													)}
												</tr>
											))}
										</tbody>
									</table>
								</div>
							)}
						</div>

						<div className="overflow-hidden rounded-lg bg-white shadow">
							<div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
								<div>
									<h2 className="text-lg font-semibold text-gray-900">Special block</h2>
									<p className="text-sm text-gray-500">Covers one-off or holiday sessions.</p>
								</div>
								{specialBlock && !editingId && (
									<button
										onClick={() => handleEdit(specialBlock)}
										className="text-blue-600 hover:text-blue-900"
									>
										<Edit2 className="h-4 w-4" />
									</button>
								)}
							</div>
							{isLoading ? (
								<div className="flex h-48 items-center justify-center">
									<div className="h-12 w-12 animate-spin rounded-full border-b-2 border-blue-600" />
								</div>
							) : !specialBlock ? (
								<div className="py-10 text-center text-gray-500">
									No special block for {selectedYear}.
								</div>
							) : editingId === specialBlock.id ? (
								<div className="space-y-4 p-6">
									<div>
										<label className="mb-1 block text-sm font-medium text-gray-700">Name</label>
										<input
											type="text"
											value={editForm.name || ''}
											onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
											className="w-full rounded-md border border-gray-300 px-3 py-2"
										/>
									</div>
									<div>
										<label className="mb-1 block text-sm font-medium text-gray-700">
											Start Date
										</label>
										<input
											type="date"
											value={editForm.startDate || ''}
											onChange={(e) => setEditForm({ ...editForm, startDate: e.target.value })}
											className="w-full rounded-md border border-gray-300 px-3 py-2"
										/>
									</div>
									<div>
										<label className="mb-1 block text-sm font-medium text-gray-700">End Date</label>
										<input
											type="date"
											value={editForm.endDate || ''}
											onChange={(e) => setEditForm({ ...editForm, endDate: e.target.value })}
											className="w-full rounded-md border border-gray-300 px-3 py-2"
										/>
									</div>
									<div className="flex gap-2">
										<button
											onClick={handleSaveEdit}
											disabled={isSaving}
											className="rounded-md bg-green-600 px-4 py-2 text-white hover:bg-green-700 disabled:opacity-50"
										>
											Save
										</button>
										<button
											onClick={handleCancelEdit}
											disabled={isSaving}
											className="rounded-md bg-gray-200 px-4 py-2 text-gray-700 hover:bg-gray-300"
										>
											Cancel
										</button>
									</div>
								</div>
							) : (
								<div className="space-y-2 p-6 text-sm text-gray-800">
									<div className="flex justify-between">
										<span className="font-semibold">Name</span>
										<span>{specialBlock.name}</span>
									</div>
									<div className="flex justify-between">
										<span className="font-semibold">Start</span>
										<span>
											{new Date(specialBlock.startDate).toLocaleDateString('en-NZ', {
												day: '2-digit',
												month: '2-digit',
												year: 'numeric',
											})}
										</span>
									</div>
									<div className="flex justify-between">
										<span className="font-semibold">End</span>
										<span>
											{new Date(specialBlock.endDate).toLocaleDateString('en-NZ', {
												day: '2-digit',
												month: '2-digit',
												year: 'numeric',
											})}
										</span>
									</div>
									<div className="flex justify-between">
										<span className="font-semibold">Timezone</span>
										<span>{specialBlock.timezone || 'Pacific/Auckland'}</span>
									</div>
								</div>
							)}
						</div>
					</div>
				</Layout>
			</div>
		</div>
	);
};

export default Terms;
