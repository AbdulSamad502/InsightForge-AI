import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Zap, Mail, Lock, User, ArrowRight, BarChart3 } from 'lucide-react'
import { authApi } from '../api/client'
import { useAuth } from '../store/auth'
import { Button, Input } from '../components/ui'
import toast from 'react-hot-toast'

export function Login() {
  const [tab, setTab]         = useState<'login' | 'register'>('login')
  const [loading, setLoading] = useState(false)
  const [form, setForm]       = useState({ email: '', password: '', full_name: '' })
  const { login }             = useAuth()
  const navigate              = useNavigate()

  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(f => ({ ...f, [k]: e.target.value }))

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = tab === 'login'
        ? await authApi.login(form.email, form.password)
        : await authApi.register(form.email, form.full_name, form.password)
      login(res.data.access_token, res.data.user)
      toast.success(`Welcome${tab === 'register' ? ', ' + res.data.user.full_name : ' back'}!`)
      navigate('/')
    } catch (err: any) {
      toast.error(err.response?.data?.message || 'Something went wrong')
    } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen bg-bg-primary flex overflow-hidden">
      {/* Left panel */}
      <div className="hidden lg:flex flex-col w-1/2 bg-bg-secondary relative p-12 border-r border-bg-border">
        {/* Background glow */}
        <div className="absolute inset-0 bg-gradient-glow opacity-60 pointer-events-none" />

        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-16">
            <div className="w-10 h-10 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow">
              <Zap className="w-6 h-6 text-white" />
            </div>
            <span className="text-xl font-bold gradient-text">InsightForge AI</span>
          </div>

          <h2 className="text-4xl font-bold text-text-primary leading-tight mb-6">
            Turn your data into{' '}
            <span className="gradient-text">strategic intelligence</span>
          </h2>
          <p className="text-text-secondary text-lg leading-relaxed mb-12">
            Upload any CSV or Excel file. Ask questions in plain English.
            Get charts, forecasts, and professional reports — instantly.
          </p>

          {/* Feature list */}
          {[
            { icon: '📊', title: 'Natural Language Analysis', desc: 'Ask anything about your data' },
            { icon: '🤖', title: 'ML Forecasting',            desc: 'Predict revenue, detect anomalies' },
            { icon: '📄', title: 'AI-Generated Reports',      desc: 'Professional PDF in one click' },
          ].map(f => (
            <div key={f.title} className="flex items-start gap-4 mb-6">
              <div className="w-10 h-10 rounded-lg bg-bg-card border border-bg-border flex items-center justify-center text-lg flex-shrink-0">
                {f.icon}
              </div>
              <div>
                <p className="text-sm font-semibold text-text-primary">{f.title}</p>
                <p className="text-sm text-text-muted">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Bottom stats */}
        <div className="relative z-10 mt-auto grid grid-cols-3 gap-4">
          {[['Free', 'Local LLM'], ['Unlimited', 'Queries'], ['1-click', 'PDF Reports']].map(([v, l]) => (
            <div key={l} className="bg-bg-card border border-bg-border rounded-xl p-4 text-center">
              <p className="text-xl font-bold gradient-text">{v}</p>
              <p className="text-xs text-text-muted mt-1">{l}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden flex items-center gap-2 justify-center mb-8">
            <div className="w-9 h-9 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow-sm">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold gradient-text">InsightForge AI</span>
          </div>

          <div className="bg-bg-card border border-bg-border rounded-2xl p-8 shadow-card">
            {/* Tabs */}
            <div className="flex rounded-lg bg-bg-secondary p-1 mb-8">
              {(['login', 'register'] as const).map(t => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`flex-1 py-2 text-sm font-medium rounded-md transition-all capitalize ${
                    tab === t
                      ? 'bg-accent-primary text-white shadow-glow-sm'
                      : 'text-text-muted hover:text-text-primary'
                  }`}
                >
                  {t === 'login' ? 'Sign In' : 'Create Account'}
                </button>
              ))}
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {tab === 'register' && (
                <Input
                  label="Full Name"
                  placeholder="Abdul Samad"
                  value={form.full_name}
                  onChange={set('full_name')}
                  required
                  icon={<User className="w-4 h-4" />}
                />
              )}
              <Input
                label="Email"
                type="email"
                placeholder="you@company.com"
                value={form.email}
                onChange={set('email')}
                required
                icon={<Mail className="w-4 h-4" />}
              />
              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                value={form.password}
                onChange={set('password')}
                required
                minLength={6}
                icon={<Lock className="w-4 h-4" />}
              />

              <Button type="submit" loading={loading} size="lg" className="w-full mt-2">
                {tab === 'login' ? 'Sign In' : 'Create Account'}
                <ArrowRight className="w-4 h-4" />
              </Button>
            </form>

            <p className="text-center text-xs text-text-muted mt-6">
              {tab === 'login' ? "Don't have an account?" : 'Already have an account?'}{' '}
              <button onClick={() => setTab(tab === 'login' ? 'register' : 'login')}
                className="text-accent-primary hover:underline">
                {tab === 'login' ? 'Create one' : 'Sign in'}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
