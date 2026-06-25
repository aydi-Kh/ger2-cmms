import { useQuery } from "@tanstack/react-query";
import { assetsApi } from "@/api/assets";
import { workOrdersApi } from "@/api/workorders";

export default function DashboardScreen() {
  const { data: assets = [], isLoading: loadingAssets } = useQuery({
    queryKey: ["assets"],
    queryFn: () => assetsApi.list({ limit: 100 }),
  });
  const { data: workOrders = [], isLoading: loadingWO } = useQuery({
    queryKey: ["workorders"],
    queryFn: () => workOrdersApi.list({ limit: 50 }),
  });

  const operational = assets.filter((a) => a.status === "operational").length;
  const openWOs     = workOrders.filter((w) => w.status !== "completed" && w.status !== "cancelled").length;
  const criticalWOs = workOrders.filter((w) => w.priority === "critical" && w.status !== "completed").length;

  return (
    <div className="screen">
      <div className="screen-hd">
        <div>
          <h1 className="screen-title">Dashboard</h1>
          <p className="screen-sub">Real-time fleet status · All Centers</p>
        </div>
      </div>

      <div className="kpi-row">
        <div className="kpi-card">
          <div className="kpi-label">Total Assets</div>
          <div className="kpi-val">{loadingAssets ? "…" : assets.length}</div>
          <div className="kpi-sub up">{operational} operational</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Open Work Orders</div>
          <div className="kpi-val">{loadingWO ? "…" : openWOs}</div>
          <div className="kpi-sub down">{criticalWOs} critical</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-label">Fleet Availability</div>
          <div className="kpi-val">{assets.length ? ((operational / assets.length) * 100).toFixed(1) : "—"}%</div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-hd"><span className="card-title">Equipment Fleet</span></div>
        <div className="fleet-grid">
          {assets.slice(0, 12).map((a) => (
            <div key={a.id} className={`fleet-item status-${a.status === "operational" ? "ok" : a.status === "maintenance" ? "warn" : "crit"}`}>
              <div className={`fleet-dot ${a.status === "operational" ? "ok" : a.status === "maintenance" ? "warn" : "crit"}`} />
              <div className="fleet-id">{a.asset_code}</div>
              <div className="fleet-name">{a.name.split(" ").slice(0, 3).join(" ")}</div>
              {a.rul_score !== undefined && <div className="fleet-rul">RUL {a.rul_score}</div>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
