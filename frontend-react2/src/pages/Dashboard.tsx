import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Upload, MessageSquare, FileText, Brain, Database, Clock, ArrowRight, TrendingUp } from 'lucide-react'
import { dashboardApi } from '../api/client'
import { Layout, PageHeader } from '../components/layout/Layout'
import { Card, Button, Spinner, StatusBadge } from '../components/ui'
import { useAuth } from '../store/auth'
import { formatDistanceToNow } from 'date-fns'

function KPICard({ icon: Icon, label, value, color }: { icon: any; label: string; value: number; color: string }) {
  return (
    <Card className="relative overflow-hidden group hover:border-accent-primary/30 transition-all duration-300">
      <div className={`absolute top-0 right-0 w-24 h-24 rounded-full opacity-5 -translate-y-6 translate-x-6 ${color}`} />
      <div className={`inline-flex p-2.5 rounded-xl ${color} bg-opacity-10 mb-4`}>
        <Icon className="w-5 h-5" />
      </div>
      <p className="text-3xl font-bold text-text-primary mb-1">{value.toLocaleString()}</p>
      <p className="text-sm text-text-muted">{label}</p>
    </Card>
  )
}

export function Dashboard() {
  const { user }  = useAuth()
  const navigate  = useNavigate()
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: () => dashboardApi.summary().then(r => r.data),
    refetchInterval: 30000,
  })

  const kpis = [
    { icon: Database,     label: 'Datasets',      value: data?.kpis?.total_datasets  ?? 0, color: 'text-accent-primary bg-accent-primary' },
    { icon: MessageSquare,label: 'Chat Sessions',  value: data?.kpis?.total_chats     ?? 0, color: 'text-accent-secondary bg-accent-secondary' },
    { icon: TrendingUp,   label: 'Questions Asked',value: data?.kpis?.total_messages  ?? 0, color: 'text-accent-cyan bg-accent-cyan' },
    { icon: FileText,     label: 'Reports Generated',value: data?.kpis?.total_reports ?? 0, color: 'text-accent-success bg-accent-success' },
    { icon: Brain,        label: 'ML Models Run',  value: data?.kpis?.total_ml_runs   ?? 0, color: 'text-accent-warning bg-accent-warning' },
  ]

  return (
    <Layout>
      <PageHeader
        title={`Welcome back, ${user?.full_name?.split(' ')[0]} 👋`}
        subtitle="Here's what's happening with your data today."
        action={
          <Button onClick={() => navigate('/upload')}>
            <Upload className="w-4 h-4" /> Upload Data
          </Button>
        }
      />

      {isLoading ? (
        <div className="flex items-center justify-center h-64"><Spinner size="lg" /></div>
      ) : (
        <div className="space-y-8">
          {/* KPI grid */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            {kpis.map(k => <KPICard key={k.label} {...k} />)}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Recent Datasets */}
            <Card className="lg:col-span-1">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-text-primary">Recent Datasets</h3>
                <Button variant="ghost" size="sm" onClick={() => navigate('/upload')}>
                  View all <ArrowRight className="w-3 h-3" />
                </Button>
              </div>
              {data?.recent_datasets?.length ? (
                <div className="space-y-3">
                  {data.recent_datasets.map((ds: any) => (
                    <div key={ds.id} className="flex items-center gap-3 p-3 bg-bg-secondary rounded-lg hover:bg-bg-hover transition-colors cursor-pointer"
                      onClick={() => navigate('/upload')}>
                      <div className="w-8 h-8 rounded-lg bg-accent-primary/10 flex items-center justify-center flex-shrink-0">
                        <Database className="w-4 h-4 text-accent-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-text-primary truncate">{ds.filename}</p>
                        <p className="text-xs text-text-muted">{ds.row_count?.toLocaleString()} rows</p>
                      </div>
                      <StatusBadge status={ds.status} />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Database className="w-8 h-8 text-text-muted mx-auto mb-2" />
                  <p className="text-sm text-text-muted">No datasets yet</p>
                  <Button variant="secondary" size="sm" className="mt-3" onClick={() => navigate('/upload')}>
                    Upload your first file
                  </Button>
                </div>
              )}
            </Card>

            {/* Recent Chats */}
            <Card className="lg:col-span-1">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-text-primary">Recent Chats</h3>
                <Button variant="ghost" size="sm" onClick={() => navigate('/chat')}>
                  Open chat <ArrowRight className="w-3 h-3" />
                </Button>
              </div>
              {data?.recent_sessions?.length ? (
                <div className="space-y-3">
                  {data.recent_sessions.map((s: any) => (
                    <div key={s.id}
                      className="p-3 bg-bg-secondary rounded-lg hover:bg-bg-hover transition-colors cursor-pointer"
                      onClick={() => navigate('/chat')}>
                      <p className="text-sm text-text-primary truncate">{s.title || 'Untitled Chat'}</p>
                      <div className="flex items-center gap-1 mt-1">
                        <Clock className="w-3 h-3 text-text-muted" />
                        <span className="text-xs text-text-muted">
                          {formatDistanceToNow(new Date(s.created_at), { addSuffix: true })}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <MessageSquare className="w-8 h-8 text-text-muted mx-auto mb-2" />
                  <p className="text-sm text-text-muted">No chats yet</p>
                  <Button variant="secondary" size="sm" className="mt-3" onClick={() => navigate('/chat')}>
                    Start chatting
                  </Button>
                </div>
              )}
            </Card>

            {/* Quick Actions */}
            <Card className="lg:col-span-1">
              <h3 className="font-semibold text-text-primary mb-4">Quick Actions</h3>
              <div className="space-y-2">
                {[
                  { label: 'Upload new dataset', icon: Upload, to: '/upload', color: 'text-accent-primary' },
                  { label: 'Ask AI a question',  icon: MessageSquare, to: '/chat',   color: 'text-accent-secondary' },
                  { label: 'Run ML forecast',    icon: Brain,    to: '/ml',     color: 'text-accent-warning' },
                  { label: 'Generate report',    icon: FileText, to: '/reports', color: 'text-accent-success' },
                ].map(a => (
                  <button key={a.label}
                    onClick={() => navigate(a.to)}
                    className="flex items-center gap-3 w-full p-3 rounded-lg bg-bg-secondary hover:bg-bg-hover transition-all text-left group">
                    <a.icon className={`w-4 h-4 ${a.color} flex-shrink-0`} />
                    <span className="text-sm text-text-secondary group-hover:text-text-primary transition-colors">{a.label}</span>
                    <ArrowRight className="w-3 h-3 text-text-muted ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                  </button>
                ))}
              </div>
            </Card>
          </div>
        </div>
      )}
    </Layout>
  )
}
