import { Outlet, NavLink } from "react-router-dom";
import { useAuthStore } from "@/store/auth";

const NAV_ITEMS = [
  { to: "/dashboard",  label: "Dashboard" },
  { to: "/assets",     label: "Assets" },
  { to: "/workorders", label: "Work Orders" },
  { to: "/agents",     label: "AI Agents" },
  { to: "/costs",      label: "Cost Management" },
  { to: "/compliance", label: "Compliance" },
];

export default function AppLayout() {
  const { user, logout } = useAuthStore();
  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg)" }}>
      <aside className="sidebar">
        <div className="brand" style={{ padding: "16px 14px" }}>
          <div className="brand-icon">G2</div>
          <div className="brand-text">
            <span className="brand-name">GER2</span>
            <span className="brand-sub">CMMS v2.4</span>
          </div>
        </div>
        <nav className="sidenav">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
            >
              <span className="nav-label">{item.label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          {user?.full_name} · {user?.role}
          <button onClick={logout} style={{ marginLeft: 8, background: "none", border: "none", color: "var(--muted)", cursor: "pointer" }}>
            Logout
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
