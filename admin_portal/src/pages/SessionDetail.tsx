import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Edit,
  Download,
  Users,
  Mail,
  Megaphone,
  Copy,
  Trash2,
} from "lucide-react";
import Sidebar from "../components/Sidebar";
import Layout from "../components/Layout";
import { adminApi } from "../services/api";
import { getStatusColor } from "../lib/utils";
import { downloadBlob } from "../lib/export";
import type { Session, Signup, Occurrence, StaffListItem } from "../types";

const SessionDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<Session | null>(null);
  const [signups, setSignups] = useState<Signup[]>([]);
  const [occurrences, setOccurrences] = useState<Occurrence[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    "signups" | "occurrences" | "staff" | "comms"
  >("signups");
  const [statusFilter, setStatusFilter] = useState<string>("");

  const [sessionStaff, setSessionStaff] = useState<StaffListItem[]>([]);
  const [allStaff, setAllStaff] = useState<StaffListItem[]>([]);
  const [selectedStaffIds, setSelectedStaffIds] = useState<string[]>([]);
  const [isSavingStaff, setIsSavingStaff] = useState(false);

  const [bulkSubject, setBulkSubject] = useState("");
  const [bulkMessage, setBulkMessage] = useState("");
  const [notifyTitle, setNotifyTitle] = useState("");
  const [notifyMessage, setNotifyMessage] = useState("");
  const [notifyDate, setNotifyDate] = useState("");
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
      console.error("Failed to load session data:", error);
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
      console.error("Failed to load staff data:", error);
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
      console.error("Failed to update signup status:", error);
      alert("Failed to update signup status");
    }
  };

  const handleExportSignups = async () => {
    if (!id || !session) return;
    try {
      const blob = await adminApi.exportSignupsCSV(
        id,
        statusFilter || undefined,
      );
      downloadBlob(blob, `signups-${session.name}.csv`);
    } catch (error) {
      console.error("Failed to export signups:", error);
      alert("Failed to export signups");
    }
  };

  const handleGenerateOccurrences = async () => {
    if (!id) return;
    if (
      !confirm(
        "This will generate occurrences based on the session schedule. Continue?",
      )
    )
      return;

    try {
      const result = await adminApi.generateOccurrences(id);
      alert(`Generated ${result.created} occurrences`);
      const updatedOccurrences = await adminApi.getSessionOccurrences(id);
      setOccurrences(updatedOccurrences);
    } catch (error) {
      console.error("Failed to generate occurrences:", error);
      alert("Failed to generate occurrences");
    }
  };

  const handleSaveStaff = async () => {
    if (!id) return;
    try {
      setIsSavingStaff(true);
      await adminApi.assignSessionStaff(id, selectedStaffIds);
      await loadStaffData(id);
    } catch (error) {
      console.error("Failed to update staff assignments:", error);
      alert("Failed to update staff assignments");
    } finally {
      setIsSavingStaff(false);
    }
  };

  const handleCancelOccurrence = async (occurrenceId: string) => {
    const reason = prompt("Enter cancellation reason (optional):");
    if (reason === null) return;

    try {
      await adminApi.cancelOccurrence(occurrenceId, reason || undefined);
      if (id) {
        const updated = await adminApi.getSessionOccurrences(id);
        setOccurrences(updated);
        alert("Occurrence cancelled");
      }
    } catch (error) {
      console.error("Failed to cancel occurrence:", error);
      alert("Failed to cancel occurrence");
    }
  };

  const handleReinstateOccurrence = async (occurrenceId: string) => {
    try {
      await adminApi.reinstateOccurrence(occurrenceId);
      if (id) {
        const updated = await adminApi.getSessionOccurrences(id);
        setOccurrences(updated);
        alert("Occurrence reinstated");
      }
    } catch (error) {
      console.error("Failed to reinstate occurrence:", error);
      alert("Failed to reinstate occurrence");
    }
  };

  const handleBulkEmail = async () => {
    if (!id) return;
    if (!bulkSubject.trim() || !bulkMessage.trim()) {
      alert("Subject and message are required");
      return;
    }
    try {
      setCommsStatus("Sending bulk email...");
      const res = await adminApi.bulkEmailSession(id, {
        subject: bulkSubject,
        message: bulkMessage,
      });
      setCommsStatus(`Enqueued ${res.enqueued} emails`);
      setBulkSubject("");
      setBulkMessage("");
    } catch (error) {
      console.error("Failed to send bulk email:", error);
      setCommsStatus("Failed to send bulk email");
    }
  };

  const handleNotify = async () => {
    if (!id) return;
    if (!notifyTitle.trim()) {
      alert("Update title is required");
      return;
    }
    try {
      setCommsStatus("Sending notification...");
      const res = await adminApi.notifySession(id, {
        updateTitle: notifyTitle,
        updateMessage: notifyMessage || null,
        affectedDate: notifyDate || null,
      });
      setCommsStatus(`Enqueued ${res.enqueued} notifications`);
      setNotifyTitle("");
      setNotifyMessage("");
      setNotifyDate("");
    } catch (error) {
      console.error("Failed to send notification:", error);
      setCommsStatus("Failed to send notification");
    }
  };

  const handleDeleteSession = async () => {
    if (!id) return;
    if (
      !confirm(
        "Are you sure you want to delete this session? This cannot be undone.",
      )
    )
      return;

    try {
      await adminApi.deleteSession(id);
      alert("Session deleted successfully");
      navigate("/sessions");
    } catch (error) {
      console.error("Failed to delete session:", error);
      alert("Failed to delete session");
    }
  };

  const handleDuplicateSession = async () => {
    if (!id) return;
    if (!confirm("This will create a copy of this session. Continue?")) return;

    try {
      const duplicated = await adminApi.duplicateSession(id);
      alert("Session duplicated successfully");
      navigate(`/sessions/${duplicated.id}`);
    } catch (error) {
      console.error("Failed to duplicate session:", error);
      alert("Failed to duplicate session");
    }
  };

  const filteredSignups = statusFilter
    ? signups.filter((s) => s.status === statusFilter)
    : signups;

  if (isLoading) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1 flex justify-center items-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
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
            <div className="text-center py-12">
              <p className="text-gray-500">Session not found</p>
              <button
                onClick={() => navigate("/sessions")}
                className="text-blue-600 hover:text-blue-700 mt-4 inline-block"
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
              onClick={() => navigate("/sessions")}
              className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Sessions
            </button>

            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  {session.name}
                </h1>
                {session.description && (
                  <p className="text-gray-600 mt-2">{session.description}</p>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleDuplicateSession}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Duplicate
                </button>
                <button
                  onClick={() => navigate(`/sessions/${id}/edit`)}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                >
                  <Edit className="w-4 h-4 mr-2" />
                  Edit
                </button>
                <button
                  onClick={handleDeleteSession}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-red-600 hover:bg-red-700"
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete
                </button>
              </div>
            </div>
          </div>

          {/* Session Info */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="flex items-start">
                <div className="text-gray-400 mr-3 mt-0.5">📅</div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Schedule</p>
                  <p className="mt-1 text-sm text-gray-900">
                    {session.dayOfWeek} {session.startTime} - {session.endTime}
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="text-gray-400 mr-3 mt-0.5">📍</div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Location</p>
                  <p className="mt-1 text-sm text-gray-900">
                    {session.location?.name || "No location set"}
                  </p>
                </div>
              </div>

              <div className="flex items-start">
                <div className="text-gray-400 mr-3 mt-0.5">👥</div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Capacity</p>
                  <p className="mt-1 text-sm text-gray-900">
                    {signups.filter((s) => s.status === "confirmed").length} /{" "}
                    {session.capacity || "Unlimited"}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200 mb-6">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab("signups")}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "signups"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Signups ({signups.length})
              </button>
              <button
                onClick={() => setActiveTab("occurrences")}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "occurrences"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Occurrences ({occurrences.length})
              </button>
              <button
                onClick={() => setActiveTab("staff")}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "staff"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Staff ({sessionStaff.length})
              </button>
              <button
                onClick={() => setActiveTab("comms")}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === "comms"
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                }`}
              >
                Communications
              </button>
            </nav>
          </div>

          {/* Signups Tab */}
          {activeTab === "signups" && (
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Signups
                  </h2>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm px-3 py-1"
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
                  className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
                >
                  <Download className="w-4 h-4 mr-2" />
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
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredSignups.map((signup) => (
                      <tr key={signup.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          <button
                            onClick={() =>
                              navigate(`/children/${signup.childId}`)
                            }
                            className="text-blue-600 hover:text-blue-800"
                          >
                            {signup.studentName}
                          </button>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          \n {signup.guardianName}\n{" "}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {signup.email}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(
                              signup.status,
                            )}`}
                          >
                            {signup.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <select
                            value={signup.status}
                            onChange={(e) =>
                              handleStatusChange(signup.id, e.target.value)
                            }
                            className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 text-sm px-2 py-1"
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
                  <div className="text-center py-12 text-gray-500">
                    No signups matching filter
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Occurrences Tab */}
          {activeTab === "occurrences" && (
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <h2 className="text-lg font-semibold text-gray-900">
                  Occurrences
                </h2>
                <button
                  onClick={handleGenerateOccurrences}
                  className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
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
                  <tbody className="bg-white divide-y divide-gray-200">
                    {occurrences.map((occurrence) => (
                      <tr key={occurrence.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(occurrence.startsAt).toLocaleDateString(
                            "en-NZ",
                            {
                              day: "2-digit",
                              month: "2-digit",
                              year: "numeric",
                            },
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {occurrence.cancelled ? (
                            <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">
                              Cancelled
                            </span>
                          ) : (
                            <span className="px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                              Active
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={() =>
                              navigate(`/attendance/${occurrence.id}`)
                            }
                            className="text-blue-600 hover:text-blue-900 mr-4"
                          >
                            Attendance
                          </button>
                          {occurrence.cancelled ? (
                            <button
                              onClick={() =>
                                handleReinstateOccurrence(occurrence.id)
                              }
                              className="text-green-600 hover:text-green-900"
                            >
                              Reinstate
                            </button>
                          ) : (
                            <button
                              onClick={() =>
                                handleCancelOccurrence(occurrence.id)
                              }
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
                  <div className="text-center py-12 text-gray-500">
                    No occurrences yet. Generate occurrences to get started.
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Staff Tab */}
          {activeTab === "staff" && (
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-gray-600" />
                  <h2 className="text-lg font-semibold text-gray-900">
                    Staff assignments
                  </h2>
                </div>
                <button
                  onClick={handleSaveStaff}
                  disabled={isSavingStaff}
                  className="inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  {isSavingStaff ? "Saving..." : "Save assignments"}
                </button>
              </div>
              <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">
                    All staff
                  </h3>
                  <div className="space-y-2 max-h-80 overflow-y-auto border border-gray-200 rounded-lg p-3">
                    {allStaff.length === 0 && (
                      <p className="text-sm text-gray-500">No staff found</p>
                    )}
                    {allStaff.map((staffMember) => {
                      const checked = selectedStaffIds.includes(staffMember.id);
                      return (
                        <label
                          key={staffMember.id}
                          className="flex items-center justify-between rounded-md px-3 py-2 hover:bg-gray-50 cursor-pointer"
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
                                    : prev.filter(
                                        (id) => id !== staffMember.id,
                                      ),
                                );
                              }}
                              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
                            />
                            <div>
                              <p className="text-sm font-medium text-gray-900">
                                {staffMember.name}
                              </p>
                              <p className="text-xs text-gray-500">
                                {staffMember.email}
                              </p>
                            </div>
                          </div>
                          <span
                            className={`text-xs font-semibold px-2 py-1 rounded-full ${
                              staffMember.active
                                ? "bg-green-100 text-green-800"
                                : "bg-gray-200 text-gray-700"
                            }`}
                          >
                            {staffMember.active ? "Active" : "Inactive"}
                          </span>
                        </label>
                      );
                    })}
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-gray-700 mb-3">
                    Assigned to this session
                  </h3>
                  <div className="space-y-3">
                    {sessionStaff.length === 0 && (
                      <p className="text-sm text-gray-500">No staff assigned</p>
                    )}
                    {sessionStaff.map((staffMember) => (
                      <div
                        key={staffMember.id}
                        className="flex items-center justify-between border border-gray-200 rounded-lg px-4 py-3"
                      >
                        <div>
                          <p className="text-sm font-semibold text-gray-900">
                            {staffMember.name}
                          </p>
                          <p className="text-xs text-gray-500">
                            {staffMember.email}
                          </p>
                        </div>
                        <button
                          onClick={() => {
                            setSelectedStaffIds((prev) =>
                              prev.filter((id) => id !== staffMember.id),
                            );
                            setSessionStaff((prev) =>
                              prev.filter((s) => s.id !== staffMember.id),
                            );
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
          {activeTab === "comms" && (
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">
                  Communications
                </h2>
                {commsStatus && (
                  <p className="text-sm text-gray-500 mt-1">{commsStatus}</p>
                )}
              </div>
              <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Mail className="w-4 h-4 text-gray-600" />
                    <h3 className="text-base font-semibold text-gray-900">
                      Bulk email
                    </h3>
                  </div>
                  <div className="space-y-3">
                    <input
                      type="text"
                      value={bulkSubject}
                      onChange={(e) => setBulkSubject(e.target.value)}
                      placeholder="Subject"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                    <textarea
                      rows={6}
                      value={bulkMessage}
                      onChange={(e) => setBulkMessage(e.target.value)}
                      placeholder="Message to caregivers"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                    <button
                      onClick={handleBulkEmail}
                      className="inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
                    >
                      Send bulk email
                    </button>
                  </div>
                </div>

                <div className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Megaphone className="w-4 h-4 text-gray-600" />
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
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                    <textarea
                      rows={4}
                      value={notifyMessage}
                      onChange={(e) => setNotifyMessage(e.target.value)}
                      placeholder="Optional message"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Affected date (optional)
                      </label>
                      <input
                        type="date"
                        value={notifyDate}
                        onChange={(e) => setNotifyDate(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                    <button
                      onClick={handleNotify}
                      className="inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
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
