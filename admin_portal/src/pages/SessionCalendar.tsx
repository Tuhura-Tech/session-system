import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { adminApi } from "../services/api";
import type { Session, Occurrence } from "../types";

export default function SessionCalendar() {
  const { id } = useParams<{ id: string }>();
  const [session, setSession] = useState<Session | null>(null);
  const [occurrences, setOccurrences] = useState<Occurrence[]>([]);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [loading, setLoading] = useState(true);
  const [selectedOccurrence, setSelectedOccurrence] =
    useState<Occurrence | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        if (!id) return;
        const [sessionData, occurrencesData] = await Promise.all([
          adminApi.getSession(id),
          adminApi.getSessionOccurrences(id),
        ]);
        setSession(sessionData);
        setOccurrences(occurrencesData);
      } catch (err) {
        console.error("Failed to load data:", err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id]);

  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const formatDate = (date: Date) => date.toISOString().split("T")[0];

  const getOccurrencesForDay = (day: number) => {
    const dateStr = formatDate(
      new Date(currentDate.getFullYear(), currentDate.getMonth(), day),
    );
    return occurrences.filter((occ) => {
      const occDate = occ.startsAt.split("T")[0];
      return occDate === dateStr;
    });
  };

  const handlePrevMonth = () => {
    setCurrentDate(
      new Date(currentDate.getFullYear(), currentDate.getMonth() - 1),
    );
  };

  const handleNextMonth = () => {
    setCurrentDate(
      new Date(currentDate.getFullYear(), currentDate.getMonth() + 1),
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading calendar...</p>
        </div>
      </div>
    );
  }

  const daysInMonth = getDaysInMonth(currentDate);
  const firstDay = getFirstDayOfMonth(currentDate);
  const monthName = currentDate.toLocaleString("default", {
    month: "long",
    year: "numeric",
  });
  const dayLabels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
  const calendarDays: (number | null)[] = [
    ...Array.from({ length: firstDay }, () => null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {session?.name} - Calendar
          </h1>
          <p className="text-gray-600">
            {occurrences.length} occurrences scheduled
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Calendar */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
              {/* Calendar Header */}
              <div className="bg-blue-50 px-6 py-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <button
                    onClick={handlePrevMonth}
                    className="p-2 hover:bg-blue-100 rounded transition"
                  >
                    <ChevronLeft className="w-5 h-5" />
                  </button>
                  <h2 className="text-lg font-semibold text-gray-900 min-w-40 text-center">
                    {monthName}
                  </h2>
                  <button
                    onClick={handleNextMonth}
                    className="p-2 hover:bg-blue-100 rounded transition"
                  >
                    <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Day Labels */}
              <div className="grid grid-cols-7 bg-gray-100 border-b border-gray-200">
                {dayLabels.map((day) => (
                  <div
                    key={day}
                    className="p-3 text-center font-semibold text-gray-700 text-sm"
                  >
                    {day}
                  </div>
                ))}
              </div>

              {/* Calendar Grid */}
              <div className="grid grid-cols-7 gap-px bg-gray-200 p-px">
                {calendarDays.map((day, idx) => {
                  const dayOccurrences = day
                    ? getOccurrencesForDay(day as number)
                    : [];
                  const isCurrentMonth = day !== null;
                  const isToday =
                    isCurrentMonth &&
                    new Date().getDate() === day &&
                    new Date().getMonth() === currentDate.getMonth() &&
                    new Date().getFullYear() === currentDate.getFullYear();

                  return (
                    <div
                      key={idx}
                      className={`min-h-24 p-2 text-sm ${
                        isCurrentMonth
                          ? `bg-white ${isToday ? "ring-2 ring-blue-400" : ""}`
                          : "bg-gray-50"
                      } cursor-pointer hover:bg-blue-50 transition`}
                    >
                      {isCurrentMonth && (
                        <>
                          <div
                            className={`font-semibold mb-1 ${isToday ? "text-blue-600" : "text-gray-900"}`}
                          >
                            {day}
                          </div>
                          <div className="space-y-1">
                            {dayOccurrences.slice(0, 2).map((occ) => (
                              <div
                                key={occ.id}
                                onClick={() => setSelectedOccurrence(occ)}
                                className="bg-blue-100 text-blue-800 rounded px-1 py-0.5 text-xs truncate hover:bg-blue-200"
                              >
                                {new Date(occ.startsAt).toLocaleTimeString([], {
                                  hour: "2-digit",
                                  minute: "2-digit",
                                })}
                              </div>
                            ))}
                            {dayOccurrences.length > 2 && (
                              <div className="text-xs text-gray-500 px-1">
                                +{dayOccurrences.length - 2} more
                              </div>
                            )}
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Sidebar - Details */}
          <div className="lg:col-span-1">
            {selectedOccurrence ? (
              <div className="bg-white rounded-lg shadow-md p-6 sticky top-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Occurrence Details
                </h3>

                <div className="space-y-4">
                  <div>
                    <p className="text-sm font-medium text-gray-500">
                      Date & Time
                    </p>
                    <p className="text-gray-900 mt-1">
                      {new Date(selectedOccurrence.startsAt).toLocaleString()}
                    </p>
                  </div>

                  <div>
                    <p className="text-sm font-medium text-gray-500">Status</p>
                    <p className="text-gray-900 mt-1 capitalize">
                      {selectedOccurrence.cancelled ? (
                        <span className="text-red-600">Cancelled</span>
                      ) : (
                        "Scheduled"
                      )}
                    </p>
                  </div>

                  {selectedOccurrence.cancellationReason && (
                    <div>
                      <p className="text-sm font-medium text-gray-500">
                        Cancellation Reason
                      </p>
                      <p className="text-gray-900 mt-1">
                        {selectedOccurrence.cancellationReason}
                      </p>
                    </div>
                  )}
                </div>

                <button
                  onClick={() => setSelectedOccurrence(null)}
                  className="mt-6 w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition"
                >
                  Close
                </button>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-md p-6">
                <p className="text-center text-gray-500">
                  Click an occurrence to view details
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
