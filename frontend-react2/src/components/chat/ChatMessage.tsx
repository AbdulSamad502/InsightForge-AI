import { useState } from 'react'
import { Lightbulb, TrendingUp, ChevronDown, ChevronUp, Bot, User } from 'lucide-react'
import { ChatMessage as Msg } from '../../types'
import { PlotlyChart } from '../charts/PlotlyChart'
import { Button } from '../ui'
import { vizApi } from '../../api/client'
import { formatDistanceToNow } from 'date-fns'

export function ChatBubble({ msg }: { msg: Msg }) {
  const [explanation, setExplanation] = useState<string | null>(null)
  const [explaining, setExplaining] = useState(false)
  const [showInsight, setShowInsight] = useState(true)

  const isUser = msg.role === 'user'

  const handleExplain = async () => {
    if (!msg.chart_data) return
    setExplaining(true)
    try {
      const layout = msg.chart_data.layout || {}
      const title = typeof layout.title === 'string' ? layout.title : layout.title?.text || ''
      const res = await vizApi.explain('bar', 'x', 'y', msg.content.slice(0, 300))
      setExplanation(res.data.explanation)
    } catch { setExplanation('Could not generate explanation.') }
    finally { setExplaining(false) }
  }

  if (isUser) {
    return (
      <div className="flex justify-end gap-3 animate-slide-up">
        <div className="max-w-[70%]">
          <div className="chat-user px-4 py-3 text-sm text-white">{msg.content}</div>
          <p className="text-xs text-text-muted mt-1 text-right">
            {formatDistanceToNow(new Date(msg.created_at), { addSuffix: true })}
          </p>
        </div>
        <div className="w-8 h-8 rounded-full bg-accent-primary/20 border border-accent-primary/30 flex items-center justify-center flex-shrink-0 mt-1">
          <User className="w-4 h-4 text-accent-primary" />
        </div>
      </div>
    )
  }

  return (
    <div className="flex gap-3 animate-slide-up">
      <div className="w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center flex-shrink-0 mt-1 shadow-glow-sm">
        <Bot className="w-4 h-4 text-white" />
      </div>
      <div className="max-w-[85%] space-y-3">
        {/* Main text */}
        <div className="chat-ai px-4 py-3">
          <p className="text-sm text-text-primary leading-relaxed whitespace-pre-wrap">{msg.content}</p>
        </div>

        {/* Chart */}
        {msg.chart_data && (
          <div className="bg-bg-card border border-bg-border rounded-xl p-4">
            <PlotlyChart chartData={msg.chart_data} height={320} />
            <div className="mt-2 flex gap-2">
              <Button
                variant="ghost"
                size="sm"
                loading={explaining}
                onClick={handleExplain}
                className="text-xs text-text-muted"
              >
                🔍 Explain this chart
              </Button>
            </div>
            {explanation && (
              <div className="mt-2 p-3 bg-accent-primary/5 border border-accent-primary/10 rounded-lg text-xs text-text-secondary">
                {explanation}
              </div>
            )}
          </div>
        )}

        {/* Insight */}
        {msg.insight && (
          <div className="insight-box px-4 py-3">
            <button
              onClick={() => setShowInsight(s => !s)}
              className="flex items-center gap-2 w-full text-left"
            >
              <Lightbulb className="w-3.5 h-3.5 text-accent-success flex-shrink-0" />
              <span className="text-xs font-semibold text-accent-success">Business Insight</span>
              {showInsight ? <ChevronUp className="w-3 h-3 text-text-muted ml-auto" /> : <ChevronDown className="w-3 h-3 text-text-muted ml-auto" />}
            </button>
            {showInsight && <p className="text-xs text-text-secondary mt-2 leading-relaxed">{msg.insight}</p>}
          </div>
        )}

        {/* Recommendation */}
        {msg.recommendation && (
          <div className="recommendation-box px-4 py-3">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-3.5 h-3.5 text-accent-warning flex-shrink-0" />
              <span className="text-xs font-semibold text-accent-warning">Recommendation</span>
            </div>
            <p className="text-xs text-text-secondary leading-relaxed">{msg.recommendation}</p>
          </div>
        )}

        {/* Meta */}
        <div className="flex items-center gap-2">
          {msg.intent_type && msg.intent_type !== 'general' && (
            <span className="text-xs font-mono text-text-muted bg-bg-card border border-bg-border px-2 py-0.5 rounded">
              {msg.intent_type}
            </span>
          )}
          <span className="text-xs text-text-muted">
            {formatDistanceToNow(new Date(msg.created_at), { addSuffix: true })}
          </span>
        </div>
      </div>
    </div>
  )
}
