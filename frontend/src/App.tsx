import { useEffect } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { api } from "./lib/api";
import { useMe } from "./lib/queries";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import CRM from "./pages/CRM";
import Clients from "./pages/Clients";
import Login from "./pages/Login";

function AuthGate({ children }: { children: React.ReactNode }) {
  const { data: user, isLoading, isError } = useMe();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="h-screen w-full flex items-center justify-center">
        <div className="text-ink-soft text-sm">Loading…</div>
      </div>
    );
  }

  if (isError || !user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
}

export default function App() {
  // Prime the CSRF cookie once on app boot so subsequent POSTs have a token.
  useEffect(() => {
    api.primeCsrf().catch(() => undefined);
  }, []);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <AuthGate>
            <Layout />
          </AuthGate>
        }
      >
        <Route index element={<Home />} />
        <Route path="/crm" element={<CRM />} />
        <Route path="/clients" element={<Clients />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
