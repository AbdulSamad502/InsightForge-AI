import { ReactNode, ButtonHTMLAttributes, InputHTMLAttributes } from 'react'
import { clsx } from 'clsx'
import { Loader2 } from 'lucide-react'

// ── Button ─────────────────────────────────────────────────
interface BtnProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  children: ReactNode
}

export function Button({ variant = 'primary', size = 'md', loading, children, className, disabled, ...p }: BtnProps) {
  const base = 'inline-flex items-center justify-center gap-2 font-medium rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed'
  const variants = {
    primary:   'bg-gradient-primary text-white hover:opacity-90 shadow-glow-sm hover:shadow-glow',
    secondary: 'bg-bg-card border border-bg-border text-text-primary hover:bg-bg-hover hover:border-accent-primary',
    ghost:     'text-text-secondary hover:text-text-primary hover:bg-bg-hover',
    danger:    'bg-accent-danger/10 border border-accent-danger/30 text-accent-danger hover:bg-accent-danger hover:text-white',
  }
  const sizes = { sm: 'px-3 py-1.5 text-sm', md: 'px-4 py-2 text-sm', lg: 'px-6 py-3 text-base' }
  return (
    <button className={clsx(base, variants[variant], sizes[size], className)} disabled={disabled || loading} {...p}>
      {loading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  )
}

// ── Card ───────────────────────────────────────────────────
export function Card({ children, className, glow }: { children: ReactNode; className?: string; glow?: boolean }) {
  return (
    <div className={clsx(
      'bg-bg-card border border-bg-border rounded-xl p-6 shadow-card',
      glow && 'shadow-glow-sm border-accent-primary/20',
      className
    )}>
      {children}
    </div>
  )
}

// ── Input ──────────────────────────────────────────────────
interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  icon?: ReactNode
}

export function Input({ label, error, icon, className, ...p }: InputProps) {
  return (
    <div className="space-y-1.5">
      {label && <label className="block text-sm font-medium text-text-secondary">{label}</label>}
      <div className="relative">
        {icon && <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">{icon}</div>}
        <input
          className={clsx(
            'w-full bg-bg-secondary border border-bg-border rounded-lg py-2.5 text-sm text-text-primary placeholder-text-muted transition-all',
            icon ? 'pl-10 pr-4' : 'px-4',
            error ? 'border-accent-danger' : 'focus:border-accent-primary',
            className
          )}
          {...p}
        />
      </div>
      {error && <p className="text-xs text-accent-danger">{error}</p>}
    </div>
  )
}

// ── Badge ──────────────────────────────────────────────────
type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info'
export function Badge({ children, variant = 'default' }: { children: ReactNode; variant?: BadgeVariant }) {
  const v: Record<BadgeVariant, string> = {
    default: 'bg-bg-border text-text-secondary',
    success: 'bg-accent-success/10 text-accent-success border border-accent-success/20',
    warning: 'bg-accent-warning/10 text-accent-warning border border-accent-warning/20',
    danger:  'bg-accent-danger/10 text-accent-danger border border-accent-danger/20',
    info:    'bg-accent-primary/10 text-accent-primary border border-accent-primary/20',
  }
  return <span className={clsx('inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', v[variant])}>{children}</span>
}

// ── Spinner ────────────────────────────────────────────────
export function Spinner({ size = 'md', className }: { size?: 'sm' | 'md' | 'lg'; className?: string }) {
  const s = { sm: 'w-4 h-4', md: 'w-6 h-6', lg: 'w-8 h-8' }
  return <Loader2 className={clsx('animate-spin text-accent-primary', s[size], className)} />
}

// ── Empty State ────────────────────────────────────────────
export function EmptyState({ icon, title, description, action }: {
  icon: ReactNode; title: string; description: string; action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-16 h-16 rounded-2xl bg-bg-card border border-bg-border flex items-center justify-center text-text-muted mb-4">{icon}</div>
      <h3 className="text-base font-semibold text-text-primary mb-1">{title}</h3>
      <p className="text-sm text-text-muted max-w-xs mb-4">{description}</p>
      {action}
    </div>
  )
}

// ── Status Badge ───────────────────────────────────────────
export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeVariant> = {
    complete: 'success', complete2: 'success',
    pending: 'warning', running: 'info', failed: 'danger',
    uploaded: 'info', profiled: 'success', cleaned: 'success',
  }
  return <Badge variant={map[status] ?? 'default'}>{status}</Badge>
}
