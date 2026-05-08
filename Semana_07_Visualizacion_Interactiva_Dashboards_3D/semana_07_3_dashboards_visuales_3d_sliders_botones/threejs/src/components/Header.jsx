import './Header.css'

export default function Header() {
  return (
    <header className="app-header">
      <div className="header-content">
        <h1>🎨 3D Visual Dashboard</h1>
        <p>Interactive Real-Time 3D Scene Controls</p>
      </div>
      <div className="header-info">
        <span className="info-badge">React Three Fiber</span>
        <span className="info-badge">Leva Controls</span>
        <span className="info-badge">Three.js</span>
      </div>
    </header>
  )
}
