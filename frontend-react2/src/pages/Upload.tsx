import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload as UploadIcon, CheckCircle, AlertTriangle, X, ChevronRight, Sparkles, Database } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { datasetsApi } from '../api/client'
import { Layout, PageHeader } from '../components/layout/Layout'
import { Card, Button, Badge, Spinner, EmptyState, StatusBadge } from '../components/ui'
import { UploadResponse, Dataset } from '../types'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'

export function Upload() {
  const navigate = useNavigate()
  const [uploading, setUploading] = useState(false)
  const [result, setResult]       = useState<UploadResponse | null>(null)
  const [cleanConfig, setCleanConfig] = useState<Record<string, any>>({
    fill_missing: {}, remove_duplicates: false,
    fix_negative_columns: [], standardize_categories: []
  })
  const [cleaning, setCleaning] = useState(false)

  const { data: datasets, refetch } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => datasetsApi.list().then(r => r.data),
  })

  const onDrop = useCallback(async (files: File[]) => {
    const file = files[0]
    if (!file) return
    setUploading(true)
    setResult(null)
    try {
      const res = await datasetsApi.upload(file)
      setResult(res.data)
      refetch()
      toast.success(`"${file.name}" uploaded and profiled!`)
    } catch (err: any) {
      toast.error(err.response?.data?.message || 'Upload failed')
    } finally { setUploading(false) }
  }, [refetch])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop, accept: { 'text/csv': ['.csv'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] },
    maxFiles: 1, disabled: uploading,
  })

  const handleClean = async () => {
    if (!result) return
    setCleaning(true)
    try {
      await datasetsApi.clean(result.dataset.id, cleanConfig)
      toast.success('Data cleaned successfully!')
      refetch()
    } catch { toast.error('Cleaning failed') }
    finally { setCleaning(false) }
  }

  const issueIcon: Record<string, string> = {
    missing_values: '⚠️', duplicates: '🔁',
    negative_values: '➖', invalid_dates: '📅', inconsistent_categories: '🔤'
  }

  return (
    <Layout>
      <PageHeader title="Upload Data" subtitle="Upload CSV or Excel files to start your AI analysis." />

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          {/* Drop zone */}
          <div
            {...getRootProps()}
            className={clsx(
              'border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300',
              isDragActive
                ? 'border-accent-primary bg-accent-primary/5 shadow-glow'
                : 'border-bg-border hover:border-accent-primary/50 hover:bg-bg-card',
              uploading && 'opacity-60 cursor-not-allowed'
            )}
          >
            <input {...getInputProps()} />
            {uploading ? (
              <div className="flex flex-col items-center gap-4">
                <Spinner size="lg" />
                <div>
                  <p className="text-base font-medium text-text-primary">Analyzing your file...</p>
                  <p className="text-sm text-text-muted mt-1">Profiling columns, computing statistics, generating AI suggestions</p>
                </div>
              </div>
            ) : isDragActive ? (
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 rounded-2xl bg-accent-primary/10 flex items-center justify-center">
                  <UploadIcon className="w-8 h-8 text-accent-primary" />
                </div>
                <p className="text-base font-semibold text-accent-primary">Drop it here!</p>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-bg-card border border-bg-border flex items-center justify-center">
                  <UploadIcon className="w-8 h-8 text-text-muted" />
                </div>
                <div>
                  <p className="text-base font-semibold text-text-primary">Drag & drop your file here</p>
                  <p className="text-sm text-text-muted mt-1">or click to browse — CSV, XLSX up to 50MB</p>
                </div>
                <Button variant="secondary" size="sm">Browse files</Button>
              </div>
            )}
          </div>

          {/* Results */}
          {result && (
            <>
              {/* Stats */}
              <Card glow>
                <div className="flex items-center gap-3 mb-4">
                  <CheckCircle className="w-5 h-5 text-accent-success" />
                  <h3 className="font-semibold text-text-primary">{result.dataset.original_filename}</h3>
                  <StatusBadge status={result.dataset.status} />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  {[
                    ['Rows', result.dataset.row_count?.toLocaleString()],
                    ['Columns', result.dataset.col_count],
                    ['Issues', result.cleaning_report.total_issues],
                  ].map(([l, v]) => (
                    <div key={String(l)} className="bg-bg-secondary rounded-xl p-4 text-center">
                      <p className="text-2xl font-bold text-text-primary">{v}</p>
                      <p className="text-xs text-text-muted mt-1">{l}</p>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Cleaning report */}
              {result.cleaning_report.total_issues > 0 && (
                <Card>
                  <h3 className="font-semibold text-text-primary mb-4 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-accent-warning" />
                    Data Quality Issues — {result.cleaning_report.total_issues} found
                  </h3>
                  <div className="space-y-3">
                    {result.cleaning_report.issues.map((issue, i) => (
                      <div key={i} className="flex items-center gap-4 p-3 bg-bg-secondary rounded-xl">
                        <span className="text-lg flex-shrink-0">{issueIcon[issue.issue_type] ?? '❗'}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-text-primary">{issue.description}</p>
                        </div>
                        <select
                          className="bg-bg-card border border-bg-border rounded-lg px-3 py-1.5 text-xs text-text-primary flex-shrink-0"
                          defaultValue="skip"
                          onChange={e => {
                            const v = e.target.value
                            if (issue.issue_type === 'missing_values' && issue.column && v !== 'skip')
                              setCleanConfig(c => ({ ...c, fill_missing: { ...c.fill_missing, [issue.column!]: v } }))
                            if (issue.issue_type === 'duplicates' && v === 'remove_duplicates')
                              setCleanConfig(c => ({ ...c, remove_duplicates: true }))
                            if (issue.issue_type === 'inconsistent_categories' && issue.column && v !== 'skip')
                              setCleanConfig(c => ({ ...c, standardize_categories: [...c.standardize_categories, issue.column] }))
                          }}
                        >
                          {issue.fix_options.map(o => <option key={o} value={o}>{o.replace(/_/g, ' ')}</option>)}
                        </select>
                      </div>
                    ))}
                  </div>
                  <Button className="mt-4 w-full" onClick={handleClean} loading={cleaning}>
                    Apply Fixes
                  </Button>
                </Card>
              )}

              {/* AI Suggestions */}
              {result.suggestions?.length > 0 && (
                <Card>
                  <h3 className="font-semibold text-text-primary mb-4 flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-accent-primary" />
                    AI-Suggested Questions
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {result.suggestions.map((q, i) => (
                      <button key={i}
                        onClick={() => { localStorage.setItem('prefill_question', q); navigate('/chat') }}
                        className="flex items-center gap-2 px-3 py-2 bg-bg-secondary hover:bg-bg-hover border border-bg-border hover:border-accent-primary/40 rounded-xl text-sm text-text-secondary hover:text-text-primary transition-all">
                        {q} <ChevronRight className="w-3 h-3" />
                      </button>
                    ))}
                  </div>
                </Card>
              )}
            </>
          )}
        </div>

        {/* Right: previous uploads */}
        <div>
          <Card>
            <h3 className="font-semibold text-text-primary mb-4">Previous Uploads</h3>
            {datasets?.length ? (
              <div className="space-y-2">
                {datasets.map((ds: Dataset) => (
                  <div key={ds.id}
                    className="flex items-center gap-3 p-3 bg-bg-secondary rounded-xl hover:bg-bg-hover transition-colors cursor-pointer"
                    onClick={() => navigate('/chat')}>
                    <Database className="w-4 h-4 text-accent-primary flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-text-primary truncate">{ds.original_filename}</p>
                      <p className="text-xs text-text-muted">{ds.row_count?.toLocaleString()} rows</p>
                    </div>
                    <StatusBadge status={ds.status} />
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState icon={<Database className="w-6 h-6" />} title="No uploads yet" description="Upload your first file to get started." />
            )}
          </Card>
        </div>
      </div>
    </Layout>
  )
}
