import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, Plus, Trash2, MessageSquare, Database, Sparkles } from 'lucide-react'
import { chatApi, datasetsApi } from '../api/client'
import { Layout, PageHeader } from '../components/layout/Layout'
import { Card, Button, Spinner, EmptyState } from '../components/ui'
import { ChatBubble } from '../components/chat/ChatMessage'
import { ChatMessage, ChatSession, Dataset } from '../types'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'

export function Chat() {
  const qc = useQueryClient()
  const bottomRef    = useRef<HTMLDivElement>(null)
  const inputRef     = useRef<HTMLInputElement>(null)
  const [sessionId, setSessionId]     = useState<string | null>(null)
  const [messages, setMessages]       = useState<ChatMessage[]>([])
  const [input, setInput]             = useState('')
  const [sending, setSending]         = useState(false)
  const [datasetId, setDatasetId]     = useState<string>('')

  // Pre-fill from upload page suggestion chips
  useEffect(() => {
    const q = localStorage.getItem('prefill_question')
    if (q) { setInput(q); localStorage.removeItem('prefill_question') }
  }, [])

  const { data: datasets } = useQuery<Dataset[]>({
    queryKey: ['datasets'],
    queryFn: () => datasetsApi.list().then(r => r.data),
  })

  const { data: sessions } = useQuery<ChatSession[]>({
    queryKey: ['sessions'],
    queryFn: () => chatApi.listSessions().then(r => r.data),
    refetchInterval: 10000,
  })

  // Auto-select first dataset
  useEffect(() => {
    if (datasets?.length && !datasetId) setDatasetId(datasets[0].id)
  }, [datasets])

  const createSession = async () => {
    if (!datasetId) { toast.error('Select a dataset first'); return }
    try {
      const res = await chatApi.createSession(datasetId)
      const id = res.data.id
      setSessionId(id)
      setMessages([])
      qc.invalidateQueries({ queryKey: ['sessions'] })
      toast.success('New chat started')
      inputRef.current?.focus()
    } catch { toast.error('Could not create session') }
  }

  const loadSession = async (id: string) => {
    try {
      const res = await chatApi.getSession(id)
      setSessionId(id)
      setMessages(res.data.messages || [])
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
    } catch { toast.error('Could not load session') }
  }

  const sendMessage = async () => {
    const msg = input.trim()
    if (!msg || sending) return
    if (!sessionId) { await createSession(); return }

    // Optimistic user message
    const tempMsg: ChatMessage = {
      id: Date.now().toString(), session_id: sessionId, role: 'user',
      content: msg, chart_data: null, insight: null, recommendation: null,
      intent_type: null, created_at: new Date().toISOString(),
    }
    setMessages(m => [...m, tempMsg])
    setInput('')
    setSending(true)
    setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)

    try {
      const res = await chatApi.sendMessage(sessionId, msg)
      const reply = res.data.message as ChatMessage
      setMessages(m => [...m, reply])
      qc.invalidateQueries({ queryKey: ['sessions'] })
    } catch (err: any) {
      const errMsg: ChatMessage = {
        id: (Date.now() + 1).toString(), session_id: sessionId, role: 'assistant',
        content: err.response?.data?.message || 'An error occurred. Please try again.',
        chart_data: null, insight: null, recommendation: null,
        intent_type: null, created_at: new Date().toISOString(),
      }
      setMessages(m => [...m, errMsg])
    } finally {
      setSending(false)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 100)
    }
  }

  const deleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await chatApi.deleteSession(id)
      if (sessionId === id) { setSessionId(null); setMessages([]) }
      qc.invalidateQueries({ queryKey: ['sessions'] })
      toast.success('Session deleted')
    } catch { toast.error('Could not delete session') }
  }

  const suggestions = ['What is total revenue by category?', 'Show top 10 products by sales', 'Are there any anomalies in the data?', 'What are the summary statistics?', 'Show revenue trend over time']

  return (
    <Layout>
      <PageHeader title="AI Chat" subtitle="Ask anything about your data in plain English." />

      <div className="flex gap-4 h-[calc(100vh-11rem)]">
        {/* Left sidebar: sessions */}
        <div className="w-64 flex-shrink-0 flex flex-col gap-3">
          {/* Dataset selector */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-text-muted uppercase tracking-wider">Dataset</label>
            <select
              value={datasetId}
              onChange={e => setDatasetId(e.target.value)}
              className="w-full bg-bg-card border border-bg-border rounded-lg px-3 py-2 text-sm text-text-primary"
            >
              {datasets?.map(d => <option key={d.id} value={d.id}>{d.original_filename}</option>)}
            </select>
          </div>

          <Button onClick={createSession} className="w-full">
            <Plus className="w-4 h-4" /> New Chat
          </Button>

          {/* Session list */}
          <div className="flex-1 overflow-y-auto space-y-1">
            {sessions?.map(s => (
              <div key={s.id}
                onClick={() => loadSession(s.id)}
                className={clsx(
                  'flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer group transition-all',
                  sessionId === s.id
                    ? 'bg-accent-primary/10 border border-accent-primary/20 text-accent-primary'
                    : 'hover:bg-bg-hover text-text-secondary hover:text-text-primary'
                )}>
                <MessageSquare className="w-3.5 h-3.5 flex-shrink-0" />
                <span className="text-xs truncate flex-1">{s.title || 'Untitled Chat'}</span>
                <button onClick={e => deleteSession(s.id, e)}
                  className="opacity-0 group-hover:opacity-100 hover:text-accent-danger transition-all">
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Main chat area */}
        <div className="flex-1 flex flex-col bg-bg-card border border-bg-border rounded-2xl overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {!sessionId ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <div className="w-16 h-16 rounded-2xl bg-gradient-primary flex items-center justify-center mb-4 shadow-glow">
                  <Sparkles className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-text-primary mb-2">Start a conversation</h3>
                <p className="text-sm text-text-muted mb-6 max-w-xs">Select a dataset, click "New Chat", and ask anything about your data.</p>
                <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                  {suggestions.map(s => (
                    <button key={s} onClick={() => setInput(s)}
                      className="px-3 py-1.5 bg-bg-secondary border border-bg-border rounded-full text-xs text-text-secondary hover:text-text-primary hover:border-accent-primary/40 transition-all">
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Database className="w-12 h-12 text-text-muted mb-3" />
                <p className="text-sm text-text-muted">Dataset loaded. Ask your first question!</p>
                <div className="flex flex-wrap gap-2 justify-center max-w-lg mt-4">
                  {suggestions.map(s => (
                    <button key={s} onClick={() => { setInput(s); inputRef.current?.focus() }}
                      className="px-3 py-1.5 bg-bg-secondary border border-bg-border rounded-full text-xs text-text-secondary hover:text-text-primary hover:border-accent-primary/40 transition-all">
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                {messages.map(msg => <ChatBubble key={msg.id} msg={msg} />)}
                {sending && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center flex-shrink-0">
                      <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <div className="chat-ai px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Spinner size="sm" />
                        <span className="text-sm text-text-muted">Analyzing your data...</span>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </>
            )}
          </div>

          {/* Input */}
          <div className="p-4 border-t border-bg-border">
            <div className="flex gap-3">
              <input
                ref={inputRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() } }}
                placeholder={sessionId ? "Ask anything about your data..." : "Create a new chat session first..."}
                disabled={sending}
                className="flex-1 bg-bg-secondary border border-bg-border rounded-xl px-4 py-3 text-sm text-text-primary placeholder-text-muted focus:border-accent-primary disabled:opacity-50"
              />
              <Button onClick={sendMessage} loading={sending} disabled={!input.trim() || !sessionId} size="lg" className="px-4">
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}
