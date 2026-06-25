export default function AIAgentsScreen() {
  return (
    <div className="screen">
      <div className="screen-hd">
        <div>
          <h1 className="screen-title">AI Agents Control Center</h1>
          <p className="screen-sub">5 agents active · Kafka event bus</p>
        </div>
      </div>
      <div className="card">
        <p style={{color: "var(--text-2)", fontSize: 13}}>
          Screen implemented in <code>src/screens/AIAgentsScreen.tsx</code>. 
          Wire up with React Query hooks using the API client in <code>src/api/</code>.
        </p>
      </div>
    </div>
  );
}
