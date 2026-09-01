// File: frontend/src/routes/AppRoutes.tsx
import { Navigate, Route, Routes } from "react-router-dom";

import AdminLayout from "@/components/layout/AdminLayout";
import ProtectedLayout from "@/components/layout/ProtectedLayout";
import PublicLayout from "@/components/layout/PublicLayout";
import AdminAuditPage from "@/features/admin/AdminAuditPage";
import AdminDashboardPage from "@/features/admin/AdminDashboardPage";
import AdminDocumentsPage from "@/features/admin/AdminDocumentsPage";
import AdminPoliciesPage from "@/features/admin/AdminPoliciesPage";
import AdminProvidersPage from "@/features/admin/AdminProvidersPage";
import LoginPage from "@/features/auth/LoginPage";
import RegisterPage from "@/features/auth/RegisterPage";
import ComparePage from "@/features/compare/ComparePage";
import DashboardPage from "@/features/dashboard/DashboardPage";
import PolicyDetailPage from "@/features/policy/PolicyDetailPage";
import RecommendationsPage from "@/features/recommendations/RecommendationsPage";
import UploadPage from "@/features/upload/UploadPage";
import HomePage from "@/pages/HomePage";
import LegalInfoPage from "@/pages/LegalInfoPage";
import NotFoundPage from "@/pages/NotFoundPage";

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/legal" element={<LegalInfoPage />} />
      </Route>

      {/* User (authenticated) */}
      <Route element={<ProtectedLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/recommendations" element={<RecommendationsPage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/policies/:id" element={<PolicyDetailPage />} />
      </Route>

      {/* Admin */}
      <Route element={<ProtectedLayout adminOnly />}>
        <Route element={<AdminLayout />}>
          <Route path="/admin" element={<AdminDashboardPage />} />
          <Route path="/admin/providers" element={<AdminProvidersPage />} />
          <Route path="/admin/policies" element={<AdminPoliciesPage />} />
          <Route path="/admin/documents" element={<AdminDocumentsPage />} />
          <Route path="/admin/audit" element={<AdminAuditPage />} />
        </Route>
      </Route>

      {/* Convenience redirect */}
      <Route path="/home" element={<Navigate to="/" replace />} />

      {/* Fallback */}
      <Route element={<PublicLayout />}>
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
