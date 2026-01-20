import React, { useState, useEffect } from "react";
import { Plus, Edit2 } from "lucide-react";
import Sidebar from "../components/Sidebar";
import Layout from "../components/Layout";
import {
  ErrorMessage,
  LoadingSpinner,
  SuccessMessage,
} from "../components/Alert";
import Modal from "../components/Modal";
import { FormInput, FormSelect } from "../components/FormComponents";
import { adminApi } from "../services/api";

interface Block {
  id: string;
  year: number;
  blockType: "term_1" | "term_2" | "term_3" | "term_4" | "special";
  name: string;
  startDate: string;
  endDate: string;
  timezone?: string;
}

const Blocks: React.FC = () => {
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [filteredBlocks, setFilteredBlocks] = useState<Block[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedYear, setSelectedYear] = useState<number>(
    new Date().getFullYear(),
  );
  const [showModal, setShowModal] = useState(false);
  const [editingBlock, setEditingBlock] = useState<Block | null>(null);

  const [formData, setFormData] = useState({
    year: new Date().getFullYear(),
    blockType: "term_1" as Block["blockType"],
    name: "",
    startDate: "",
    endDate: "",
    timezone: "Pacific/Auckland",
  });

  useEffect(() => {
    loadBlocks();
  }, [selectedYear]);

  useEffect(() => {
    const filtered = blocks.filter((block) => block.year === selectedYear);
    setFilteredBlocks(filtered);
  }, [blocks, selectedYear]);

  const loadBlocks = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await adminApi.getBlocks(selectedYear);
      setBlocks(data);
    } catch (err) {
      setError("Failed to load blocks");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingBlock(null);
    setFormData({
      year: selectedYear,
      blockType: "term_1",
      name: "",
      startDate: "",
      endDate: "",
      timezone: "Pacific/Auckland",
    });
    setShowModal(true);
  };

  const handleEdit = (block: Block) => {
    setEditingBlock(block);
    setFormData({
      year: block.year,
      blockType: block.blockType,
      name: block.name,
      startDate: block.startDate,
      endDate: block.endDate,
      timezone: block.timezone || "Pacific/Auckland",
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    try {
      if (editingBlock) {
        await adminApi.updateBlock(editingBlock.id, formData);
        setSuccess("Block updated successfully");
      } else {
        await adminApi.createBlock(formData);
        setSuccess("Block created successfully");
      }

      setShowModal(false);
      loadBlocks();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save block");
    }
  };

  const blockTypeLabels = {
    term_1: "Term 1",
    term_2: "Term 2",
    term_3: "Term 3",
    term_4: "Term 4",
    special: "Special",
  };

  const years = Array.from(
    { length: 5 },
    (_, i) => new Date().getFullYear() - 1 + i,
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
          title="Session Blocks"
          actions={
            <button
              onClick={handleCreate}
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Block
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

          {/* Blocks Table */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Start Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    End Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredBlocks.map((block) => (
                  <tr key={block.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {blockTypeLabels[block.blockType]}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {block.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(block.startDate).toLocaleDateString("en-NZ", {
                        day: "2-digit",
                        month: "2-digit",
                        year: "numeric",
                      })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(block.endDate).toLocaleDateString("en-NZ", {
                        day: "2-digit",
                        month: "2-digit",
                        year: "numeric",
                      })}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <button
                        onClick={() => handleEdit(block)}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {filteredBlocks.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                No blocks found for {selectedYear}. Create one to get started.
              </div>
            )}
          </div>
        </Layout>
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <Modal
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          title={editingBlock ? "Edit Block" : "Create Block"}
        >
          <form onSubmit={handleSubmit} className="space-y-4">
            <FormSelect
              label="Year"
              value={formData.year}
              onChange={(e) =>
                setFormData({ ...formData, year: Number(e.target.value) })
              }
              required
            >
              {years.map((year) => (
                <option key={year} value={year}>
                  {year}
                </option>
              ))}
            </FormSelect>

            <FormSelect
              label="Block Type"
              value={formData.blockType}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  blockType: e.target.value as Block["blockType"],
                })
              }
              required
            >
              <option value="term_1">Term 1</option>
              <option value="term_2">Term 2</option>
              <option value="term_3">Term 3</option>
              <option value="term_4">Term 4</option>
              <option value="special">Special</option>
            </FormSelect>

            <FormInput
              label="Name"
              type="text"
              value={formData.name}
              onChange={(e) =>
                setFormData({ ...formData, name: e.target.value })
              }
              required
              placeholder="e.g., Term 1 2024"
            />

            <FormInput
              label="Start Date"
              type="date"
              value={formData.startDate}
              onChange={(e) =>
                setFormData({ ...formData, startDate: e.target.value })
              }
              required
            />

            <FormInput
              label="End Date"
              type="date"
              value={formData.endDate}
              onChange={(e) =>
                setFormData({ ...formData, endDate: e.target.value })
              }
              required
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
                {editingBlock ? "Update" : "Create"}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};

export default Blocks;
