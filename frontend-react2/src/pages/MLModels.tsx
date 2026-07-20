import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Brain, TrendingUp, AlertTriangle, Users, Play, Clock, CheckCircle, XCircle } from 'lucide-react'
import { mlApi, datasetsApi } from '../api/client'
import { Layout, PageHeader } from '../components/layout/Layout'
import { Card, Button, Input, Spinner, Badge } from '../components/ui'
import { PlotlyChart } from '../components/charts/PlotlyChart'
import { Dataset, MLResult } from '../types'
import toast from 'react-hot-toast'

type ModelType = 'forecast' | 'anomaly' | 'churn'

function MLCard({ type, icon: Icon, title, description, color, onRun, loading }: {
  type: ModelType; icon: any; title: string; description: string
  color: string; onRun: (col: string, periods?: number) => void; loading: boolean
}) {
  const [col, setCol]         = useState('')
  const [periods, setPeriods] = useState(3)
  return (
    <Card className="hover:border-accent-primary/20 transition-all">
      <div className={`inline-flex p-2.5 rounded-xl ${color} bg-opacity-10 mb-4`}>
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <h3 className="font-semibold text-text-primary mb-1">{title}</h3>
      <p className="text-sm text-text-muted mb-4">{description}</p>
      <Input
        placeholder="Target column (e.g. revenue)"
        value={col}
        onChange={e => setCol(e.target.value)}
        className="mb-3"
      />
      {type === 'forecast' && (
        <div className="mb-3">
          <label className="text-xs text-text-muted mb-1 block">Periods to forecast: {periods}</label>
          <input type="range" min={1} max={12} value={periods}
            onChange={e => setPeriods(+e.target.value)}
            className="w-full accent-accent-primary" />
        </div>
      )}
      <Button
        className="w-full" loading={loading} disabled={!col.trim()}
        onClick={() => col.trim() && onRun(col.trim(), type === 'forecast' ? periods : undefined)}
      >
        <Play className="w-4 h-4" /> Run {title}
      </Button>
    </Card>
  )
}

