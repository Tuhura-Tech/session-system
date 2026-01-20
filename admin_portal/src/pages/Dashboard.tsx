import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Calendar, Users, MapPin, TrendingUp } from "lucide-react";
import Sidebar from "../components/Sidebar";
import Layout from "../components/Layout";
import { LoadingSpinner } from "../components/Alert";
import CalendarView from "../components/CalendarView";
import { adminApi } from "../services/api";
import type { Session } from "../types";

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({
    totalSessions: 0,
    activeSessions: 0,
    totalLocations: 0,
    currentYear: new Date().getFullYear(),
  });
  const [recentSessions, setRecentSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const currentYear = new Date().getFullYear();

      const [sessions, locations] = await Promise.all([
        adminApi.getSessions(currentYear),
        adminApi.getLocations(),
      ]);

      const activeSessions = sessions.filter((s) => !s.archived);

      setStats({
        totalSessions: sessions.length,
        activeSessions: activeSessions.length,
        totalLocations: locations.length,
        currentYear,
      });

      setRecentSessions(activeSessions.slice(0, 5));
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
      setError("Failed to load dashboard data. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar />

      <div className="flex-1">
        <Layout title="Dashboard">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          {isLoading ? (
            <LoadingSpinner />
          ) : (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-blue-100 text-blue-600">
                      <Calendar className="w-6 h-6" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">
                        Total Sessions
                      </p>
                      <p className="text-2xl font-semibold text-gray-900">
                        {stats.totalSessions}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {stats.currentYear}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-green-100 text-green-600">
                      <TrendingUp className="w-6 h-6" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">
                        Active Sessions
                      </p>
                      <p className="text-2xl font-semibold text-gray-900">
                        {stats.activeSessions}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {stats.totalSessions > 0
                          ? `${Math.round((stats.activeSessions / stats.totalSessions) * 100)}% of total`
                          : "N/A"}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-purple-100 text-purple-600">
                      <MapPin className="w-6 h-6" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">
                        Locations
                      </p>
                      <p className="text-2xl font-semibold text-gray-900">
                        {stats.totalLocations}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        Available venues
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <Link
                  to="/sessions/new"
                  className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow flex items-center gap-4 group"
                >
                  <div className="p-3 rounded-full bg-blue-50 text-blue-600 group-hover:bg-blue-100">
                    <Calendar className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 group-hover:text-blue-600">
                      New Session
                    </h3>
                    <p className="text-sm text-gray-500">
                      Create a new session
                    </p>
                  </div>
                </Link>

                <Link
                  to="/locations"
                  className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow flex items-center gap-4 group"
                >
                  <div className="p-3 rounded-full bg-purple-50 text-purple-600 group-hover:bg-purple-100">
                    <MapPin className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 group-hover:text-purple-600">
                      Locations
                    </h3>
                    <p className="text-sm text-gray-500">Manage venues</p>
                  </div>
                </Link>

                <Link
                  to="/terms"
                  className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow flex items-center gap-4 group"
                >
                  <div className="p-3 rounded-full bg-green-50 text-green-600 group-hover:bg-green-100">
                    <Users className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 group-hover:text-green-600">
                      Terms
                    </h3>
                    <p className="text-sm text-gray-500">Manage school terms</p>
                  </div>
                </Link>
              </div>

              {/* Calendar View */}
              <div className="mb-8">
                <CalendarView />
              </div>

              {/* Recent Sessions */}
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                  <h2 className="text-lg font-semibold text-gray-900">
                    Recent Sessions
                  </h2>
                  <Link
                    to="/sessions"
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    View all →
                  </Link>
                </div>
                <div className="p-6">
                  {recentSessions.length === 0 ? (
                    <div className="text-center py-8">
                      <p className="text-gray-500 mb-4">No sessions yet</p>
                      <Link
                        to="/sessions/new"
                        className="inline-block px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700"
                      >
                        Create First Session
                      </Link>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {recentSessions.map((session) => (
                        <Link
                          key={session.id}
                          to={`/sessions/${session.id}`}
                          className="block p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
                        >
                          <div className="flex justify-between items-start">
                            <div>
                              <h3 className="font-semibold text-gray-900">
                                {session.name}
                              </h3>
                              <p className="text-sm text-gray-600 mt-1">
                                {session.dayOfWeek} {session.startTime} -{" "}
                                {session.endTime}
                              </p>
                              {session.location && (
                                <p className="text-xs text-gray-500 mt-1">
                                  📍 {session.location.name}
                                </p>
                              )}
                            </div>
                            <div className="text-right">
                              <span
                                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                  session.waitlist
                                    ? "bg-yellow-100 text-yellow-800"
                                    : "bg-green-100 text-green-800"
                                }`}
                              >
                                {session.waitlist ? "Waitlist" : "Active"}
                              </span>
                            </div>
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </Layout>
      </div>
    </div>
  );
};

export default Dashboard;
