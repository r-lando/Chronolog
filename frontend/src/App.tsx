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
import { SkillsListPage } from "./pages/Skills/SkillsListPage";
import { SkillDetailPage } from "./pages/Skills/SkillDetailPage";
import { ToolsListPage } from "./pages/Tools/ToolsListPage";
import { ToolDetailPage } from "./pages/Tools/ToolDetailPage";
import { MitreListPage } from "./pages/Mitre/MitreListPage";
import { MitreDetailPage } from "./pages/Mitre/MitreDetailPage";
import { CtfEventsListPage } from "./pages/CTFs/CtfEventsListPage";
import { CtfEventDetailPage } from "./pages/CTFs/CtfEventDetailPage";
import { CtfChallengeDetailPage } from "./pages/CTFs/CtfChallengeDetailPage";
import { RoadmapPage } from "./pages/Roadmap/RoadmapPage";
import { PortfolioPage } from "./pages/Portfolio/PortfolioPage";
import { PublicPortfolioIndexPage } from "./pages/Public/PublicPortfolioIndexPage";
import { PublicLabPage } from "./pages/Public/PublicLabPage";
import { ReportsPage } from "./pages/Reports/ReportsPage";
import { SearchResultsPage } from "./pages/Search/SearchResultsPage";
import { SettingsPage } from "./pages/Settings/SettingsPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/p" element={<PublicPortfolioIndexPage />} />
          <Route path="/p/:slug" element={<PublicLabPage />} />
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
                <CtfEventsListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ctfs/challenges/:challengeId"
            element={
              <ProtectedRoute>
                <CtfChallengeDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ctfs/:eventId"
            element={
              <ProtectedRoute>
                <CtfEventDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/skills"
            element={
              <ProtectedRoute>
                <SkillsListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/skills/:id"
            element={
              <ProtectedRoute>
                <SkillDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tools"
            element={
              <ProtectedRoute>
                <ToolsListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/tools/:id"
            element={
              <ProtectedRoute>
                <ToolDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/mitre"
            element={
              <ProtectedRoute>
                <MitreListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/mitre/:id"
            element={
              <ProtectedRoute>
                <MitreDetailPage />
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
                <RoadmapPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/portfolio"
            element={
              <ProtectedRoute>
                <PortfolioPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <ProtectedRoute>
                <ReportsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/search"
            element={
              <ProtectedRoute>
                <SearchResultsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
