import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, Upload, MessageSquare, BarChart3, FileText, LogOut, Cpu, Zap } from 'lucide-react'
import { clsx } from 'clsx'
import { useAuth } from '../../store/auth'

const NAV = [
  { to: '/',        icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/upload',  icon: Upload,          label: 'Upload'    },
  { to: '/chat',    icon: MessageSquare,   label: 'AI Chat'   },
  { to: '/ml',      icon: BarChart3,       label: 'ML Models' },
  { to: '/reports', icon: FileText,        label: 'Reports'   },
]

export function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/login') }

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-bg-secondary border-r border-bg-border flex flex-col z-40">
      {/* Logo */}
      <div className="px-6 py-6 border-b border-bg-border">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow-sm">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-bold gradient-text">InsightForge</h1>
            <p className="text-xs text-text-muted">AI Analytics</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
              isActive
                ? 'bg-accent-primary/10 text-accent-primary border border-accent-primary/20'
                : 'text-text-secondary hover:text-text-primary hover:bg-bg-hover'
            )}
          >
            <Icon className="w-4 h-4 flex-shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* LLM Status */}
      <div className="px-4 py-3 mx-3 mb-2 bg-bg-card rounded-lg border border-bg-border">
        <div className="flex items-center gap-2 mb-1">
          <Cpu className="w-3.5 h-3.5 text-accent-success" />
          <span className="text-xs font-medium text-text-secondary">AI Engine</span>
        </div>
        <p className="text-xs text-accent-success font-mono">● Groq / Ollama</p>
      </div>

      {/* User */}
      <div className="p-4 border-t border-bg-border">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
            {user?.full_name?.[0]?.toUpperCase() ?? 'U'}
          </div>
          <div className="overflow-hidden">
            <p className="text-sm font-medium text-text-primary truncate">{user?.full_name}</p>
            <p className="text-xs text-text-muted truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-text-muted hover:text-accent-danger hover:bg-accent-danger/5 transition-all"
        >
          <LogOut className="w-4 h-4" />
          Sign out
        </button>
      </div>
    </aside>
  )
}
