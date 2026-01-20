import api from "../lib/api";
import type {
  Session,
  SessionLocation,
  SessionBlock,
  SchoolTerm,
  ExclusionDate,
  Signup,
  AttendanceRoll,
  AttendanceUpsert,
  AttendanceRecord,
  Occurrence,
  Staff,
  StaffListItem,
  StaffSessionSummary,
  ChildDetails,
  ChildNote,
} from "../types";

export const adminApi = {
  // Auth
  checkSession: async () => {
    const { data } = await api.get("/admin/auth/me");
    return data;
  },

  logout: async () => {
    await api.post("/admin/auth/logout");
  },

  // Sessions
  getSessions: async (
    year?: number,
    includeArchived = false,
  ): Promise<Session[]> => {
    const params = new URLSearchParams();
    if (year) params.append("year", year.toString());
    if (includeArchived) params.append("include_archived", "true");
    const { data } = await api.get(`/admin/sessions?${params}`);
    return data;
  },

  getSession: async (id: string): Promise<Session> => {
    const { data } = await api.get(`/admin/sessions/${id}`);
    return data;
  },

  createSession: async (session: any): Promise<Session> => {
    const { data } = await api.post("/admin/sessions", session);
    return data;
  },

  updateSession: async (id: string, session: any): Promise<Session> => {
    const { data } = await api.patch(`/admin/sessions/${id}`, session);
    return data;
  },

  deleteSession: async (id: string): Promise<void> => {
    await api.delete(`/admin/sessions/${id}`);
  },

  duplicateSession: async (id: string): Promise<Session> => {
    const { data } = await api.post(`/admin/sessions/${id}/duplicate`);
    return data;
  },

  // Locations
  getLocations: async (): Promise<SessionLocation[]> => {
    const { data } = await api.get("/admin/locations");
    return data;
  },

  getLocation: async (id: string): Promise<SessionLocation> => {
    const { data } = await api.get(`/admin/locations/${id}`);
    return data;
  },

  getLocationSessions: async (
    id: string,
    year?: number,
    includeArchived = false,
  ): Promise<Session[]> => {
    const params = new URLSearchParams();
    if (year) params.append("year", year.toString());
    if (includeArchived) params.append("include_archived", "true");
    const qs = params.toString();
    const url = qs
      ? `/admin/locations/${id}/sessions?${qs}`
      : `/admin/locations/${id}/sessions`;
    const { data } = await api.get(url);
    return data;
  },

  createLocation: async (
    location: Partial<SessionLocation>,
  ): Promise<SessionLocation> => {
    const { data } = await api.post("/admin/locations", location);
    return data;
  },

  updateLocation: async (
    id: string,
    location: Partial<SessionLocation>,
  ): Promise<SessionLocation> => {
    const { data } = await api.patch(`/admin/locations/${id}`, location);
    return data;
  },

  // Blocks
  getBlocks: async (year?: number): Promise<SessionBlock[]> => {
    const params = year ? `?year=${year}` : "";
    const { data } = await api.get(`/admin/blocks${params}`);
    return data;
  },

  createBlock: async (block: Partial<SessionBlock>): Promise<SessionBlock> => {
    const { data } = await api.post("/admin/blocks", block);
    return data;
  },

  updateBlock: async (
    id: string,
    block: Partial<SessionBlock>,
  ): Promise<SessionBlock> => {
    const { data } = await api.patch(`/admin/blocks/${id}`, block);
    return data;
  },

  // Terms
  getTerms: async (year?: number): Promise<SchoolTerm[]> => {
    const params = year ? `?year=${year}` : "";
    const { data } = await api.get(`/admin/terms${params}`);
    return data;
  },

  createTerm: async (term: Partial<SchoolTerm>): Promise<SchoolTerm> => {
    const { data } = await api.post("/admin/terms", term);
    return data;
  },

  updateTerm: async (
    id: string,
    term: Partial<SchoolTerm>,
  ): Promise<SchoolTerm> => {
    const { data } = await api.patch(`/admin/terms/${id}`, term);
    return data;
  },

  // Exclusions
  getExclusions: async (year?: number): Promise<ExclusionDate[]> => {
    const params = year ? `?year=${year}` : "";
    const { data } = await api.get(`/admin/exclusions${params}`);
    return data;
  },

  createExclusion: async (exclusion: {
    date: string;
    reason: string | null;
  }): Promise<ExclusionDate> => {
    const { data } = await api.post("/admin/exclusions", exclusion);
    return data;
  },

  updateExclusion: async (
    id: string,
    exclusion: { reason: string | null },
  ): Promise<ExclusionDate> => {
    const { data } = await api.patch(`/admin/exclusions/${id}`, exclusion);
    return data;
  },

  deleteExclusion: async (id: string): Promise<void> => {
    await api.delete(`/admin/exclusions/${id}`);
  },

  // Signups
  getSessionSignups: async (
    sessionId: string,
    status?: string,
  ): Promise<Signup[]> => {
    const params = status ? `?status=${status}` : "";
    const { data } = await api.get(
      `/admin/sessions/${sessionId}/signups${params}`,
    );
    return data;
  },

  updateSignupStatus: async (
    signupId: string,
    status: string,
  ): Promise<Signup> => {
    const { data } = await api.patch(`/admin/signups/${signupId}/status`, {
      status,
    });
    return data;
  },

  // Occurrences
  getSessionOccurrences: async (sessionId: string): Promise<Occurrence[]> => {
    const { data } = await api.get(`/admin/sessions/${sessionId}/occurrences`);
    return data;
  },

  generateOccurrences: async (
    sessionId: string,
  ): Promise<{ created: number; skippedExisting: number }> => {
    const { data } = await api.post(
      `/admin/sessions/${sessionId}/occurrences/generate`,
    );
    return data;
  },

  cancelOccurrence: async (
    occurrenceId: string,
    reason?: string,
  ): Promise<Occurrence> => {
    const { data } = await api.patch(
      `/admin/occurrences/${occurrenceId}/cancel`,
      {
        cancelled: true,
        cancellationReason: reason,
      },
    );
    return data;
  },

  reinstateOccurrence: async (occurrenceId: string): Promise<Occurrence> => {
    const { data } = await api.patch(
      `/admin/occurrences/${occurrenceId}/cancel`,
      {
        cancelled: false,
      },
    );
    return data;
  },

  // Attendance
  getAttendanceRoll: async (occurrenceId: string): Promise<AttendanceRoll> => {
    const { data } = await api.get(`/admin/occurrences/${occurrenceId}/roll`);
    return data;
  },

  markAttendance: async (
    occurrenceId: string,
    attendance: AttendanceUpsert,
  ): Promise<AttendanceRecord> => {
    const { data } = await api.post(
      `/admin/occurrences/${occurrenceId}/attendance`,
      attendance,
    );
    return data;
  },

  // Exports
  exportSignupsCSV: async (
    sessionId: string,
    status?: string,
  ): Promise<Blob> => {
    const params = status ? `?status=${status}` : "";
    const { data } = await api.get(
      `/admin/sessions/${sessionId}/export/signups.csv${params}`,
      {
        responseType: "blob",
      },
    );
    return data;
  },

  exportAttendanceCSV: async (sessionId: string): Promise<Blob> => {
    const { data } = await api.get(
      `/admin/sessions/${sessionId}/export/attendance.csv`,
      {
        responseType: "blob",
      },
    );
    return data;
  },

  // Staff
  getStaff: async (activeOnly = true): Promise<StaffListItem[]> => {
    const params = activeOnly ? "?active_only=true" : "?active_only=false";
    const { data } = await api.get(`/admin/staff/${params}`);
    return data;
  },

  getStaffMember: async (staffId: string): Promise<Staff> => {
    const { data } = await api.get(`/admin/staff/${staffId}`);
    return data;
  },

  createStaff: async (payload: {
    name: string;
    email: string;
    ssoId: string;
  }): Promise<Staff> => {
    const { data } = await api.post("/admin/staff/", {
      name: payload.name,
      email: payload.email,
      sso_id: payload.ssoId,
    });
    return data;
  },

  updateStaff: async (
    staffId: string,
    payload: Partial<{ name: string; email: string; active: boolean }>,
  ): Promise<Staff> => {
    const { data } = await api.patch(`/admin/staff/${staffId}`, payload);
    return data;
  },

  getStaffSessions: async (staffId: string): Promise<StaffSessionSummary[]> => {
    const { data } = await api.get(`/admin/staff/${staffId}/sessions`);
    return data;
  },

  getSessionStaff: async (sessionId: string): Promise<StaffListItem[]> => {
    const { data } = await api.get(`/admin/sessions/${sessionId}/staff`);
    return data;
  },

  assignSessionStaff: async (
    sessionId: string,
    staffIds: string[],
  ): Promise<{ message: string }> => {
    const { data } = await api.post(`/admin/sessions/${sessionId}/staff`, {
      staff_ids: staffIds,
    });
    return data;
  },

  removeSessionStaff: async (
    sessionId: string,
    staffId: string,
  ): Promise<void> => {
    await api.delete(`/admin/sessions/${sessionId}/staff/${staffId}`);
  },

  // Children / Notes
  getChild: async (childId: string): Promise<ChildDetails> => {
    const { data } = await api.get(`/admin/children/${childId}`);
    return data;
  },

  getChildNotes: async (childId: string): Promise<ChildNote[]> => {
    const { data } = await api.get(`/admin/children/${childId}/notes`);
    return data;
  },

  addChildNote: async (
    childId: string,
    payload: { note: string; author?: string | null },
  ): Promise<ChildNote> => {
    const { data } = await api.post(`/admin/children/${childId}/notes`, {
      note: payload.note,
      author: payload.author ?? null,
    });
    return data;
  },

  // Children list
  listChildren: async (): Promise<ChildDetails[]> => {
    const { data } = await api.get("/admin/children");
    return data;
  },

  // Attendance History
  getAttendanceHistory: async (
    occurrenceId: string,
    childId?: string,
  ): Promise<AttendanceRecord[]> => {
    const params = childId ? `?child_id=${childId}` : "";
    const { data } = await api.get(
      `/admin/occurrences/${occurrenceId}/attendance-history${params}`,
    );
    return data;
  },

  // Communications
  bulkEmailSession: async (
    sessionId: string,
    payload: { subject: string; message: string; actor?: string | null },
  ): Promise<{ enqueued: number }> => {
    const { data } = await api.post(
      `/admin/sessions/${sessionId}/email`,
      payload,
    );
    return data;
  },

  notifySession: async (
    sessionId: string,
    payload: {
      updateTitle: string;
      updateMessage?: string | null;
      affectedDate?: string | null;
      actor?: string | null;
    },
  ): Promise<{ enqueued: number }> => {
    const { data } = await api.post(
      `/admin/sessions/${sessionId}/notify`,
      payload,
    );
    return data;
  },
};
