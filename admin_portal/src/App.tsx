import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './context/AuthContext';
import AttendanceRoll from './pages/AttendanceRoll';
import Child from './pages/Child';
import CreateSession from './pages/CreateSession';
import Dashboard from './pages/Dashboard';
import EditSession from './pages/EditSession';
import Exclusions from './pages/Exclusions';
import LocationDetail from './pages/LocationDetail';
import Locations from './pages/Locations';
import Login from './pages/Login';
import SessionDetail from './pages/SessionDetail';
import Sessions from './pages/Sessions';
import Students from './pages/Students';
import Terms from './pages/Terms';

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
						path="/students/:id"
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
