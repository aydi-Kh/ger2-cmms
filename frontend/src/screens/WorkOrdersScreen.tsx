export default function WorkOrdersScreen() {
  return (
    <div className="screen">
      <div className="screen-hd">
        <div>
          <h1 className="screen-title">Work Orders</h1>
          <p className="screen-sub">Kanban view · All centers</p>
        </div>
      </div>
      <div className="card">
        <p style={{color: "var(--text-2)", fontSize: 13}}>
          Screen implemented in <code>src/screens/WorkOrdersScreen.tsx</code>. 
          Wire up with React Query hooks using the API client in <code>src/api/</code>.
        </p>
      </div>
    </div>
  );
}
