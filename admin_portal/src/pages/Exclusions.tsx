import React, { useState, useEffect } from "react";
import { Plus, Edit2, Trash2 } from "lucide-react";
import Sidebar from "../components/Sidebar";
import Layout from "../components/Layout";
import {
  ErrorMessage,
  LoadingSpinner,
  SuccessMessage,
} from "../components/Alert";
import Modal from "../components/Modal";
import {
  FormInput,
  FormTextarea,
} from "../components/FormComponents";
import { adminApi } from "../services/api";

interface ExclusionDate {
  id: string;
  year: number;
  date: string;
  reason: string | null;
}

const Exclusions: React.FC = () => {
  const [exclusions, setExclusions] = useState<ExclusionDate[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedYear, setSelectedYear] = useState<number>(
    new Date().getFullYear(),
  );
  const [showModal, setShowModal] = useState(false);
  const [editingExclusion, setEditingExclusion] =
    useState<ExclusionDate | null>(null);

  const [formData, setFormData] = useState({
    year: new Date().getFullYear(),
    date: "",
    reason: "",
  });

  useEffect(() => {
    loadExclusions();
  }, [selectedYear]);

  const loadExclusions = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await adminApi.getExclusions(selectedYear);
      setExclusions(data);
    } catch (err) {
      setError("Failed to load exclusion dates");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingExclusion(null);
    setFormData({
      year: selectedYear,
      date: "",
      reason: "",
    });
    setShowModal(true);
  };

  const handleEdit = (exclusion: ExclusionDate) => {
    setEditingExclusion(exclusion);
    setFormData({
      year: exclusion.year,
      date: exclusion.date,
      reason: exclusion.reason || "",
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      if (editingExclusion) {
        await adminApi.updateExclusion(editingExclusion.id, {
          reason: formData.reason || null,
        });
        setSuccess("Exclusion updated successfully");
      } else {
        await adminApi.createExclusion({
          date: formData.date,
          reason: formData.reason || null,
        });
        setSuccess("Exclusion created successfully");
      }

      setShowModal(false);
      loadExclusions();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save exclusion");
    }
  };

  const handleDelete = async (exclusion: ExclusionDate) => {
    if (
      !confirm(
        `Are you sure you want to delete the exclusion for ${new Date(exclusion.date).toLocaleDateString("en-NZ", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}?`,
      )
    ) {
      return;
    }

    try {
      setError(null);
      setSuccess(null);
      await adminApi.deleteExclusion(exclusion.id);
      setSuccess("Exclusion deleted successfully");
      loadExclusions();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to delete exclusion");
    }
  };

  const years = Array.from(
    { length: 5 },
    (_, i) => new Date().getFullYear() - 1 + i,
  );

  // Group exclusions by month
  const groupedByMonth = exclusions.reduce(
    (acc, exclusion) => {
      const month = new Date(exclusion.date).toLocaleDateString("en-NZ", {
        month: "long",
      });
      if (!acc[month]) acc[month] = [];
      acc[month].push(exclusion);
      return acc;
    },
    {} as Record<string, ExclusionDate[]>,
  );

  if (isLoading) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex justify-center items-center">
          <LoadingSpinner />
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <div className="flex-1">
        <Layout
          title="Exclusion Dates (Holidays & Closures)"
          actions={
            <button
              onClick={handleCreate}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Exclusion
            </button>
          }
        >
          {error && <ErrorMessage error={error} />}
          {success && (
            <SuccessMessage
              message={success}
              onClose={() => setSuccess(null)}
            />
          )}

          {/* Year Filter */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Filter by Year
            </label>
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

          {/* Exclusions by Month */}
          <div className="space-y-6">
            {Object.entries(groupedByMonth).length === 0 ? (
              <div className="bg-white rounded-lg shadow p-12 text-center text-gray-500">
                No exclusion dates for {selectedYear}. Add holidays or closure
                dates to exclude them from session scheduling.
              </div>
            ) : (
              Object.entries(groupedByMonth)
                .sort(([a], [b]) => {
                  const months = [
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December",
                  ];
                  return months.indexOf(a) - months.indexOf(b);
                })
                .map(([month, dates]) => (
                  <div
                    key={month}
                    className="bg-white rounded-lg shadow overflow-hidden"
                  >
                    <div className="bg-gray-50 px-6 py-3 border-b border-gray-200">
                      <h3 className="text-lg font-semibold text-gray-900">
                        {month}
                      </h3>
                    </div>
                    <div className="divide-y divide-gray-200">
                      {dates
                        .sort(
                          (a, b) =>
                            new Date(a.date).getTime() -
                            new Date(b.date).getTime(),
                        )
                        .map((exclusion) => (
                          <div
                            key={exclusion.id}
                            className="px-6 py-4 flex justify-between items-start"
                          >
                            <div className="flex-1">
                              <div className="text-sm font-medium text-gray-900">
                                {new Date(exclusion.date).toLocaleDateString(
                                  "en-NZ",
                                  {
                                    weekday: "long",
                                    day: "numeric",
                                    month: "long",
                                    year: "numeric",
                                  },
                                )}
                              </div>
                              {exclusion.reason && (
                                <div className="text-sm text-gray-500 mt-1">
                                  {exclusion.reason}
                                </div>
                              )}
                            </div>
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleEdit(exclusion)}
                                className="text-blue-600 hover:text-blue-900"
                                title="Edit exclusion"
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDelete(exclusion)}
                                className="text-red-600 hover:text-red-900"
                                title="Delete exclusion"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))}
                    </div>
                  </div>
                ))
            )}
          </div>
        </Layout>
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <Modal
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          title={
            editingExclusion ? "Edit Exclusion Date" : "Add Exclusion Date"
          }
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            {!editingExclusion && (
              <FormInput
                label="Date"
                type="date"
                value={formData.date}
                onChange={(e) =>
                  setFormData({ ...formData, date: e.target.value })
                }
                required
              />
            )}

            {editingExclusion && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Date
                </label>
                <div className="text-sm text-gray-900">
                  {new Date(editingExclusion.date).toLocaleDateString("en-NZ", {
                    weekday: "long",
                    day: "numeric",
                    month: "long",
                    year: "numeric",
                  })}
                </div>
              </div>
            )}

            <FormTextarea
              label="Reason (optional)"
              value={formData.reason}
              onChange={(e) =>
                setFormData({ ...formData, reason: e.target.value })
              }
              placeholder="e.g., Public Holiday - Waitangi Day"
              rows={3}
            />

            <div className="flex justify-end gap-3 mt-6">
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                {editingExclusion ? "Update" : "Add"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};

export default Exclusions;
