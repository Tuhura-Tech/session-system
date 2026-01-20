import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Sidebar from "../components/Sidebar";
import Layout from "../components/Layout";
import { adminApi } from "../services/api";
import type { SessionLocation } from "../types";

const CreateSession: React.FC = () => {
  const navigate = useNavigate();
  const [locations, setLocations] = useState<SessionLocation[]>([]);
  const [blocks, setBlocks] = useState<any[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    year: new Date().getFullYear(),
    sessionLocationId: "",
    ageLower: "",
    ageUpper: "",
    dayOfWeek: "",
    startTime: "",
    endTime: "",
    capacity: "16",
    waitlist: false,
    whatToBring: "",
    prerequisites: "",
    photoAlbumUrl: "",
    internalNotes: "",
    sessionType: "term",
    blockIds: [] as string[],
  });

  useEffect(() => {
    loadFormData();
  }, []);

  const loadFormData = async () => {
    try {
      const [locationsData, blocksData] = await Promise.all([
        adminApi.getLocations(),
        adminApi.getBlocks(),
      ]);
      setLocations(locationsData);
      setBlocks(blocksData);
    } catch (error) {
      console.error("Failed to load form data:", error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      setIsSubmitting(true);
      const sessionData = {
        name: formData.name,
        year: formData.year,
        sessionLocationId: formData.sessionLocationId || null,
        ageLower: formData.ageLower ? parseInt(formData.ageLower) : null,
        ageUpper: formData.ageUpper ? parseInt(formData.ageUpper) : null,
        dayOfWeek: formData.dayOfWeek ? parseInt(formData.dayOfWeek) : null,
        startTime: formData.startTime || null,
        endTime: formData.endTime || null,
        capacity: formData.capacity ? parseInt(formData.capacity) : null,
        waitlist: formData.waitlist,
        whatToBring: formData.whatToBring || null,
        prerequisites: formData.prerequisites || null,
        photoAlbumUrl: formData.photoAlbumUrl || null,
        internalNotes: formData.internalNotes || null,
        sessionType: formData.sessionType,
        blockIds: formData.blockIds,
      };

      const created = await adminApi.createSession(sessionData);
      navigate(`/sessions/${created.id}`);
    } catch (error) {
      console.error("Failed to create session:", error);
      alert("Failed to create session");
    } finally {
      setIsSubmitting(false);
    }
  };

  const daysOfWeek = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <div className="flex-1">
        <Layout>
          <button
            onClick={() => navigate("/sessions")}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Sessions
          </button>

          <div className="bg-white rounded-lg shadow p-6">
            <h1 className="text-2xl font-bold text-gray-900 mb-6">
              Create New Session
            </h1>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Session Name *
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
                    Year *
                  </label>
                  <input
                    type="number"
                    required
                    value={formData.year}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        year: parseInt(e.target.value),
                      })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Session Type *
                  </label>
                  <select
                    required
                    value={formData.sessionType}
                    onChange={(e) =>
                      setFormData({ ...formData, sessionType: e.target.value })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="term">Term (Recurring)</option>
                    <option value="special">Special (One-off)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Location
                  </label>
                  <select
                    value={formData.sessionLocationId}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        sessionLocationId: e.target.value,
                      })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="">Select a location</option>
                    {locations.map((loc) => (
                      <option key={loc.id} value={loc.id}>
                        {loc.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Day of Week
                  </label>
                  <select
                    value={formData.dayOfWeek}
                    onChange={(e) =>
                      setFormData({ ...formData, dayOfWeek: e.target.value })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="">Select a day</option>
                    {daysOfWeek.map((day, index) => (
                      <option key={day} value={index}>
                        {day}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Start Time
                  </label>
                  <input
                    type="time"
                    value={formData.startTime}
                    onChange={(e) =>
                      setFormData({ ...formData, startTime: e.target.value })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    End Time
                  </label>
                  <input
                    type="time"
                    value={formData.endTime}
                    onChange={(e) =>
                      setFormData({ ...formData, endTime: e.target.value })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Age Lower
                  </label>
                  <select
                    value={formData.ageLower}
                    onChange={(e) =>
                      setFormData({ ...formData, ageLower: e.target.value })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="">No minimum</option>
                    {Array.from({ length: 21 }, (_, i) => i + 5).map((age) => (
                      <option key={age} value={age}>
                        {age}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Age Upper
                  </label>
                  <select
                    value={formData.ageUpper}
                    onChange={(e) =>
                      setFormData({ ...formData, ageUpper: e.target.value })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="">No maximum</option>
                    {Array.from({ length: 21 }, (_, i) => i + 5).map((age) => (
                      <option key={age} value={age}>
                        {age}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Capacity
                  </label>
                  <select
                    value={formData.capacity}
                    onChange={(e) =>
                      setFormData({ ...formData, capacity: e.target.value })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="">Select capacity</option>
                    {Array.from({ length: 46 }, (_, i) => i + 5).map((cap) => (
                      <option key={cap} value={cap}>
                        {cap}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.waitlist}
                    onChange={(e) =>
                      setFormData({ ...formData, waitlist: e.target.checked })
                    }
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label className="ml-2 block text-sm text-gray-900">
                    Enable waitlist
                  </label>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Associated Blocks (for term sessions)
                  </label>
                  <div className="mt-2 space-y-2">
                    {blocks.map((block) => (
                      <label key={block.id} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.blockIds.includes(block.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData({
                                ...formData,
                                blockIds: [...formData.blockIds, block.id],
                              });
                            } else {
                              setFormData({
                                ...formData,
                                blockIds: formData.blockIds.filter(
                                  (id) => id !== block.id,
                                ),
                              });
                            }
                          }}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-900">
                          {block.name} ({block.blockType}) - {block.year}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">
                    What to Bring
                  </label>
                  <textarea
                    rows={3}
                    value={formData.whatToBring}
                    onChange={(e) =>
                      setFormData({ ...formData, whatToBring: e.target.value })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Prerequisites
                  </label>
                  <textarea
                    rows={3}
                    value={formData.prerequisites}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        prerequisites: e.target.value,
                      })
                    }
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-4">
                <button
                  type="button"
                  onClick={() => navigate("/sessions")}
                  className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  {isSubmitting ? "Creating..." : "Create Session"}
                </button>
              </div>
            </form>
          </div>
        </Layout>
      </div>
    </div>
  );
};

export default CreateSession;
