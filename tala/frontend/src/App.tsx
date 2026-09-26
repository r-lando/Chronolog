import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/layout/ProtectedRoute";
import { LoginPage } from "./pages/Auth/LoginPage";
import { RegisterPage } from "./pages/Auth/RegisterPage";
import { DashboardPage } from "./pages/Dashboard/DashboardPage";
import { LabsListPage } from "./pages/Labs/LabsListPage";
import { LabFormPage } from "./pages/Labs/LabFormPage";
import { LabDetailPage } from "./pages/Labs/LabDetailPage";
import { EvidencePage } from "./pages/Evidence/EvidencePage";
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
                <LabsListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/labs/new"
            element={
              <ProtectedRoute>
                <LabFormPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/labs/:id"
            element={
              <ProtectedRoute>
                <LabDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/labs/:id/edit"
            element={
              <ProtectedRoute>
                <LabFormPage />
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
                <EvidencePage />
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
