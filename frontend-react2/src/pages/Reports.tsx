import { useState, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { FileText, Download, Plus, Clock, CheckCircle, XCircle, Loader2, AlertTriangle } from 'lucide-react'
import { reportsApi, datasetsApi } from '../api/client'
import { Layout, PageHeader } from '../components/layout/Layout'
import { Card, Button, Spinner, EmptyState } from '../components/ui'
import { Report, Dataset } from '../types'
import { formatDistanceToNow } from 'date-fns'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'

function ReportRow({ report, onDownload }: { report: Report; onDownload: (id: string) => void }) {
  const statusConfig: Record<string, { icon: any; color: string; label: string }> = {
    complete: { icon: CheckCircle, color: 'text-accent-success', label: 'Complete' },
    pending:  { icon: Clock,       color: 'text-accent-warning', label: 'Pending' },
    running:  { icon: Loader2,     color: 'text-accent-primary', label: 'Generating...' },
    failed:   { icon: XCircle,     color: 'text-accent-danger',  label: 'Failed' },
  }
  const cfg = statusConfig[report.status] ?? statusConfig.pending
  const StatusIcon = cfg.icon

  return (
    <div className="flex items-center gap-4 p-4 bg-bg-secondary rounded-xl hover:bg-bg-hover transition-all">
      <div className="w-10 h-10 rounded-xl bg-bg-card border border-bg-border flex items-center justify-center flex-shrink-0">
        <FileText className="w-5 h-5 text-accent-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-text-primary">
          Report <code className="text-xs text-text-muted font-mono">{report.id.slice(0, 12)}...</code>
        </p>
        <p className="text-xs text-text-muted mt-0.5">
          {formatDistanceToNow(new Date(report.created_at), { addSuffix: true })}
        </p>
        {report.error_message && (
          <p className="text-xs text-accent-danger mt-1 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" /> {report.error_message.slice(0, 80)}
          </p>
        )}
      </div>
      <div className={clsx('flex items-center gap-1.5 text-xs font-medium', cfg.color)}>
        <StatusIcon className={clsx('w-4 h-4', report.status === 'running' && 'animate-spin')} />
        {cfg.label}
      </div>
      {report.status === 'complete' && (
        <Button variant="secondary" size="sm" onClick={() => onDownload(report.id)}>
          <Download className="w-3.5 h-3.5" /> Download PDF
        </Button>
      )}
    </div>
  )
}

export function Reports() {
  const qc = useQueryClient()
  const [datasetId, setDatasetId]   = useState('')
  const [generating, setGenerating] = useState(false)
  const [activeIds, setActiveIds]   = useState<string[]>([])

  const { data: datasets } = useQuery<Dataset[]>({
    queryKey: ['datasets'],
    queryFn: () => datasetsApi.list().then(r => r.data),
  })

  const { data: reports, refetch } = useQuery<Report[]>({
    queryKey: ['reports'],
    queryFn: () => reportsApi.list().then(r => r.data),
    refetchInterval: activeIds.length ? 3000 : false,
  })

  useEffect(() => {
    if (datasets?.length && !datasetId) setDatasetId(datasets[0].id)
  }, [datasets])

  // Stop polling when active reports complete
  useEffect(() => {
    if (!reports || !activeIds.length) return
    const pendingIds = activeIds.filter(id => {
      const r = reports.find(rep => rep.id === id)
      return r && (r.status === 'pending' || r.status === 'running')
    })
    if (pendingIds.length < activeIds.length) {
      const completed = activeIds.filter(id => {
        const r = reports.find(rep => rep.id === id)
        return r?.status === 'complete'
      })
      if (completed.length) toast.success('Report ready! Click Download to save your PDF.')
    }
    setActiveIds(pendingIds)
  }, [reports])

  const generate = async () => {
    if (!datasetId) { toast.error('Select a dataset first'); return }
    setGenerating(true)
    try {
      const res = await reportsApi.generate(datasetId)
      const reportId = res.data.report_id
      setActiveIds(ids => [...ids, reportId])
      await refetch()
      toast.success('Report generation started! This takes 30-60 seconds.')
    } catch (err: any) {
      toast.error(err.response?.data?.message || 'Failed to start report generation')
    } finally { setGenerating(false) }
  }

  const download = async (id: string) => {
    try {
      const res = await reportsApi.download(id)
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `insightforge-report-${id.slice(0, 8)}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('PDF downloaded!')
    } catch { toast.error('Download failed') }
  }

  return (
    <Layout>
      <PageHeader
        title="Reports"
        subtitle="Generate professional PDF reports from your AI analysis."
        action={
          <Button onClick={generate} loading={generating}>
            <Plus className="w-4 h-4" /> Generate Report
          </Button>
        }
      />

      {/* Config */}
      <Card className="mb-6">
        <div className="flex flex-col sm:flex-row gap-4 items-end">
          <div className="flex-1">
            <label className="text-xs font-medium text-text-muted uppercase tracking-wider mb-2 block">
              Dataset for Report
            </label>
            <select value={datasetId} onChange={e => setDatasetId(e.target.value)}
              className="w-full bg-bg-secondary border border-bg-border rounded-xl px-4 py-2.5 text-sm text-text-primary">
              {datasets?.map(d => <option key={d.id} value={d.id}>{d.original_filename}</option>)}
            </select>
          </div>
          <Button onClick={generate} loading={generating} size="lg">
            <Plus className="w-4 h-4" /> Generate Report
          </Button>
        </div>

        {activeIds.length > 0 && (
          <div className="mt-4 flex items-center gap-3 p-3 bg-accent-primary/5 border border-accent-primary/10 rounded-xl">
            <Spinner size="sm" />
            <div>
              <p className="text-sm font-medium text-text-primary">Generating your report...</p>
              <p className="text-xs text-text-muted">
                Gathering insights → exporting charts → writing summary → compiling PDF.
                This takes 30-90 seconds.
              </p>
            </div>
          </div>
        )}

        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            ['📊', 'AI Insights', 'From your chat history'],
            ['📈', 'ML Results',  'Forecast & anomaly data'],
            ['📉', 'Charts',      'Top 5 visualizations'],
            ['📄', '7-Section PDF', 'Professional layout'],
          ].map(([icon, title, desc]) => (
            <div key={String(title)} className="bg-bg-secondary rounded-xl p-3 text-center">
              <p className="text-lg mb-1">{icon}</p>
              <p className="text-xs font-semibold text-text-primary">{title}</p>
              <p className="text-xs text-text-muted">{desc}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Reports list */}
      <div className="space-y-3">
        {reports === undefined ? (
          <div className="flex justify-center py-12"><Spinner size="lg" /></div>
        ) : reports.length === 0 ? (
          <Card>
            <EmptyState
              icon={<FileText className="w-8 h-8" />}
              title="No reports yet"
              description="Generate your first AI-powered business intelligence report."
              action={
                <Button onClick={generate} loading={generating}>
                  <Plus className="w-4 h-4" /> Generate Report
                </Button>
              }
            />
          </Card>
        ) : (
          reports.map(r => <ReportRow key={r.id} report={r} onDownload={download} />)
        )}
      </div>
    </Layout>
  )
}
