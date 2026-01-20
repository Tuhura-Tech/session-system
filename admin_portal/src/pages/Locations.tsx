import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Plus } from "lucide-react";
import Sidebar from "../components/Sidebar";
import Layout from "../components/Layout";
import { adminApi } from "../services/api";
import type { SessionLocation } from "../types";

const Locations: React.FC = () => {
  const [locations, setLocations] = useState<SessionLocation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    address: "",
    region: "",
    lat: 0,
    lng: 0,
    contactName: "",
    contactEmail: "",
    contactPhone: "",
    instructions: "",
    internalNotes: "",
  });

  useEffect(() => {
    loadLocations();
  }, []);

  const loadLocations = async () => {
    try {
      setIsLoading(true);
      const data = await adminApi.getLocations();
      setLocations(data);
    } catch (error) {
      console.error("Failed to load locations:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (editingId) {
        await adminApi.updateLocation(editingId, formData);
      } else {
        await adminApi.createLocation(formData);
      }

      setShowForm(false);
      setEditingId(null);
      setFormData({
        name: "",
        address: "",
        region: "",
        lat: 0,
        lng: 0,
        contactName: "",
        contactEmail: "",
        contactPhone: "",
        instructions: "",
        internalNotes: "",
      });
      loadLocations();
    } catch (error) {
      console.error("Failed to save location:", error);
      alert("Failed to save location");
    }
  };

  const handleEdit = (location: SessionLocation) => {
    setFormData({
      name: location.name,
      address: location.address || "",
      region: location.region || "",
      lat: location.lat || 0,
      lng: location.lng || 0,
      contactName: location.contactName || "",
      contactEmail: location.contactEmail || "",
      contactPhone: location.contactPhone || "",
      instructions: location.instructions || "",
      internalNotes: location.internalNotes || "",
    });
    setEditingId(location.id);
    setShowForm(true);
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingId(null);
    setFormData({
      name: "",
      address: "",
      region: "",
      lat: 0,
      lng: 0,
      contactName: "",
      contactEmail: "",
      contactPhone: "",
      instructions: "",
      internalNotes: "",
    });
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <div className="flex-1">
        <Layout
          title="Locations"
          actions={
            !showForm && (
              <button
                onClick={() => setShowForm(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="w-4 h-4 mr-2" />
                New Location
              </button>
            )
          }
        >
          {showForm && (
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                {editingId ? "Edit Location" : "Create New Location"}
              </h2>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.name}
                      onChange={(e) =>
                        setFormData({ ...formData, name: e.target.value })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Region
                    </label>
                    <input
                      type="text"
                      value={formData.region}
                      onChange={(e) =>
                        setFormData({ ...formData, region: e.target.value })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Address
                    </label>
                    <input
                      type="text"
                      value={formData.address}
                      onChange={(e) =>
                        setFormData({ ...formData, address: e.target.value })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Latitude *
                    </label>
                    <input
                      type="number"
                      step="0.000001"
                      required
                      value={formData.lat}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          lat: parseFloat(e.target.value),
                        })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Longitude *
                    </label>
                    <input
                      type="number"
                      step="0.000001"
                      required
                      value={formData.lng}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          lng: parseFloat(e.target.value),
                        })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Contact Name
                    </label>
                    <input
                      type="text"
                      value={formData.contactName}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          contactName: e.target.value,
                        })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Contact Email
                    </label>
                    <input
                      type="email"
                      value={formData.contactEmail}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          contactEmail: e.target.value,
                        })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Contact Phone
                    </label>
                    <input
                      type="tel"
                      value={formData.contactPhone}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          contactPhone: e.target.value,
                        })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Instructions
                    </label>
                    <textarea
                      rows={3}
                      value={formData.instructions}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          instructions: e.target.value,
                        })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Internal Notes
                    </label>
                    <textarea
                      rows={3}
                      value={formData.internalNotes}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          internalNotes: e.target.value,
                        })
                      }
                      className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-4">
                  <button
                    type="button"
                    onClick={handleCancel}
                    className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                  >
                    {editingId ? "Update" : "Create"} Location
                  </button>
                </div>
              </form>
            </div>
          )}

          <div className="bg-white rounded-lg shadow overflow-hidden">
            {isLoading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Region
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Address
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Contact
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {locations.map((location) => (
                      <tr key={location.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {location.name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {location.region || "-"}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {location.address || "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {location.contactName || "-"}
                          {location.contactEmail && (
                            <div className="text-xs text-gray-400">
                              {location.contactEmail}
                            </div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() =>
                              navigate(`/locations/${location.id}`)
                            }
                            className="text-blue-600 hover:text-blue-900 mr-4"
                          >
                            View
                          </button>
                          <button
                            onClick={() => handleEdit(location)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            Edit
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {locations.length === 0 && (
                  <div className="text-center py-12 text-gray-500">
                    No locations yet
                  </div>
                )}
              </div>
            )}
          </div>
        </Layout>
      </div>
    </div>
  );
};

export default Locations;
