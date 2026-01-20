import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Save } from "lucide-react";
import Sidebar from "../components/Sidebar";
import Layout from "../components/Layout";
import { adminApi } from "../services/api";
import type { AttendanceRoll, AttendanceUpsert, Session } from "../types";

const AttendanceRoll: React.FC = () => {
  const { occurrenceId } = useParams<{ occurrenceId: string }>();
  const navigate = useNavigate();
  const [roll, setRoll] = useState<AttendanceRoll | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [changes, setChanges] = useState<Map<string, AttendanceUpsert>>(
    new Map(),
  );

  useEffect(() => {
    if (occurrenceId) {
      loadRoll(occurrenceId);
    }
  }, [occurrenceId]);

  const loadRoll = async (id: string) => {
    try {
      setIsLoading(true);
      const data = await adminApi.getAttendanceRoll(id);
      setRoll(data);

      // Load session data to get full session details
      if (data.occurrence.sessionId) {
        const sessionData = await adminApi.getSession(
          data.occurrence.sessionId,
        );
        setSession(sessionData);
      }
    } catch (error) {
      console.error("Failed to load attendance roll:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStatusChange = (
    signupId: string,
    status: "present" | "absent_known" | "absent_unknown",
  ) => {
    const newChanges = new Map(changes);
    newChanges.set(signupId, { signupId, status });
    setChanges(newChanges);
  };

  const handleSaveAll = async () => {
    if (!occurrenceId || changes.size === 0) return;

    try {
      setIsSaving(true);

      for (const [, attendance] of changes) {
        await adminApi.markAttendance(occurrenceId, attendance);
      }

      setChanges(new Map());
      await loadRoll(occurrenceId);
      alert("Attendance saved successfully");
    } catch (error) {
      console.error("Failed to save attendance:", error);
      alert("Failed to save attendance");
    } finally {
      setIsSaving(false);
    }
  };

  const getStatusForStudent = (
    signupId: string,
    currentStatus: string | null,
  ) => {
    const change = changes.get(signupId);
    return change ? change.status : currentStatus || "";
  };

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

  if (!roll) {
    return (
      <div className="flex min-h-screen">
        <Sidebar />
        <div className="flex-1">
          <Layout title="Occurrence Not Found">
            <p className="text-gray-500">Occurrence not found</p>
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
          <button
            onClick={() => navigate(`/sessions/${roll.occurrence.sessionId}`)}
            className="flex items-center text-gray-600 hover:text-gray-900 mb-6"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Session
          </button>

          <div className="bg-white rounded-lg shadow overflow-hidden">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex justify-between items-start">
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">
                    {session?.name}
                  </h1>
                  <p className="text-sm text-gray-600 mt-1">
                    {new Date(roll.occurrence.startsAt).toLocaleDateString(
                      "en-NZ",
                      { day: "2-digit", month: "2-digit", year: "numeric" },
                    )}{" "}
                    • {session?.dayOfWeek} {session?.startTime} -{" "}
                    {session?.endTime}
                  </p>
                  {session?.location && (
                    <p className="text-sm text-gray-600">
                      {session.location.name}
                    </p>
                  )}
                  {roll.occurrence.cancelled && (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 mt-2">
                      Cancelled
                    </span>
                  )}
                </div>

                {changes.size > 0 && (
                  <button
                    onClick={handleSaveAll}
                    disabled={isSaving}
                    className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    {isSaving
                      ? "Saving..."
                      : `Save ${changes.size} change${changes.size !== 1 ? "s" : ""}`}
                  </button>
                )}
              </div>
            </div>

            {/* Attendance Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Student
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Guardian
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Attendance
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {roll.items.map((item) => {
                    const currentStatus = getStatusForStudent(
                      item.signupId,
                      item.attendance?.status || null,
                    );
                    const hasChanges = changes.has(item.signupId);

                    return (
                      <tr
                        key={item.signupId}
                        className={hasChanges ? "bg-yellow-50" : ""}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {item.childName}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-500">
                            {item.guardianName}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex gap-2">
                            <button
                              onClick={() =>
                                handleStatusChange(item.signupId, "present")
                              }
                              className={`px-3 py-1 rounded-md text-sm font-medium ${
                                currentStatus === "present"
                                  ? "bg-green-600 text-white"
                                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                              }`}
                            >
                              Present
                            </button>
                            <button
                              onClick={() =>
                                handleStatusChange(
                                  item.signupId,
                                  "absent_unknown",
                                )
                              }
                              className={`px-3 py-1 rounded-md text-sm font-medium ${
                                currentStatus === "absent_unknown"
                                  ? "bg-red-600 text-white"
                                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                              }`}
                            >
                              Absent (Unknown)
                            </button>
                            <button
                              onClick={() =>
                                handleStatusChange(
                                  item.signupId,
                                  "absent_known",
                                )
                              }
                              className={`px-3 py-1 rounded-md text-sm font-medium ${
                                currentStatus === "absent_known"
                                  ? "bg-yellow-600 text-white"
                                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                              }`}
                            >
                              Absent (Known)
                            </button>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {item.attendance?.markedAt && (
                            <span className="text-xs text-gray-500">
                              Marked{" "}
                              {new Date(
                                item.attendance.markedAt,
                              ).toLocaleString()}
                            </span>
                          )}
                          {hasChanges && (
                            <span className="ml-2 text-xs text-yellow-700 font-medium">
                              Unsaved
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {roll.items.length === 0 && (
                <div className="text-center py-12 text-gray-500">
                  No students enrolled in this session
                </div>
              )}
            </div>

            {/* Summary */}
            {roll.items.length > 0 && (
              <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Total:</span>{" "}
                  {roll.items.length} students
                  {" • "}
                  <span className="font-medium text-green-700">
                    Present:{" "}
                    {
                      roll.items.filter(
                        (i) =>
                          getStatusForStudent(
                            i.signupId,
                            i.attendance?.status || null,
                          ) === "present",
                      ).length
                    }
                  </span>
                  {" • "}
                  <span className="font-medium text-red-700">
                    Absent:{" "}
                    {
                      roll.items.filter(
                        (i) =>
                          getStatusForStudent(
                            i.signupId,
                            i.attendance?.status || null,
                          ) === "absent",
                      ).length
                    }
                  </span>
                  {" • "}
                  <span className="font-medium text-yellow-700">
                    Excused:{" "}
                    {
                      roll.items.filter(
                        (i) =>
                          getStatusForStudent(
                            i.signupId,
                            i.attendance?.status || null,
                          ) === "excused",
                      ).length
                    }
                  </span>
                </div>
              </div>
            )}
          </div>
        </Layout>
      </div>
    </div>
  );
};

export default AttendanceRoll;
