import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/layout/ProtectedRoute";
import { LoginPage } from "./pages/Auth/LoginPage";
import { RegisterPage } from "./pages/Auth/RegisterPage";
import { DashboardPage } from "./pages/Dashboard/DashboardPage";
import { ComingSoonPage } from "./pages/ComingSoonPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/labs"
            element={
              <ProtectedRoute>
                <ComingSoonPage title="Labs" milestone="Milestone 2" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ctfs"
            element={
              <ProtectedRoute>
                <ComingSoonPage title="CTFs" milestone="Milestone 6" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/skills"
            element={
              <ProtectedRoute>
                <ComingSoonPage title="Skills" milestone="Milestone 4" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tools"
            element={
              <ProtectedRoute>
                <ComingSoonPage title="Tools" milestone="Milestone 4" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/mitre"
            element={
              <ProtectedRoute>
                <ComingSoonPage title="MITRE ATT&CK" milestone="Milestone 5" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/evidence"
            element={
              <ProtectedRoute>
                <ComingSoonPage title="Evidence" milestone="Milestone 3" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/roadmap"
            element={
              <ProtectedRoute>
                <ComingSoonPage title="Learning Roadmap" milestone="Milestone 8" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/portfolio"
            element={
              <ProtectedRoute>
                <ComingSoonPage title="Portfolio" milestone="Milestone 9" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute>
                <ComingSoonPage title="Reports" milestone="Milestone 10" />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <ComingSoonPage title="Settings" milestone="a later milestone" />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