function ResultCard({ result }: { result: MLResult }) {
  const [open, setOpen] = useState(false)
  const icons: Record<string, any> = { forecast: TrendingUp, anomaly: AlertTriangle, churn: Users }
  const Icon = icons[result.model_type] ?? Brain

  const statusIcon = result.status === 'complete'
    ? <CheckCircle className="w-4 h-4 text-accent-success" />
    : result.status === 'failed'
      ? <XCircle className="w-4 h-4 text-accent-danger" />
      : <Clock className="w-4 h-4 text-accent-warning animate-pulse" />

  const data = result.result_data || {}

  return (
    <Card className="hover:border-accent-primary/20 transition-all">
      <div className="flex items-center gap-3 mb-3">
        <Icon className="w-4 h-4 text-accent-primary" />
        <span className="font-medium text-text-primary capitalize">{result.model_type}</span>
        <span className="text-text-muted text-sm">on <code className="text-accent-cyan text-xs">{result.target_column}</code></span>
        <div className="ml-auto flex items-center gap-2">{statusIcon}
          <span className="text-xs text-text-muted capitalize">{result.status}</span>
        </div>
      </div>

      {result.status === 'complete' && (
        <>
          {/* Summary row */}
          <div className="grid grid-cols-3 gap-3 mb-3">
            {result.model_type === 'forecast' && [
              ['MAE', data.mae?.toLocaleString() ?? '—'],
              ['R²', data.r2_score?.toFixed(3) ?? '—'],
              ['Periods', data.dates?.length ?? '—'],
            ].map(([l, v]) => (
              <div key={String(l)} className="bg-bg-secondary rounded-lg p-2 text-center">
                <p className="text-sm font-bold text-text-primary">{v}</p>
                <p className="text-xs text-text-muted">{l}</p>
              </div>
            ))}
            {result.model_type === 'anomaly' && [
              ['Anomalies', data.anomaly_count ?? '—'],
              ['%', `${data.anomaly_pct ?? '—'}%`],
              ['Total', data.total_count ?? '—'],
            ].map(([l, v]) => (
              <div key={String(l)} className="bg-bg-secondary rounded-lg p-2 text-center">
                <p className="text-sm font-bold text-text-primary">{v}</p>
                <p className="text-xs text-text-muted">{l}</p>
              </div>
            ))}
            {result.model_type === 'churn' && [
              ['Accuracy', `${((data.accuracy ?? 0) * 100).toFixed(1)}%`],
              ['High Risk', (data.top_at_risk_customers ?? []).filter((c: any) => c.risk_level === 'High').length],
              ['Features', data.feature_importance?.length ?? '—'],
            ].map(([l, v]) => (
              <div key={String(l)} className="bg-bg-secondary rounded-lg p-2 text-center">
                <p className="text-sm font-bold text-text-primary">{v}</p>
                <p className="text-xs text-text-muted">{l}</p>
              </div>
            ))}
          </div>

          {/* Chart toggle */}
          {result.chart_data && (
            <button onClick={() => setOpen(o => !o)}
              className="text-xs text-accent-primary hover:underline mb-2 block">
              {open ? 'Hide chart ▲' : 'Show chart ▼'}
            </button>
          )}
          {open && result.chart_data && <PlotlyChart chartData={result.chart_data} height={280} />}

          {/* Forecast table */}
          {result.model_type === 'forecast' && data.dates?.length && (
            <div className="mt-2 space-y-1">
              {data.dates.map((d: string, i: number) => (
                <div key={d} className="flex items-center justify-between text-xs p-2 bg-bg-secondary rounded-lg">
                  <span className="text-text-muted">{d}</span>
                  <span className="font-mono font-medium text-text-primary">{data.predictions?.[i]?.toLocaleString()}</span>
                  <span className="text-text-muted">
                    {data.lower_ci?.[i]?.toLocaleString()} – {data.upper_ci?.[i]?.toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
      {result.status === 'failed' && (
        <p className="text-xs text-accent-danger bg-accent-danger/5 border border-accent-danger/20 rounded-lg p-2">
          {result.error_message || 'Task failed'}
        </p>
      )}
    </Card>
  )
}

export function MLModels() {
  const [datasetId, setDatasetId] = useState('')
  const [taskIds, setTaskIds]     = useState<string[]>([])
  const [activeLoading, setActiveLoading] = useState<ModelType | null>(null)
  const [results, setResults]     = useState<MLResult[]>([])

  const { data: datasets } = useQuery<Dataset[]>({
    queryKey: ['datasets'],
    queryFn: () => datasetsApi.list().then(r => r.data),
  })

  useEffect(() => {
    if (datasets?.length && !datasetId) setDatasetId(datasets[0].id)
  }, [datasets])

  // Poll for task results
  useEffect(() => {
    if (!taskIds.length) return
    const interval = setInterval(async () => {
      const updates = await Promise.all(taskIds.map(id => mlApi.getResult(id).then(r => r.data)))
      setResults(prev => {
        const map = new Map(prev.map(r => [r.id, r]))
        updates.forEach(u => map.set(u.id, u))
        return Array.from(map.values())
      })
      const allDone = updates.every(u => u.status === 'complete' || u.status === 'failed')
      if (allDone) { setTaskIds([]); setActiveLoading(null) }
    }, 2000)
    return () => clearInterval(interval)
  }, [taskIds])

  const run = async (type: ModelType, col: string, periods?: number) => {
    if (!datasetId) { toast.error('Select a dataset first'); return }
    setActiveLoading(type)
    try {
      let res
      if (type === 'forecast') res = await mlApi.forecast(datasetId, col, periods)
      else if (type === 'anomaly') res = await mlApi.anomaly(datasetId, col)
      else res = await mlApi.churn(datasetId, col)
      const taskId = res.data.task_id
      setTaskIds(ids => [...ids, taskId])
      // Add pending result immediately
      setResults(prev => [{
        id: taskId, model_type: type, target_column: col,
        status: 'pending', result_data: null, chart_data: null,
        error_message: null, created_at: new Date().toISOString(), completed_at: null
      }, ...prev])
      toast.success(`${type} model started! Polling for results...`)
    } catch (err: any) {
      toast.error(err.response?.data?.message || 'Failed to start model')
      setActiveLoading(null)
    }
  }

  const models: { type: ModelType; icon: any; title: string; description: string; color: string }[] = [
    { type: 'forecast', icon: TrendingUp,    title: 'Forecast',  color: 'text-accent-primary',
      description: 'Predict future values using GradientBoosting with confidence intervals.' },
    { type: 'anomaly',  icon: AlertTriangle, title: 'Anomaly',   color: 'text-accent-warning',
      description: 'Detect unusual values using IQR + IsolationForest.' },
    { type: 'churn',    icon: Users,         title: 'Churn',     color: 'text-accent-danger',
      description: 'Predict customer churn risk using RandomForest classifier.' },
  ]

  return (
    <Layout>
      <PageHeader title="ML Models" subtitle="Train machine learning models on your data." />

      {/* Dataset selector */}
      <div className="mb-6 flex items-center gap-4">
        <div className="w-72">
          <label className="text-xs text-text-muted mb-1 block uppercase tracking-wider">Active Dataset</label>
          <select value={datasetId} onChange={e => setDatasetId(e.target.value)}
            className="w-full bg-bg-card border border-bg-border rounded-xl px-4 py-2.5 text-sm text-text-primary">
            {datasets?.map(d => <option key={d.id} value={d.id}>{d.original_filename}</option>)}
          </select>
        </div>
        {taskIds.length > 0 && (
          <div className="flex items-center gap-2 text-sm text-accent-warning">
            <Spinner size="sm" /> Running {taskIds.length} model(s)...
          </div>
        )}
      </div>

      {/* Model cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-8">
        {models.map(m => (
          <MLCard key={m.type} {...m}
            loading={activeLoading === m.type}
            onRun={(col, periods) => run(m.type, col, periods)} />
        ))}
      </div>

      {/* Results */}
      {results.length > 0 && (
        <>
          <h2 className="text-lg font-semibold text-text-primary mb-4">Results</h2>
          <div className="space-y-4">
            {results.map(r => <ResultCard key={r.id} result={r} />)}
          </div>
        </>
      )}
    </Layout>
  )
}
