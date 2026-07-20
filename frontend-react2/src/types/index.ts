export interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface Dataset {
  id: string
  original_filename: string
  stored_filename: string
  file_type: string
  status: string
  row_count: number | null
  col_count: number | null
  created_at: string
  profile?: DatasetProfile
}

export interface ColumnMetadata {
  name: string
  dtype: string
  null_count: number
  null_pct: number
  unique_count: number
  sample_values: any[]
}

export interface DatasetProfile {
  id: string
  dataset_id: string
  columns_metadata: ColumnMetadata[]
  statistics: Record<string, any>
  null_summary: Record<string, number>
  sample_questions: string[] | null
  profiled_at: string
}

export interface CleaningIssue {
  issue_type: string
  column: string | null
  description: string
  count: number
  fix_options: string[]
}

export interface CleaningReport {
  dataset_id: string
  total_issues: number
  issues: CleaningIssue[]
  has_duplicates: boolean
  duplicate_count: number
}

export interface UploadResponse {
  dataset: Dataset
  cleaning_report: CleaningReport
  suggestions: string[]
}

export interface ChatMessage {
  id: string
  session_id: string
  role: 'user' | 'assistant'
  content: string
  chart_data: Record<string, any> | null
  insight: string | null
  recommendation: string | null
  intent_type: string | null
  created_at: string
}

export interface ChatSession {
  id: string
  user_id: string
  dataset_id: string | null
  title: string | null
  created_at: string
  updated_at: string
  messages: ChatMessage[]
}

export interface MLResult {
  id: string
  model_type: string
  target_column: string | null
  status: string
  result_data: Record<string, any> | null
  chart_data: Record<string, any> | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface Report {
  id: string
  dataset_id: string
  status: string
  file_path: string | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export interface DashboardKPIs {
  total_datasets: number
  total_chats: number
  total_messages: number
  total_reports: number
  total_ml_runs: number
}

export interface DashboardSummary {
  kpis: DashboardKPIs
  recent_datasets: any[]
  recent_sessions: any[]
  recent_reports: any[]
  recent_ml_results: any[]
}
