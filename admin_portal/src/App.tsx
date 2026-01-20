import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Sessions from "./pages/Sessions";
import SessionDetail from "./pages/SessionDetail";
import CreateSession from "./pages/CreateSession";
import EditSession from "./pages/EditSession";
import Locations from "./pages/Locations";
import LocationDetail from "./pages/LocationDetail";
import Terms from "./pages/Terms";
import AttendanceRoll from "./pages/AttendanceRoll";
import Exclusions from "./pages/Exclusions";
import Child from "./pages/Child";
import Students from "./pages/Students";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/sessions"
            element={
              <ProtectedRoute>
                <Sessions />
              </ProtectedRoute>
            }
          />

          <Route
            path="/sessions/new"
            element={
              <ProtectedRoute>
                <CreateSession />
              </ProtectedRoute>
            }
          />

          <Route
            path="/sessions/:id"
            element={
              <ProtectedRoute>
                <SessionDetail />
              </ProtectedRoute>
            }
          />

          <Route
            path="/sessions/:id/edit"
            element={
              <ProtectedRoute>
                <EditSession />
              </ProtectedRoute>
            }
          />

          <Route
            path="/attendance/:occurrenceId"
            element={
              <ProtectedRoute>
                <AttendanceRoll />
              </ProtectedRoute>
            }
          />

          <Route
            path="/locations"
            element={
              <ProtectedRoute>
                <Locations />
              </ProtectedRoute>
            }
          />

          <Route
            path="/locations/:id"
            element={
              <ProtectedRoute>
                <LocationDetail />
              </ProtectedRoute>
            }
          />

          <Route
            path="/terms"
            element={
              <ProtectedRoute>
                <Terms />
              </ProtectedRoute>
            }
          />

          <Route
            path="/exclusions"
            element={
              <ProtectedRoute>
                <Exclusions />
              </ProtectedRoute>
            }
          />

          <Route
            path="/students"
            element={
              <ProtectedRoute>
                <Students />
              </ProtectedRoute>
            }
          />

          <Route
            path="/children/:id"
            element={
              <ProtectedRoute>
                <Child />
              </ProtectedRoute>
            }
          />

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
