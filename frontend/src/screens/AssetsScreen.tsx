export default function AssetsScreen() {
  return (
    <div className="screen">
      <div className="screen-hd">
        <div>
          <h1 className="screen-title">Asset Management</h1>
          <p className="screen-sub">Equipment registry · Lifecycle tracking</p>
        </div>
      </div>
      <div className="card">
        <p style={{color: "var(--text-2)", fontSize: 13}}>
          Screen implemented in <code>src/screens/AssetsScreen.tsx</code>. 
          Wire up with React Query hooks using the API client in <code>src/api/</code>.
        </p>
      </div>
    </div>
  );
}
