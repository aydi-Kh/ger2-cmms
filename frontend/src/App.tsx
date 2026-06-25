import { Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/auth";
import AppLayout from "@/components/layout/AppLayout";
import LoginScreen from "@/screens/LoginScreen";
import DashboardScreen from "@/screens/DashboardScreen";
import AssetsScreen from "@/screens/AssetsScreen";
import WorkOrdersScreen from "@/screens/WorkOrdersScreen";
import AIAgentsScreen from "@/screens/AIAgentsScreen";
import CostsScreen from "@/screens/CostsScreen";
import ComplianceScreen from "@/screens/ComplianceScreen";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginScreen />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <AppLayout />
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard"  element={<DashboardScreen />} />
        <Route path="assets"     element={<AssetsScreen />} />
        <Route path="workorders" element={<WorkOrdersScreen />} />
        <Route path="agents"     element={<AIAgentsScreen />} />
        <Route path="costs"      element={<CostsScreen />} />
        <Route path="compliance" element={<ComplianceScreen />} />
      </Route>
    </Routes>
  );
}
