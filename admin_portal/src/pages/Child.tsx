import { ArrowLeft, PlusCircle } from 'lucide-react';
import type React from 'react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FormInput, FormTextarea } from '../components/FormComponents';
import Layout from '../components/Layout';
import Sidebar from '../components/Sidebar';
import { adminApi } from '../services/api';
import type { ChildDetails, ChildNote } from '../types';

const ChildPage: React.FC = () => {
	const { id } = useParams<{ id: string }>();
	const navigate = useNavigate();

	const [child, setChild] = useState<ChildDetails | null>(null);
	const [notes, setNotes] = useState<ChildNote[]>([]);
	const [isLoading, setIsLoading] = useState(true);
	const [noteForm, setNoteForm] = useState({ author: '', note: '' });
	const [isSubmitting, setIsSubmitting] = useState(false);

	useEffect(() => {
		if (id) {
			loadChild(id);
		}
	}, [id]);

	const loadChild = async (childId: string) => {
		try {
			setIsLoading(true);
			const [childData, noteData] = await Promise.all([
				adminApi.getChild(childId),
				adminApi.getChildNotes(childId),
			]);
			setChild(childData);
			setNotes(noteData);
		} catch (err) {
			console.error(err);
			alert('Failed to load child details');
		} finally {
			setIsLoading(false);
		}
	};

	const handleAddNote = async () => {
		if (!id) return;
		if (!noteForm.note.trim()) {
			alert('Note cannot be empty');
			return;
		}
		try {
			setIsSubmitting(true);
			await adminApi.addChildNote(id, {
				note: noteForm.note,
				author: noteForm.author || null,
			});
			setNoteForm({ author: '', note: '' });
			await loadChild(id);
		} catch (err) {
			console.error(err);
			alert('Failed to add note');
		} finally {
			setIsSubmitting(false);
		}
	};

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

	if (!child) {
		return (
			<div className="flex min-h-screen">
				<Sidebar />
				<div className="flex-1">
					<Layout>
						<div className="py-12 text-center">
							<p className="text-gray-500">Child not found</p>
							<button
								onClick={() => navigate(-1)}
								className="mt-4 inline-block text-blue-600 hover:text-blue-700"
							>
								Go back
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
				<Layout title={child.name}>
					<button
						onClick={() => navigate(-1)}
						className="mb-4 flex items-center text-gray-600 hover:text-gray-900"
					>
						<ArrowLeft className="mr-2 h-4 w-4" /> Back
					</button>

					<div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
						<div className="rounded-lg bg-white p-6 shadow lg:col-span-1">
							<h2 className="mb-4 text-lg font-semibold text-gray-900">Profile</h2>
							<dl className="space-y-3 text-sm text-gray-800">
								<div>
									<dt className="font-medium text-gray-600">Name</dt>
									<dd>{child.name}</dd>
								</div>
								<div>
									<dt className="font-medium text-gray-600">Date of birth</dt>
									<dd>
										{new Date(child.dateOfBirth).toLocaleDateString('en-NZ', {
											day: '2-digit',
											month: '2-digit',
											year: 'numeric',
										})}
									</dd>
								</div>
								<div>
									<dt className="font-medium text-gray-600">Age</dt>
									<dd>
										{Math.floor(
											(new Date().getTime() - new Date(child.dateOfBirth).getTime()) / 3.15576e10,
										)}{' '}
										years
									</dd>
								</div>
								<div>
									<dt className="font-medium text-gray-600">Media consent</dt>
									<dd>{child.mediaConsent ? 'Yes' : 'No'}</dd>
								</div>
								<div>
									<dt className="font-medium text-gray-600">Medical info</dt>
									<dd>{child.medicalInfo || 'None'}</dd>
								</div>
								<div>
									<dt className="font-medium text-gray-600">Other info</dt>
									<dd>{child.otherInfo || 'None'}</dd>
								</div>
							</dl>
						</div>

						<div className="rounded-lg bg-white p-6 shadow lg:col-span-2">
							<div className="mb-4 flex items-center justify-between">
								<h2 className="text-lg font-semibold text-gray-900">Notes</h2>
								<span className="text-sm text-gray-500">{notes.length} note(s)</span>
							</div>
							<div className="space-y-4">
								{notes.length === 0 && <div className="text-sm text-gray-500">No notes yet.</div>}
								{notes.map((note) => (
									<div key={note.id} className="rounded-lg border border-gray-200 p-4">
										<p className="text-sm whitespace-pre-line text-gray-900">{note.note}</p>
										<p className="mt-2 text-xs text-gray-500">{note.author || 'Unknown author'}</p>
									</div>
								))}
							</div>

							<div className="mt-6 border-t pt-4">
								<h3 className="mb-2 text-base font-semibold text-gray-900">Add note</h3>
								<div className="space-y-3">
									<FormInput
										label="Author (optional)"
										value={noteForm.author}
										onChange={(e) => setNoteForm((p) => ({ ...p, author: e.target.value }))}
									/>
									<FormTextarea
										label="Note"
										rows={4}
										value={noteForm.note}
										onChange={(e) => setNoteForm((p) => ({ ...p, note: e.target.value }))}
										required
									/>
									<button
										onClick={handleAddNote}
										disabled={isSubmitting}
										className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
									>
										<PlusCircle className="mr-2 h-4 w-4" />
										{isSubmitting ? 'Saving...' : 'Add note'}
									</button>
								</div>
							</div>
						</div>
					</div>
				</Layout>
			</div>
		</div>
	);
};

export default ChildPage;
