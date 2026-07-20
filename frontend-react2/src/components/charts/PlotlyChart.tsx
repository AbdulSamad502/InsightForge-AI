import Plot from 'react-plotly.js'

interface Props {
  chartData: Record<string, any>
  height?: number
}

export function PlotlyChart({ chartData, height = 380 }: Props) {
  if (!chartData || !chartData.data) return null

  const darkLayout = {
    ...chartData.layout,
    height,
    paper_bgcolor: 'transparent',
    plot_bgcolor:  'transparent',
    font:         { family: 'Inter, sans-serif', color: '#94a3b8', size: 12 },
    title:        { ...chartData.layout?.title, font: { color: '#f1f5f9', size: 15 } },
    xaxis: {
      ...chartData.layout?.xaxis,
      gridcolor: '#1e1e35',
      linecolor: '#1e1e35',
      tickfont:  { color: '#94a3b8' },
      titlefont: { color: '#94a3b8' },
    },
    yaxis: {
      ...chartData.layout?.yaxis,
      gridcolor: '#1e1e35',
      linecolor: '#1e1e35',
      tickfont:  { color: '#94a3b8' },
      titlefont: { color: '#94a3b8' },
    },
    legend: { ...chartData.layout?.legend, font: { color: '#94a3b8' }, bgcolor: 'transparent' },
    margin: { t: 50, l: 50, r: 20, b: 50 },
    colorway: ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444'],
  }

  return (
    <Plot
      data={chartData.data}
      layout={darkLayout}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: '100%' }}
      useResizeHandler
    />
  )
}
