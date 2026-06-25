export default function LoginScreen() {
  return (
    <div className="screen">
      <div className="screen-hd">
        <div>
          <h1 className="screen-title">GER2 CMMS Login</h1>
          
        </div>
      </div>
      <div className="card">
        <p style={{color: "var(--text-2)", fontSize: 13}}>
          Screen implemented in <code>src/screens/LoginScreen.tsx</code>. 
          Wire up with React Query hooks using the API client in <code>src/api/</code>.
        </p>
      </div>
    </div>
  );
}
