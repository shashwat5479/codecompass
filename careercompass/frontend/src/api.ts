export type SessionUser = {
  id: number
  name: string
  email: string
  role: 'job_seeker' | 'recruiter' | 'admin' | string
}

export type Job = {
  id: number
  title: string
  company: string
  location: string
  salary_range: string
  employment_type: string
  experience: string
  description: string
  required_skills: string
  work_mode: string
  is_active: boolean
}

export type RoadmapPhase = {
  phase: string
  topics: string[]
  estimated_time: string
}

export type ScoreComponent = {
  key: string
  label: string
  score: number
  weight: number
  points: number
}

export type PartialSkill = {
  skill: string
  coverage: number
  via: string | null
  kind: 'implied' | 'related' | string
}

export type CareerRecommendation = {
  title: string
  rank?: number
  category?: string
  salary_range?: string
  demand?: string
  difficulty_level?: string
  description?: string
  score: number
  match_percentage?: number
  readiness?: string
  confidence?: 'High' | 'Medium' | 'Low' | string
  required_coverage?: number
  estimated_weeks_to_ready?: number
  score_breakdown?: ScoreComponent[]
  not_scored?: Array<{ key: string; label: string }>
  matching_skills: string[]
  partial_skills?: PartialSkill[]
  resume_matching_skills: string[]
  required_skills: string[]
  recommended_skills: string[]
  missing_skills: string[]
  missing_recommended_skills?: string[]
  explanation: string
  suggested_projects: string[]
  learning_resources: string[]
  recommended_certifications: string[]
  related_jobs: string[]
  next_steps: string[]
  career_roadmap: Array<{ title: string; description: string }>
  roadmap_phases?: RoadmapPhase[]
}

export type RecommendationInsights = {
  best_fit: string | null
  best_fit_score: number | null
  top_skills_to_learn: Array<{ skill: string; unlocks: string[]; impact: number }>
  profile_strength: { score: number; label: string; tips: string[] }
}

export type JobRecommendation = {
  job_id: number
  title: string
  company?: string
  location: string
  salary_range: string
  employment_type: string
  work_mode: string
  experience: string
  description: string
  required_skills: string[]
  preferred_skills?: string[]
  match_score: number
  match_percentage: number
  readiness?: string
  already_applied?: boolean
  resume_matched_skills: string[]
  all_matched_skills: string[]
  partial_skills?: PartialSkill[]
  missing_skills: string[]
  score_breakdown?: ScoreComponent[]
  reasons?: string[]
  matched_career?: string | null
}

export type CustomRoadmap = {
  job_title: string
  fit_score: number
  matched_skills: string[]
  partial_skills?: PartialSkill[]
  missing_skills: string[]
  all_required_skills: string[]
  suggested_projects: string[]
  suggested_certifications: string[]
  estimated_weeks?: number
  roadmap: Array<{ step: number; title: string; description: string; estimated_timeline: string }>
}

export type CommunityComment = {
  id: number
  post_id: number
  user_id: number
  author: string
  author_role?: string
  content: string
  parent_id?: number | null
  created_at: string
}

export type CommunityPost = {
  id: number
  user_id: number
  author: string
  author_role?: string
  title: string
  content: string
  category: string
  tags: string
  created_at: string
  likes_count?: number
  user_liked?: boolean
  comments_count: number
}

export type Application = {
  id: number
  job_id: number
  job_title?: string
  applicant_name?: string
  applicant_email?: string
  status: string
  submitted_at: string
  cover_letter?: string
  notes?: string
}

export type LoginResponse = {
  access_token: string
  token_type: string
  user: SessionUser
}

const SESSION_KEY = 'careercompass_session'
const listeners = new Set<() => void>()

export function getSession(): LoginResponse | null {
  const raw = localStorage.getItem(SESSION_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as LoginResponse
  } catch {
    return null
  }
}

export function setSession(session: LoginResponse | null): void {
  if (session) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session))
  } else {
    localStorage.removeItem(SESSION_KEY)
  }
  listeners.forEach((listener) => listener())
}

export function subscribeToSession(callback: () => void): () => void {
  listeners.add(callback)
  return () => {
    listeners.delete(callback)
  }
}

export async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const session = getSession()
  const headers = new Headers(options.headers || {})
  if (!headers.has('Content-Type') && options.body && typeof options.body === 'string') {
    headers.set('Content-Type', 'application/json')
  }
  if (!headers.has('Authorization') && session?.access_token) {
    headers.set('Authorization', `Bearer ${session.access_token}`)
  }

  const response = await fetch(endpoint, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let message = 'Request failed'
    try {
      const payload = await response.json()
      message = payload.detail || payload.message || message
    } catch {
      // Keep default message
    }
    throw new Error(message)
  }

  return response.json() as Promise<T>
}

export async function downloadFile(endpoint: string, fallbackName: string): Promise<void> {
  const session = getSession()
  const headers = new Headers()
  if (session?.access_token) {
    headers.set('Authorization', `Bearer ${session.access_token}`)
  }

  const response = await fetch(endpoint, { headers })
  if (!response.ok) {
    throw new Error('Failed to download file')
  }

  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = fallbackName
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}

export function jsonBody(data: unknown): string {
  return JSON.stringify(data)
}
