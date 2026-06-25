export default function CostsScreen() {
  return (
    <div className="screen">
      <div className="screen-hd">
        <div>
          <h1 className="screen-title">Cost Management</h1>
          <p className="screen-sub">MTD spend · TCO dashboard</p>
        </div>
      </div>
      <div className="card">
        <p style={{color: "var(--text-2)", fontSize: 13}}>
          Screen implemented in <code>src/screens/CostsScreen.tsx</code>. 
          Wire up with React Query hooks using the API client in <code>src/api/</code>.
        </p>
      </div>
    </div>
  );
}
