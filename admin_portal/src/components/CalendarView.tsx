import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { adminApi } from "../services/api";
import type { Session, Occurrence } from "../types";

interface CalendarViewProps {
  currentStaffId?: string;
}

interface CalendarDay {
  date: Date;
  isCurrentMonth: boolean;
  occurrences: Array<{
    id: string;
    sessionId: string;
    sessionName: string;
    startTime: string;
    endTime: string;
    isAssigned: boolean;
    cancelled: boolean;
  }>;
}

const CalendarView: React.FC<CalendarViewProps> = ({ currentStaffId }) => {
  const navigate = useNavigate();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [calendarDays, setCalendarDays] = useState<CalendarDay[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadCalendarData();
  }, [currentDate]);

  const loadCalendarData = async () => {
    try {
      setIsLoading(true);
      const year = currentDate.getFullYear();

      // Fetch all sessions for the year
      const allSessions = await adminApi.getSessions(year);

      // Fetch occurrences for each session
      const occurrencesPromises = allSessions.map((session) =>
        adminApi.getSessionOccurrences(session.id).catch(() => []),
      );
      const allOccurrences = await Promise.all(occurrencesPromises);

      // Build calendar grid
      const days = buildCalendarGrid(
        currentDate,
        allSessions,
        allOccurrences.flat(),
      );
      setCalendarDays(days);
    } catch (error) {
      console.error("Failed to load calendar data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const buildCalendarGrid = (
    date: Date,
    sessions: Session[],
    occurrences: Occurrence[],
  ): CalendarDay[] => {
    const year = date.getFullYear();
    const month = date.getMonth();

    // First day of the month
    const firstDay = new Date(year, month, 1);

    // Start from the Monday before the first day of the month
    const startDate = new Date(firstDay);
    const dayOfWeek = firstDay.getDay();
    const daysToSubtract = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
    startDate.setDate(firstDay.getDate() - daysToSubtract);

    // Build 6 weeks (42 days) to cover all possible month layouts
    const days: CalendarDay[] = [];
    const currentDay = new Date(startDate);

    for (let i = 0; i < 42; i++) {
      const dateStr = currentDay.toISOString().split("T")[0];

      // Find occurrences for this day
      const dayOccurrences = occurrences
        .filter((occ) => occ.startsAt.split("T")[0] === dateStr)
        .map((occ) => {
          const session = sessions.find((s) => s.id === occ.sessionId);
          return {
            id: occ.id,
            sessionId: occ.sessionId,
            sessionName: session?.name || "Unknown",
            startTime: session?.startTime || "",
            endTime: session?.endTime || "",
            isAssigned: false, // Staff assignments not included in calendar
            cancelled: occ.cancelled,
          };
        });

      days.push({
        date: new Date(currentDay),
        isCurrentMonth: currentDay.getMonth() === month,
        occurrences: dayOccurrences,
      });

      currentDay.setDate(currentDay.getDate() + 1);
    }

    return days;
  };

  const goToPreviousMonth = () => {
    setCurrentDate(
      new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1),
    );
  };

  const goToNextMonth = () => {
    setCurrentDate(
      new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1),
    );
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const monthName = currentDate.toLocaleDateString("en-NZ", {
    month: "long",
    year: "numeric",
  });
  const weekDays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-900">
          Session Calendar
        </h2>
        <div className="flex items-center gap-2">
          <button
            onClick={goToToday}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md"
          >
            Today
          </button>
          <button
            onClick={goToPreviousMonth}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <span className="text-sm font-medium min-w-37.5 text-center">
            {monthName}
          </span>
          <button
            onClick={goToNextMonth}
            className="p-1 hover:bg-gray-100 rounded"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      <div className="p-4">
        {isLoading ? (
          <div className="text-center py-12 text-gray-500">
            Loading calendar...
          </div>
        ) : (
          <div className="grid grid-cols-7 gap-1">
            {/* Week day headers */}
            {weekDays.map((day) => (
              <div
                key={day}
                className="text-center text-xs font-semibold text-gray-600 py-2"
              >
                {day}
              </div>
            ))}

            {/* Calendar days */}
            {calendarDays.map((day, index) => {
              const isToday =
                day.date.toDateString() === new Date().toDateString();

              return (
                <div
                  key={index}
                  className={`min-h-25 border rounded p-1 ${
                    day.isCurrentMonth
                      ? "bg-white border-gray-200"
                      : "bg-gray-50 border-gray-100"
                  } ${isToday ? "ring-2 ring-blue-500" : ""}`}
                >
                  <div
                    className={`text-xs font-medium mb-1 ${
                      day.isCurrentMonth ? "text-gray-900" : "text-gray-400"
                    } ${isToday ? "text-blue-600 font-bold" : ""}`}
                  >
                    {day.date.getDate()}
                  </div>

                  <div className="space-y-1">
                    {day.occurrences.map((occ) => (
                      <div
                        key={occ.id}
                        onClick={() =>
                          !occ.cancelled && navigate(`/attendance/${occ.id}`)
                        }
                        className={`text-xs p-1 rounded truncate ${
                          occ.cancelled
                            ? "bg-gray-200 text-gray-500 line-through cursor-not-allowed"
                            : occ.isAssigned
                              ? "bg-blue-100 text-blue-800 font-medium cursor-pointer hover:bg-blue-200"
                              : "bg-green-100 text-green-800 cursor-pointer hover:bg-green-200"
                        }`}
                        title={`${occ.sessionName} ${occ.startTime}-${occ.endTime}${occ.cancelled ? " (Cancelled)" : ""}${!occ.cancelled ? " - Click to view attendance" : ""}`}
                      >
                        {occ.startTime && `${occ.startTime} `}
                        {occ.sessionName}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="px-6 py-3 border-t border-gray-200 flex gap-4 text-xs">
        {currentStaffId && (
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-100 rounded"></div>
            <span className="text-gray-600">Your sessions</span>
          </div>
        )}
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-green-100 rounded"></div>
          <span className="text-gray-600">Other sessions</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-gray-200 rounded"></div>
          <span className="text-gray-600">Cancelled</span>
        </div>
      </div>
    </div>
  );
};

export default CalendarView;
