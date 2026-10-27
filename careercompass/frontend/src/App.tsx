import { JobRoadmapModal } from './JobRoadmapModal'
import { JobApplicationModal, type JobApplyTarget } from './JobApplicationModal'
import { type FormEvent, useEffect, useState } from 'react'
import { BrowserRouter, NavLink, Route, Routes, useNavigate, useLocation } from 'react-router-dom'
import { apiRequest, downloadFile, getSession, jsonBody, setSession, subscribeToSession, type Application, type CareerRecommendation, type JobRecommendation, type RecommendationInsights, type ScoreComponent, type CommunityPost, type CommunityComment, type Job, type LoginResponse } from './api'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  ArrowRight,
  BriefcaseBusiness,
  Building2,
  CheckCircle2,
  Compass,
  FileText,
  GraduationCap,
  MapPin,
  MessageSquare,
  Search,
  ShieldCheck,
  Sparkles,
  Star,
  Target,
  Trash2,
  Users,
  Heart,
  Send,
  TrendingUp,
  DollarSign,
  Tag,
} from 'lucide-react'

const stats = [
  { label: 'Available Jobs', value: '2,450+', icon: BriefcaseBusiness },
  { label: 'Registered Companies', value: '340', icon: Building2 },
  { label: 'Active Job Seekers', value: '18,700', icon: Users },
  { label: 'Successful Applications', value: '9,420', icon: CheckCircle2 },
]

const careerPaths = [
  'Data Analyst',
  'Software Developer',
  'Frontend Developer',
  'Cybersecurity Analyst',
  'Machine Learning Engineer',
  'Product Manager',
]

const roadmap = [
  'Excel & statistics foundations',
  'SQL & Python for analysis',
  'Power BI / Tableau storytelling',
  'Portfolio projects and case studies',
  'Resume & interview preparation',
]

const recommendationData = [
  { month: 'Jan', value: 46 },
  { month: 'Feb', value: 62 },
  { month: 'Mar', value: 58 },
  { month: 'Apr', value: 81 },
  { month: 'May', value: 76 },
  { month: 'Jun', value: 88 },
]

const navItems = [
  { label: 'Home', to: '/' },
  { label: 'Explore Jobs', to: '/jobs' },
  { label: 'Career Paths', to: '/careers' },
  { label: 'Community', to: '/community' },
  { label: 'About', to: '/about' },
]

function AppShell({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [session, setCurrentSession] = useState(getSession)
  useEffect(() => subscribeToSession(() => setCurrentSession(getSession())), [])

  // Dynamic Document Title Updater for Every Page
  useEffect(() => {
    const titles: Record<string, string> = {
      '/': 'CareerCompass AI | AI-Powered Career Platform & Job Matching',
      '/jobs': 'Explore Jobs & Required Skills Roadmaps | CareerCompass AI',
      '/careers': 'Career Paths & Skill Gap Analysis | CareerCompass AI',
      '/community': 'Community Discussions & Career Mentorship | CareerCompass AI',
      '/about': 'About CareerCompass AI | Our Mission & Platform',
      '/dashboard': 'Candidate Dashboard & Resume Manager | CareerCompass AI',
      '/recruiter-dashboard': 'Recruiter Portal & Hiring Pipeline | CareerCompass AI',
      '/admin-dashboard': 'Admin Control Center & Operations | CareerCompass AI',
      '/recruiter/jobs/new': 'Post a New Job Opportunity | CareerCompass AI',
      '/auth': 'Sign In / Register | CareerCompass AI',
    }
    document.title = titles[location.pathname] || 'CareerCompass AI | Career Guidance & Job Matching'
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [location.pathname])

  const homeForRole = session?.user.role === 'recruiter'
    ? '/recruiter-dashboard'
    : session?.user.role === 'admin'
      ? '/admin-dashboard'
      : '/dashboard'

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-badge">CC</div>
          <div>
            <div className="brand-name">CareerCompass AI</div>
          </div>
        </div>
        <nav className="main-nav" aria-label="Main navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              {item.label}
            </NavLink>
          ))}
          {session ? (
            <NavLink to={homeForRole} className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
              Dashboard
            </NavLink>
          ) : (
            <NavLink to="/auth" className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
              Login
            </NavLink>
          )}
        </nav>
        <div className="nav-actions">
          {session ? (
            <>
              <span className="nav-user">{session.user.name}</span>
              <button type="button" className="secondary-btn small" onClick={() => { setSession(null); navigate('/auth') }}>Log out</button>
            </>
          ) : (
            <NavLink to="/auth" className="primary-btn">Get Started</NavLink>
          )}
        </div>
      </header>
      {children}
      <footer className="site-footer">
        <div>
          <div className="brand-name">CareerCompass AI</div>
          <p>Career guidance, job discovery, and hiring support designed for modern professionals.</p>
        </div>
        <div>
          <h4>Company</h4>
          <NavLink to="/about">About CareerCompass</NavLink>
          <NavLink to="/auth">Create an account</NavLink>
        </div>
        <div>
          <h4>Explore</h4>
          <NavLink to="/jobs">Jobs</NavLink>
          <NavLink to="/careers">Career Paths</NavLink>
          <NavLink to="/community">Community</NavLink>
        </div>
        <div>
          <h4>Connect</h4>
          <p>Connect with learners and professionals in the community.</p>
          <NavLink to="/community">Visit the community</NavLink>
        </div>
      </footer>
    </div>
  )
}

function LandingPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [posts, setPosts] = useState<CommunityPost[]>([])
  useEffect(() => {
    apiRequest<Job[]>('/api/jobs').then((data) => setJobs(data.slice(0, 3))).catch(() => setJobs([]))
    apiRequest<CommunityPost[]>('/api/community/posts').then((data) => setPosts(data.slice(0, 3))).catch(() => setPosts([]))
  }, [])

  return (
    <main>
      <section className="hero-section">
        <div className="hero-copy">
          <div className="eyebrow">
            <SparklesIcon />
            Future-ready career support
          </div>
          <h1>Discover Your Potential. Find Your Career.</h1>
          <p>
            Get personalized career recommendations, discover opportunities that match your skills,
            and take the next step toward your professional future.
          </p>
          <div className="cta-row">
            <NavLink to="/auth" className="primary-btn large">
              Find My Career <ArrowRight size={18} />
            </NavLink>
            <NavLink to="/jobs" className="secondary-btn large">
              Explore Jobs
            </NavLink>
          </div>
          <div className="mini-proof">
            <div>
              <strong>14k+</strong>
              <span>Profiles tracked</span>
            </div>
            <div>
              <strong>94%</strong>
              <span>Career fit satisfaction</span>
            </div>
          </div>
        </div>
        <div className="hero-visual" aria-label="Dashboard preview">
          <div className="dashboard-card main-card">
            <div className="card-header">
              <span className="dot blue" />
              <span className="dot green" />
              <span className="dot amber" />
            </div>
            <div className="dashboard-widget">
              <div className="widget-title">Career Fit</div>
              <div className="metric">89%</div>
              <div className="progress-bar"><span style={{ width: '89%' }} /></div>
            </div>
            <div className="widget-grid">
              {['Data Analyst', 'UX Research', 'Product Analyst'].map((item) => (
                <div className="tag" key={item}>{item}</div>
              ))}
            </div>
            <div className="chart-mini">
              <ResponsiveContainer width="100%" height={110}>
                <AreaChart data={recommendationData}>
                  <defs>
                    <linearGradient id="areaGlow" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="#5b7cff" stopOpacity={0.4} />
                      <stop offset="100%" stopColor="#5b7cff" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <Area type="monotone" dataKey="value" stroke="#5b7cff" strokeWidth={3} fill="url(#areaGlow)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </section>

      <section className="stats-section">
        {stats.map(({ label, value, icon: Icon }) => (
          <div className="stat-card" key={label}>
            <div className="stat-icon"><Icon size={18} /></div>
            <div>
              <strong>{value}</strong>
              <span>{label}</span>
            </div>
          </div>
        ))}
      </section>

      <section className="content-section">
        <div className="section-heading">
          <span className="section-kicker">How it works</span>
          <h2>Four steps to your next career move</h2>
        </div>
        <div className="steps-grid">
          {[
            ['Create Your Profile', 'Share your interests, skills, and education to build an accurate profile.'],
            ['Analyze Your Skills', 'Use your strengths and resume details to reveal where you stand out.'],
            ['Discover Career Matches', 'Receive explainable recommendations tailored to your goals.'],
            ['Apply for Opportunities', 'Track jobs and applications from one dashboard.'],
          ].map(([title, text], index) => (
            <div className="info-card" key={title}>
              <div className="step-index">0{index + 1}</div>
              <h3>{title}</h3>
              <p>{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="content-section">
        <div className="section-heading split">
          <div>
            <span className="section-kicker">Featured jobs</span>
            <h2>Opportunities that match your goals</h2>
          </div>
          <NavLink to="/jobs" className="text-link">View all jobs</NavLink>
        </div>
        <div className="job-grid">
          {jobs.map((job) => (
            <div className="job-card" key={job.id}>
              <div className="job-topline">
                <span className="employer">{job.company}</span>
                <span className="badge">{job.employment_type}</span>
              </div>
              <h3>{job.title}</h3>
              <div className="meta-row">
                <span><MapPin size={15} /> {job.location}</span>
                <span>{job.salary_range}</span>
              </div>
              <NavLink to="/jobs" className="secondary-btn small">View and apply</NavLink>
            </div>
          ))}
          {!jobs.length ? <div className="empty-state">No job listings yet. Check back soon.</div> : null}
        </div>
      </section>

      <section className="content-section">
        <div className="section-heading split">
          <div>
            <span className="section-kicker">Popular careers</span>
            <h2>Top pathways students explore</h2>
          </div>
        </div>
        <div className="pill-list">
          {careerPaths.map((path) => (
            <div className="pill" key={path}>{path}</div>
          ))}
        </div>
      </section>

      <section className="content-section">
        <div className="section-heading split">
          <div>
            <span className="section-kicker">Community</span>
            <h2>Advice from learners and professionals</h2>
          </div>
        </div>
        <div className="community-grid">
          {posts.map((post) => (
            <div className="community-card" key={post.id}>
              <div className="community-head">
                <span className="pill soft">{post.category}</span>
                <span className="mini-stat"><MessageSquare size={14} /> {post.comments_count}</span>
              </div>
              <h3>{post.title}</h3>
              <p>By {post.author}</p>
            </div>
          ))}
          {!posts.length ? <div className="empty-state">Join the community and start the first conversation.</div> : null}
        </div>
      </section>

      <section className="testimonials-section">
        <div className="section-heading">
          <span className="section-kicker">Testimonials</span>
          <h2>Students and recruiters trust the platform</h2>
        </div>
        <div className="testimonial-grid">
          {[
            'CareerCompass helped me discover my path in data analytics. The recommendations felt practical and transparent.',
            'The job matches and dashboard kept us organized while hiring for multiple internship roles.',
          ].map((quote, index) => (
            <div className="testimonial-card" key={quote}>
              <div className="stars"><Star size={16} fill="currentColor" /> <Star size={16} fill="currentColor" /> <Star size={16} fill="currentColor" /> <Star size={16} fill="currentColor" /> <Star size={16} fill="currentColor" /></div>
              <p>“{quote}”</p>
              <strong>{index === 0 ? 'Meera K.' : 'Rohit S.'}</strong>
            </div>
          ))}
        </div>
      </section>
    </main>
  )
}

function JobsPage() {
  const session = getSession()
  const role = session?.user.role
  const sessionToken = session?.access_token
  const [jobs, setJobs] = useState<Job[]>([])
  const [recommendedJobs, setRecommendedJobs] = useState<JobRecommendation[]>([])
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('All')
  const [activeTab, setActiveTab] = useState<'all' | 'recommended'>('all')
  const [savedIds, setSavedIds] = useState<number[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [roadmapModal, setRoadmapModal] = useState<{ title: string; skills?: string; id?: number } | null>(null)

  useEffect(() => {
    let cancelled = false
    const params = new URLSearchParams()
    if (query.trim()) params.set('q', query.trim())
    apiRequest<Job[]>(`/api/jobs${params.size ? `?${params.toString()}` : ''}`)
      .then((data) => { if (!cancelled) { setJobs(data); setError('') } })
      .catch((reason: Error) => { if (!cancelled) setError(reason.message) })
      .finally(() => { if (!cancelled) setLoading(false) })

    if (role === 'job_seeker') {
      apiRequest<{ job_id: number }[]>('/api/jobs/saved')
        .then((rows) => { if (!cancelled) setSavedIds(rows.map((row) => row.job_id)) })
        .catch(() => { if (!cancelled) setSavedIds([]) })

      apiRequest<JobRecommendation[]>('/api/recommendations/jobs')
        .then((data) => { if (!cancelled) setRecommendedJobs(data) })
        .catch(() => {})
    }
    return () => { cancelled = true }
  }, [query, sessionToken, role])

  const filteredJobs = jobs.filter((job) => {
    if (filter === 'Remote' || filter === 'Hybrid') return job.work_mode?.toLowerCase() === filter.toLowerCase()
    if (filter === 'Freshers') return /0\s*[-–]\s*2|fresher|entry/i.test(job.experience || '')
    if (filter === 'Internships') return /intern/i.test(job.employment_type || '')
    return true
  })

  const saveJob = async (job: { id: number; title: string }) => {
    if (getSession()?.user.role !== 'job_seeker') {
      setNotice('Sign in as a job seeker to save jobs.')
      return
    }
    try {
      await apiRequest(`/api/jobs/${job.id}/save`, { method: 'POST' })
      setSavedIds((ids) => ids.includes(job.id) ? ids : [...ids, job.id])
      setNotice(`${job.title} saved to your list.`)
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : 'Could not save this job.')
    }
  }

  const [applyModalJob, setApplyModalJob] = useState<JobApplyTarget | null>(null)

  const handleApplyClick = (job: JobApplyTarget) => {
    if (getSession()?.user.role !== 'job_seeker') {
      setNotice('Sign in as a job seeker to apply for jobs.')
      return
    }
    setApplyModalJob(job)
  }

  return (
    <main className="page-shell">
      <div className="page-head">
        <div>
          <span className="section-kicker">Explore opportunities</span>
          <h1>Find your dream role & acquire the exact skills needed</h1>
        </div>
        <div className="search-box">
          <Search size={16} />
          <input
            value={query}
            onChange={(event) => { setLoading(true); setQuery(event.target.value) }}
            type="search"
            placeholder="Search by title, required skills, or company"
            aria-label="Search jobs"
          />
        </div>
      </div>

      <div className="tabs-nav-bar">
        <button
          type="button"
          className={activeTab === 'all' ? 'tab-nav-btn active' : 'tab-nav-btn'}
          onClick={() => setActiveTab('all')}
        >
          All Available Jobs ({jobs.length})
        </button>
        {role === 'job_seeker' ? (
          <button
            type="button"
            className={activeTab === 'recommended' ? 'tab-nav-btn active' : 'tab-nav-btn'}
            onClick={() => setActiveTab('recommended')}
          >
            ★ Recommended For You (Resume Match)
          </button>
        ) : null}
      </div>

      <div className="filter-row">
        {['All', 'Remote', 'Hybrid', 'Freshers', 'Internships'].map((item) => (
          <button
            key={item}
            type="button"
            className={filter === item ? 'filter-chip active' : 'filter-chip'}
            onClick={() => setFilter(item)}
          >
            {item}
          </button>
        ))}
      </div>

      {error ? <div className="state-message error-message">{error}</div> : null}
      {notice ? (
        <div className="state-message">
          {notice}
          <button type="button" aria-label="Dismiss message" onClick={() => setNotice('')}>×</button>
        </div>
      ) : null}
      {loading ? <div className="state-message">Loading available jobs…</div> : null}

      {activeTab === 'recommended' && role === 'job_seeker' ? (
        <div className="job-list">
          {recommendedJobs.length === 0 ? (
            <div className="empty-state">
              Upload your resume in the Dashboard or add profile skills to view personalized job recommendations.
            </div>
          ) : null}
          {recommendedJobs.map((item) => (
            <div className="list-card highlight" key={item.job_id}>
              <div>
                <div className="job-topline">
                  <span className="employer">{item.company || 'Matched for your profile'}</span>
                  <span className="badge">{item.employment_type}</span>
                  {item.readiness ? <span className="badge">{item.readiness}</span> : null}
                  {item.already_applied ? <span className="badge">Applied</span> : null}
                  <span className="match-pill">{item.match_percentage}% Match</span>
                </div>
                <h3>{item.title}</h3>
                <p>{item.location} · {item.salary_range} · {item.experience} · {item.work_mode}</p>
                <p className="job-description">{item.description}</p>
                {item.reasons?.length ? (
                  <ul className="match-reasons">
                    {item.reasons.slice(0, 4).map((reason) => <li key={reason}>{reason}</li>)}
                  </ul>
                ) : null}
                <ScoreBreakdown items={item.score_breakdown} label="Why this match?" />

                <div className="job-skills-wrap">
                  {item.required_skills.map((skill) => {
                    const partial = item.partial_skills?.find((p) => p.skill.toLowerCase() === skill.toLowerCase())
                    const isResumeMatched = item.resume_matched_skills.some((s) => s.toLowerCase() === skill.toLowerCase())
                    const isAllMatched = item.all_matched_skills.some((s) => s.toLowerCase() === skill.toLowerCase())
                    return (
                      <span
                        key={skill}
                        className={`skill-tag-pill ${isResumeMatched || isAllMatched ? 'matched' : partial ? 'partial' : 'missing'}`}
                        title={isResumeMatched ? 'Detected in Resume' : isAllMatched ? 'In Profile Skills' : partial ? `Likely covered via ${partial.via}` : 'Skill Gap'}
                      >
                        {isResumeMatched ? '✓ In Resume: ' : isAllMatched ? '✓ Profile: ' : partial ? `≈ ${partial.coverage}%: ` : 'Gap: '}{skill}
                      </span>
                    )
                  })}
                </div>
              </div>

              <div className="card-actions">
                <button
                  type="button"
                  className="secondary-btn small roadmap-cta-btn"
                  onClick={() => setRoadmapModal({ title: item.title, skills: item.required_skills.join(', '), id: item.job_id })}
                >
                  <Compass size={15} /> Skills Roadmap
                </button>
                <button
                  type="button"
                  className="secondary-btn small"
                  onClick={() => void saveJob({ id: item.job_id, title: item.title })}
                >
                  {savedIds.includes(item.job_id) ? 'Saved' : 'Save'}
                </button>
                <button
                  type="button"
                  className="primary-btn small"
                  onClick={() => handleApplyClick({ id: item.job_id, title: item.title, location: item.location, salary_range: item.salary_range })}
                >
                  Apply
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="job-list">
          {!loading && filteredJobs.length === 0 ? (
            <div className="empty-state">No jobs match this search. Try a different title or filter.</div>
          ) : null}
          {filteredJobs.map((job) => (
            <div className="list-card" key={job.id}>
              <div>
                <div className="job-topline">
                  <span className="employer">{job.company}</span>
                  <span className="badge">{job.employment_type}</span>
                </div>
                <h3>{job.title}</h3>
                <p>{job.location} · {job.salary_range} · {job.experience} · {job.work_mode}</p>
                <p className="job-description">{job.description}</p>
                {job.required_skills ? (
                  <div className="job-skills-wrap">
                    {job.required_skills.split(',').map((s) => (
                      <span key={s.trim()} className="skill-tag-pill">
                        {s.trim()}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>

              <div className="card-actions">
                <button
                  type="button"
                  className="secondary-btn small roadmap-cta-btn"
                  onClick={() => setRoadmapModal({ title: job.title, skills: job.required_skills, id: job.id })}
                >
                  <Compass size={15} /> Required Skills & Roadmap
                </button>
                <button
                  type="button"
                  className="secondary-btn small"
                  onClick={() => void saveJob(job)}
                >
                  {savedIds.includes(job.id) ? 'Saved' : 'Save'}
                </button>
                <button
                  type="button"
                  className="primary-btn small"
                  onClick={() => handleApplyClick({ id: job.id, title: job.title, company: job.company, location: job.location, salary_range: job.salary_range })}
                >
                  Apply
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {roadmapModal ? (
        <JobRoadmapModal
          jobTitle={roadmapModal.title}
          requiredSkills={roadmapModal.skills}
          jobId={roadmapModal.id}
          onClose={() => setRoadmapModal(null)}
        />
      ) : null}

      {applyModalJob ? (
        <JobApplicationModal
          job={applyModalJob}
          onClose={() => setApplyModalJob(null)}
          onSuccess={(msg) => setNotice(msg)}
        />
      ) : null}
    </main>
  )
}

function ScoreBreakdown({ items, label = 'How this score is calculated' }: { items?: ScoreComponent[]; label?: string }) {
  if (!items || items.length === 0) return null
  return (
    <details className="score-breakdown">
      <summary>{label}</summary>
      <div className="breakdown-rows">
        {items.map((item) => (
          <div className="breakdown-row" key={item.key}>
            <span className="breakdown-label">{item.label}</span>
            <div className="progress-bar breakdown-bar" aria-label={`${item.label}: ${item.score}%`}>
              <span style={{ width: `${item.score}%` }} />
            </div>
            <span className="breakdown-value">{item.score}% <small>· weight {item.weight}%</small></span>
          </div>
        ))}
      </div>
    </details>
  )
}

function CareerPage() {
  const session = getSession()
  const role = session?.user.role
  const [recommendations, setRecommendations] = useState<CareerRecommendation[]>([])
  const [resumeSkills, setResumeSkills] = useState<string[]>([])
  const [insights, setInsights] = useState<RecommendationInsights | null>(null)
  const [loading, setLoading] = useState(role === 'job_seeker')
  const [error, setError] = useState('')
  const [customGoal, setCustomGoal] = useState('')
  const [customSkills, setCustomSkills] = useState('')
  const [selectedRoadmap, setSelectedRoadmap] = useState<{ title: string; skills?: string } | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('All')
  const [searchFilter, setSearchFilter] = useState('')

  useEffect(() => {
    if (role !== 'job_seeker') return
    let cancelled = false
    apiRequest<CareerRecommendation[]>('/api/recommendations')
      .then((items) => { if (!cancelled) setRecommendations(items) })
      .catch((reason: Error) => { if (!cancelled) setError(reason.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    apiRequest<RecommendationInsights>('/api/recommendations/insights')
      .then((data) => { if (!cancelled) setInsights(data) })
      .catch(() => { /* insights are optional */ })
    apiRequest<{ skills: string[] }>('/api/resumes/analyze')
      .then((resume) => { if (!cancelled) setResumeSkills(resume.skills) })
      .catch((reason: Error) => {
        if (!cancelled && reason.message !== 'No resume uploaded') setError(reason.message)
      })
    return () => { cancelled = true }
  }, [role, session?.access_token])

  const handleCustomRoadmap = (e: FormEvent) => {
    e.preventDefault()
    if (!customGoal.trim()) return
    setSelectedRoadmap({ title: customGoal.trim(), skills: customSkills.trim() })
  }

  const categories = ['All', ...Array.from(new Set(recommendations.map(r => r.category).filter(Boolean) as string[]))]

  const filteredRecommendations = recommendations.filter((career) => {
    const matchesCategory = selectedCategory === 'All' || career.category === selectedCategory
    const q = searchFilter.toLowerCase().trim()
    const matchesSearch = !q ||
      career.title.toLowerCase().includes(q) ||
      career.required_skills.some(s => s.toLowerCase().includes(q)) ||
      career.recommended_skills.some(s => s.toLowerCase().includes(q))
    return matchesCategory && matchesSearch
  })

  return (
    <main className="page-shell">
      <div className="page-head">
        <div>
          <span className="section-kicker">Career recommendation system</span>
          <h1>Industry-standard career tracks & AI-tailored learning roadmaps</h1>
        </div>
      </div>

      <div className="interactive-roadmap-box">
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={18} color="var(--primary)" />
          <strong>Generate Roadmap For Any Specific Career or Job Title</strong>
        </div>
        <p className="career-note">
          Interested in a custom job or niche field? Type any job role below to get the required skills, knowledge areas, and step-by-step roadmap to land it.
        </p>
        <form className="interactive-roadmap-form" onSubmit={handleCustomRoadmap}>
          <input
            className="interactive-roadmap-input"
            value={customGoal}
            onChange={(e) => setCustomGoal(e.target.value)}
            placeholder="e.g. AI Research Engineer, Blockchain Developer, Solutions Architect..."
            required
          />
          <input
            className="interactive-roadmap-input"
            value={customSkills}
            onChange={(e) => setCustomSkills(e.target.value)}
            placeholder="Optional skills you want to include (e.g. Solidity, Cryptography)"
          />
          <button type="submit" className="primary-btn small">
            Generate Roadmap
          </button>
        </form>
      </div>

      {getSession()?.user.role !== 'job_seeker' ? (
        <div className="empty-state">
          Sign in as a job seeker to get personalized recommendations tailored to your resume. <NavLink className="text-link" to="/auth">Sign in</NavLink>
        </div>
      ) : null}

      {loading ? <div className="state-message">Analyzing your resume and profile skills against industry benchmarks…</div> : null}
      {error ? <div className="state-message error-message">{error}</div> : null}

      {getSession()?.user.role === 'job_seeker' ? (
        <section className="panel-card resume-skills">
          <div className="panel-header">
            <h3>Skills detected in your latest resume</h3>
            <span className="pill soft">{resumeSkills.length} found</span>
          </div>
          {resumeSkills.length ? (
            <div className="pill-list">
              {resumeSkills.map((skill) => (
                <span className="skill-chip resume-chip" key={skill}>
                  ✓ {skill}
                </span>
              ))}
            </div>
          ) : (
            <p className="career-note">
              Upload a PDF or DOCX resume from your <NavLink className="text-link" to="/dashboard">dashboard</NavLink> to personalize these matches. Profile skills are used until a resume is available.
            </p>
          )}
        </section>
      ) : null}

      {insights && recommendations.length > 0 ? (
        <section className="insight-panel">
          <div>
            <span className="section-kicker">Your best next moves</span>
            {insights.best_fit ? (
              <h3>Best fit right now: {insights.best_fit} ({insights.best_fit_score}%)</h3>
            ) : null}
            {insights.top_skills_to_learn.length ? (
              <>
                <p className="career-note">Learning these skills unlocks the most of your top matches:</p>
                <div className="pill-list">
                  {insights.top_skills_to_learn.map((item) => (
                    <span
                      className="skill-chip gap-chip"
                      key={item.skill}
                      title={`Helps with: ${item.unlocks.join(', ')}`}
                    >
                      + {item.skill} · {item.unlocks.length} {item.unlocks.length === 1 ? 'career' : 'careers'}
                    </span>
                  ))}
                </div>
              </>
            ) : null}
          </div>
          <div className="insight-strength">
            <strong>Profile strength: {insights.profile_strength.label}</strong>
            <div className="progress-bar"><span style={{ width: `${insights.profile_strength.score}%` }} /></div>
            {insights.profile_strength.tips.length ? (
              <ul>
                {insights.profile_strength.tips.slice(0, 3).map((tip) => <li key={tip}>{tip}</li>)}
              </ul>
            ) : null}
          </div>
        </section>
      ) : null}

      {recommendations.length > 0 && (
        <div className="career-filters-bar">
          <div className="career-filter-tabs">
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                className={`filter-tab-btn ${selectedCategory === cat ? 'active' : ''}`}
                onClick={() => setSelectedCategory(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
          <div className="career-search-wrap">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              placeholder="Search by role or tech stack (e.g. React, Python, Cloud)..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="career-search-input"
            />
          </div>
        </div>
      )}

      <div className="career-stack">
        {filteredRecommendations.map((career) => (
          <article className="list-card highlight career-roadmap-card" key={career.title}>
            <div className="career-card-heading">
              <div>
                <div className="career-title-row">
                  <h3>{career.title}</h3>
                  {career.category && (
                    <span className="career-category-tag"><Tag size={12} /> {career.category}</span>
                  )}
                  {career.demand && (
                    <span className={`career-demand-badge demand-${career.demand.toLowerCase().replace(/\s+/g, '-')}`}>
                      <TrendingUp size={12} /> {career.demand}
                    </span>
                  )}
                  {career.salary_range && (
                    <span className="career-salary-badge">
                      <DollarSign size={12} /> {career.salary_range}
                    </span>
                  )}
                </div>
                <div className="career-meta-row">
                  {career.readiness ? (
                    <span className={`readiness-badge readiness-${career.readiness.toLowerCase().replace(/[^a-z]+/g, '-')}`}>
                      {career.readiness}
                    </span>
                  ) : null}
                  {career.estimated_weeks_to_ready ? (
                    <span className="career-note">≈ {career.estimated_weeks_to_ready} weeks to job-ready</span>
                  ) : null}
                  {career.confidence ? (
                    <span className="career-note" title="How much profile data backs this score">
                      Confidence: {career.confidence}
                    </span>
                  ) : null}
                </div>
                <p>{career.explanation}</p>
              </div>
              <div className="match-box career-match">
                <span>{Math.round(career.score * 100)}% Match</span>
                <div className="progress-bar">
                  <span style={{ width: `${Math.round(career.score * 100)}%` }} />
                </div>
              </div>
            </div>

            <ScoreBreakdown items={career.score_breakdown} />

            <div className="career-skill-grid">
              <div className="career-skill-group">
                <h4>Skills matched from your profile & resume</h4>
                <div className="pill-list">
                  {career.matching_skills.length || career.partial_skills?.length ? (
                    <>
                      {career.matching_skills.map((skill) => {
                        const inResume = career.resume_matching_skills.some((s) => s.toLowerCase() === skill.toLowerCase())
                        return (
                          <span
                            className="skill-chip resume-chip"
                            key={skill}
                            title={inResume ? 'Found in your resume' : 'From your profile'}
                          >
                            ✓ {skill}{inResume ? ' · resume' : ''}
                          </span>
                        )
                      })}
                      {career.partial_skills?.map((p) => (
                        <span
                          className="skill-chip partial-chip"
                          key={p.skill}
                          title={p.via ? `Likely covered through ${p.via}` : 'Related skill'}
                        >
                          ≈ {p.skill} ({p.coverage}%)
                        </span>
                      ))}
                    </>
                  ) : (
                    <span className="career-note">No skills for this role were detected yet.</span>
                  )}
                </div>
              </div>

              <div className="career-skill-group">
                <h4>Core required skills to acquire</h4>
                <div className="pill-list">
                  {career.missing_skills.length ? (
                    career.missing_skills.map((skill) => (
                      <span className="skill-chip gap-chip" key={skill}>
                        + {skill}
                      </span>
                    ))
                  ) : (
                    <span className="skill-chip resume-chip">All core skills matched!</span>
                  )}
                </div>
                {career.recommended_skills.length ? (
                  <div style={{ marginTop: '8px' }}>
                    <span style={{ fontSize: '0.78rem', color: '#6b7280', fontWeight: 600 }}>Recommended & Modern Tools: </span>
                    <span style={{ fontSize: '0.82rem', color: '#374151' }}>{career.recommended_skills.join(', ')}</span>
                  </div>
                ) : null}
              </div>
            </div>

            <div className="career-roadmap">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                <h4>Your step-by-step roadmap to this role</h4>
                <button
                  type="button"
                  className="secondary-btn small"
                  onClick={() => setSelectedRoadmap({ title: career.title, skills: [...career.required_skills, ...career.recommended_skills].join(', ') })}
                >
                  <Compass size={14} /> Full Roadmap View
                </button>
              </div>
              <ol>
                {career.career_roadmap.map((step) => (
                  <li key={step.title}>
                    <strong>{step.title}</strong>
                    <span>{step.description}</span>
                  </li>
                ))}
              </ol>

              {career.roadmap_phases && career.roadmap_phases.length ? (
                <div style={{ marginTop: '16px' }}>
                  <h4 style={{ margin: '0 0 10px', fontSize: '0.88rem', color: '#36374a' }}>Structured Learning Curriculum</h4>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px' }}>
                    {career.roadmap_phases.map((p) => (
                      <div key={p.phase} className="deep-roadmap-card">
                        <div className="deep-roadmap-title">
                          <span>{p.phase}</span>
                          <span className="pill soft" style={{ fontSize: '0.72rem' }}>{p.estimated_time}</span>
                        </div>
                        <ul className="deep-topics-list">
                          {p.topics.map((t) => (
                            <li key={t}>{t}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          </article>
        ))}

        {!loading && filteredRecommendations.length === 0 && getSession()?.user.role === 'job_seeker' && !error ? (
          <div className="empty-state">No matching career tracks found for the selected filter. Try another keyword.</div>
        ) : null}
      </div>

      {selectedRoadmap ? (
        <JobRoadmapModal
          jobTitle={selectedRoadmap.title}
          requiredSkills={selectedRoadmap.skills}
          onClose={() => setSelectedRoadmap(null)}
        />
      ) : null}
    </main>
  )
}


function CommunityPostCard({
  post,
  onLikeToggle,
  onCommentAdded,
}: {
  post: CommunityPost
  onLikeToggle: (postId: number) => void
  onCommentAdded: (postId: number) => void
}) {
  const [showComments, setShowComments] = useState(false)
  const [comments, setComments] = useState<CommunityComment[]>([])
  const [loadingComments, setLoadingComments] = useState(false)
  const [replyText, setReplyText] = useState('')
  const [submittingReply, setSubmittingReply] = useState(false)
  const [replyError, setReplyError] = useState('')
  const session = getSession()

  const loadComments = async () => {
    setLoadingComments(true)
    try {
      const data = await apiRequest<CommunityComment[]>(`/api/community/posts/${post.id}/comments`)
      setComments(data)
    } catch {
      // Ignored
    } finally {
      setLoadingComments(false)
    }
  }

  const toggleComments = () => {
    if (!showComments) {
      void loadComments()
    }
    setShowComments(!showComments)
  }

  const handleSendReply = async (e: FormEvent) => {
    e.preventDefault()
    if (!session) {
      setReplyError('Please sign in to reply to this post.')
      return
    }
    if (!replyText.trim()) return

    setSubmittingReply(true)
    setReplyError('')
    try {
      const res = await apiRequest<{ message: string; comment: CommunityComment }>(
        `/api/community/posts/${post.id}/comments`,
        {
          method: 'POST',
          body: jsonBody({ content: replyText.trim() }),
        }
      )
      setComments((prev) => [...prev, res.comment])
      setReplyText('')
      onCommentAdded(post.id)
    } catch (err) {
      setReplyError(err instanceof Error ? err.message : 'Failed to post reply')
    } finally {
      setSubmittingReply(false)
    }
  }

  return (
    <article className="list-card community-post">
      <div className="community-head">
        <span className="pill soft">{post.category}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {post.author_role && (
            <span className="user-role-badge">{post.author_role.replace('_', ' ')}</span>
          )}
          <span className="post-timestamp">{new Date(post.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>
        </div>
      </div>

      <h3 className="community-post-title">{post.title}</h3>
      <p className="community-post-body">{post.content}</p>

      <div className="community-author-row">
        <span>Posted by <strong>{post.author}</strong></span>
      </div>

      <div className="community-actions-bar">
        <button
          type="button"
          className={`action-pill-btn ${post.user_liked ? 'liked' : ''}`}
          onClick={() => onLikeToggle(post.id)}
          title={session ? 'Like post' : 'Sign in to like'}
        >
          <Heart size={15} fill={post.user_liked ? 'currentColor' : 'none'} />
          <span>{post.likes_count ?? 0}</span>
        </button>

        <button
          type="button"
          className={`action-pill-btn ${showComments ? 'active' : ''}`}
          onClick={toggleComments}
        >
          <MessageSquare size={15} />
          <span>{post.comments_count} {post.comments_count === 1 ? 'Reply' : 'Replies'}</span>
        </button>
      </div>

      {showComments && (
        <div className="comments-section">
          {loadingComments ? (
            <div className="comments-loading">Loading replies...</div>
          ) : comments.length === 0 ? (
            <div className="no-comments-msg">No replies yet. Be the first to share your thoughts!</div>
          ) : (
            <div className="comments-list">
              {comments.map((comm) => (
                <div key={comm.id} className="comment-item">
                  <div className="comment-header">
                    <span className="comment-author">{comm.author}</span>
                    {comm.author_role && (
                      <span className="user-role-badge small">{comm.author_role.replace('_', ' ')}</span>
                    )}
                    <span className="comment-time">{new Date(comm.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
                  </div>
                  <p className="comment-text">{comm.content}</p>
                </div>
              ))}
            </div>
          )}

          {session ? (
            <form className="comment-input-form" onSubmit={handleSendReply}>
              {replyError && <div className="reply-error-msg">{replyError}</div>}
              <div className="comment-input-row">
                <input
                  type="text"
                  placeholder="Write a helpful reply..."
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  className="comment-text-input"
                  required
                />
                <button
                  type="submit"
                  disabled={submittingReply || !replyText.trim()}
                  className="primary-btn small reply-submit-btn"
                >
                  <Send size={14} />
                  <span>{submittingReply ? 'Sending...' : 'Reply'}</span>
                </button>
              </div>
            </form>
          ) : (
            <div className="comment-signin-prompt">
              <NavLink to="/auth" className="text-link">Sign in</NavLink> to join the discussion and reply to this post.
            </div>
          )}
        </div>
      )}
    </article>
  )
}

function CommunityPage() {
  const [posts, setPosts] = useState<CommunityPost[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [category, setCategory] = useState('Career Guidance')
  const [activeCategory, setActiveCategory] = useState('All')
  const session = getSession()

  const loadPosts = async () => {
    try {
      setPosts(await apiRequest<CommunityPost[]>('/api/community/posts'))
      setError('')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not load community posts.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { void Promise.resolve().then(loadPosts) }, [])

  const createPost = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!session) {
      setError('Sign in to create a community post.')
      return
    }
    setSubmitting(true)
    try {
      await apiRequest('/api/community/posts', {
        method: 'POST',
        body: jsonBody({ title, content, category, tags: '' }),
      })
      setTitle('')
      setContent('')
      setShowForm(false)
      await loadPosts()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not create your post.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleLikeToggle = async (postId: number) => {
    if (!session) {
      setError('Please sign in to like community posts.')
      return
    }
    try {
      const res = await apiRequest<{ message: string; liked: boolean; likes_count: number }>(
        `/api/community/posts/${postId}/like`,
        { method: 'POST' }
      )
      setPosts((prev) =>
        prev.map((p) =>
          p.id === postId ? { ...p, user_liked: res.liked, likes_count: res.likes_count } : p
        )
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to like post')
    }
  }

  const handleCommentAdded = (postId: number) => {
    setPosts((prev) =>
      prev.map((p) =>
        p.id === postId ? { ...p, comments_count: p.comments_count + 1 } : p
      )
    )
  }

  const categories = ['All', 'Career Guidance', 'Internships', 'Resume Review', 'General Discussion']

  const filteredPosts = posts.filter(
    (p) => activeCategory === 'All' || p.category === activeCategory
  )

  return (
    <main className="page-shell">
      <div className="page-head">
        <div>
          <span className="section-kicker">Community</span>
          <h1>Career discussions, peer guidance, and live Q&A</h1>
        </div>
        <button
          type="button"
          className="primary-btn small"
          onClick={() => setShowForm((value) => !value)}
        >
          {showForm ? 'Cancel' : 'Create Post'}
        </button>
      </div>

      {error ? <div className="state-message error-message">{error}</div> : null}

      {showForm ? (
        <form className="panel-card post-form" onSubmit={(event) => void createPost(event)}>
          <label>Post title<input required maxLength={200} value={title} onChange={(event) => setTitle(event.target.value)} placeholder="e.g. Tips for landing a Junior Frontend role in 2026?" /></label>
          <label>Category
            <select value={category} onChange={(event) => setCategory(event.target.value)}>
              <option>Career Guidance</option>
              <option>Internships</option>
              <option>Resume Review</option>
              <option>General Discussion</option>
            </select>
          </label>
          <label>What would you like to discuss?<textarea required rows={5} value={content} onChange={(event) => setContent(event.target.value)} placeholder="Share your experience, ask questions, or provide advice to peers..." /></label>
          <button disabled={submitting} type="submit" className="primary-btn small">{submitting ? 'Publishing…' : 'Publish post'}</button>
        </form>
      ) : null}

      <div className="community-category-filter">
        {categories.map((cat) => (
          <button
            key={cat}
            type="button"
            className={`community-cat-btn ${activeCategory === cat ? 'active' : ''}`}
            onClick={() => setActiveCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      {loading ? <div className="state-message">Loading community posts…</div> : null}

      <div className="community-stack">
        {filteredPosts.map((post) => (
          <CommunityPostCard
            key={post.id}
            post={post}
            onLikeToggle={handleLikeToggle}
            onCommentAdded={handleCommentAdded}
          />
        ))}
        {!loading && filteredPosts.length === 0 && !error ? (
          <div className="empty-state">No community posts in this category yet. Start a conversation!</div>
        ) : null}
      </div>
    </main>
  )
}

function AboutPage() {
  return (
    <main className="page-shell narrow">
      <div className="section-heading">
        <span className="section-kicker">About</span>
        <h1>Built to help students, professionals, and recruiters connect meaningfully.</h1>
      </div>
      <div className="info-grid">
        <div className="info-card">
          <Target size={24} />
          <h3>Career clarity</h3>
          <p>Structured recommendations explain how skills and interests map to potential career paths.</p>
        </div>
        <div className="info-card">
          <ShieldCheck size={24} />
          <h3>Trust and privacy</h3>
          <p>Private profile and resume data are protected and only shared with appropriate parties.</p>
        </div>
        <div className="info-card">
          <GraduationCap size={24} />
          <h3>Continuous learning</h3>
          <p>Roadmaps and suggested resources help users upskill in a realistic, measurable way.</p>
        </div>
      </div>
    </main>
  )
}

function DashboardPage() {
  const session = getSession()
  const role = session?.user.role
  const [name, setName] = useState(session?.user.name ?? 'Job seeker')
  const [profileCompletion, setProfileCompletion] = useState(0)
  const [applications, setApplications] = useState<Application[]>([])
  const [recommendations, setRecommendations] = useState<CareerRecommendation[]>([])
  const [savedCount, setSavedCount] = useState(0)
  const [resumes, setResumes] = useState<Array<{ id: number; file_name: string; uploaded_at: string }>>([])
  const [loading, setLoading] = useState(role === 'job_seeker')
  const [error, setError] = useState('')
  const [profileOpen, setProfileOpen] = useState(false)
  const [education, setEducation] = useState('')
  const [skills, setSkills] = useState('')
  const [savingProfile, setSavingProfile] = useState(false)
  const [resumeMessage, setResumeMessage] = useState('')

  useEffect(() => {
    if (role !== 'job_seeker') return
    let cancelled = false
    Promise.all([
      apiRequest<{ user: { full_name: string }; profile: { profile_completion?: number; education_level?: string; skills_summary?: string } | null }>('/api/profiles/me'),
      apiRequest<Application[]>('/api/applications'),
      apiRequest<CareerRecommendation[]>('/api/recommendations'),
      apiRequest<{ job_id: number }[]>('/api/jobs/saved'),
      apiRequest<Array<{ id: number; file_name: string; uploaded_at: string }>>('/api/resumes'),
    ]).then(([profileData, applicationsData, recommendationData, savedData, resumeData]) => {
      if (cancelled) return
      setName(profileData.user.full_name)
      setProfileCompletion(profileData.profile?.profile_completion ?? 0)
      setEducation(profileData.profile?.education_level ?? '')
      setSkills(profileData.profile?.skills_summary ?? '')
      setApplications(applicationsData)
      setRecommendations(recommendationData)
      setSavedCount(savedData.length)
      setResumes(resumeData)
    }).catch((reason: Error) => {
      if (!cancelled) setError(reason.message)
    }).finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [session?.access_token, role])

  const saveProfile = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSavingProfile(true)
    try {
      const result = await apiRequest<{ profile_completion: number }>('/api/profiles/me', {
        method: 'PUT',
        body: jsonBody({ education_level: education, skills_summary: skills }),
      })
      setProfileCompletion(result.profile_completion)
      setRecommendations(await apiRequest<CareerRecommendation[]>('/api/recommendations'))
      setProfileOpen(false)
      setError('')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not update your profile.')
    } finally {
      setSavingProfile(false)
    }
  }

  const uploadResume = async (file?: File) => {
    if (!file) return
    const body = new FormData()
    body.append('file', file)
    try {
      const result = await apiRequest<{ message: string; resume_id: number; file_name: string; extracted_skills: string[] }>('/api/resumes/upload', { method: 'POST', body })
      setResumeMessage(result.extracted_skills.length ? `${result.message}. Skills detected: ${result.extracted_skills.join(', ')}` : `${result.message}. No catalog skills were detected.`)
      setResumes((items) => [{ id: result.resume_id, file_name: result.file_name, uploaded_at: new Date().toISOString() }, ...items])
      setRecommendations(await apiRequest<CareerRecommendation[]>('/api/recommendations'))
    } catch (reason) {
      setResumeMessage(reason instanceof Error ? reason.message : 'Resume upload failed.')
    }
  }

  const deleteResume = async (resumeId: number, fileName: string) => {
    // Instantly remove from UI for immediate feedback
    setResumes((items) => items.filter((r) => r.id !== resumeId))
    setResumeMessage(`Deleting "${fileName}"...`)

    try {
      let res: { message?: string } | undefined
      try {
        res = await apiRequest<{ message?: string }>(`/api/resumes/${resumeId}/delete`, { method: 'POST' })
      } catch {
        try {
          res = await apiRequest<{ message?: string }>(`/api/resumes/${resumeId}`, { method: 'DELETE' })
        } catch {
          res = await apiRequest<{ message?: string }>(`/api/resumes/${resumeId}`, { method: 'POST' })
        }
      }
      setResumeMessage(res?.message || `Successfully removed "${fileName}".`)
      try {
        const updatedRecs = await apiRequest<CareerRecommendation[]>('/api/recommendations')
        setRecommendations(updatedRecs)
      } catch {
        // Recommendations refresh is non-blocking
      }
    } catch (reason) {
      console.error('Delete resume failed:', reason)
      const err = reason instanceof Error ? reason.message : 'Deletion failed on server'
      setResumeMessage(`Note: Server reported (${err}). If backend is offline, please restart backend server.`)
    }
  }

  if (!session || session.user.role !== 'job_seeker') {
    return <main className="page-shell"><div className="empty-state">Sign in as a job seeker to view your dashboard. <NavLink className="text-link" to="/auth">Sign in</NavLink></div></main>
  }

  const metrics = [
    { label: 'Profile completion', value: `${profileCompletion}%` },
    { label: 'Applications', value: String(applications.length) },
    { label: 'Saved jobs', value: String(savedCount) },
    { label: 'Interviews', value: String(applications.filter((application) => application.status === 'Interview').length) },
  ]

  return (
    <main className="page-shell dashboard-layout">
      <div className="page-head">
        <div>
          <span className="section-kicker">Job seeker dashboard</span>
          <h1>Welcome back, {name}</h1>
        </div>
        <button type="button" className="secondary-btn small" onClick={() => setProfileOpen((open) => !open)}>{profileOpen ? 'Close profile' : 'Edit profile'}</button>
      </div>
      {error ? <div className="state-message error-message">{error}</div> : null}
      {loading ? <div className="state-message">Loading your dashboard…</div> : null}
      {profileOpen ? (
        <form className="panel-card profile-form" onSubmit={(event) => void saveProfile(event)}>
          <label>Education level<input value={education} onChange={(event) => setEducation(event.target.value)} placeholder="e.g. Bachelor's degree" /></label>
          <label>Skills, separated by commas<textarea rows={3} value={skills} onChange={(event) => setSkills(event.target.value)} placeholder="Python, SQL, communication" /></label>
          <button disabled={savingProfile} className="primary-btn small" type="submit">{savingProfile ? 'Saving…' : 'Save profile'}</button>
        </form>
      ) : null}
      <div className="panel-card resume-manager-card">
        <div className="resume-manager-top">
          <div>
            <strong>Resumes ({resumes.length} uploaded)</strong>
            <span>Upload multiple resumes without losing previous versions. All extracted skills combine to power your career recommendations.</span>
          </div>
          <label className="primary-btn small upload-control">
            + Upload Another Resume
            <input type="file" accept=".pdf,.docx" onChange={(event) => void uploadResume(event.target.files?.[0])} />
          </label>
        </div>
        {resumeMessage ? (
          <div className={`resume-status-banner ${resumeMessage.toLowerCase().includes('fail') || resumeMessage.toLowerCase().includes('error') || resumeMessage.toLowerCase().includes('note') ? 'warning' : 'success'}`}>
            <span>{resumeMessage}</span>
            <button type="button" className="close-banner-btn" onClick={() => setResumeMessage('')}>×</button>
          </div>
        ) : null}
        <div className="resume-items-list">
          {resumes.length === 0 ? (
            <div className="empty-state compact">No resumes uploaded yet. Upload your PDF or DOCX resume to get personalized recommendations.</div>
          ) : null}
          {resumes.map((resume) => (
            <div className="resume-item-row" key={resume.id}>
              <div className="resume-item-info">
                <FileText size={16} color="var(--primary)" />
                <div>
                  <button
                    type="button"
                    className="resume-item-name"
                    title="Click to download"
                    onClick={() => void downloadFile(`/api/resumes/${resume.id}/download`, resume.file_name).catch((reason: Error) => setResumeMessage(reason.message))}
                  >
                    {resume.file_name}
                  </button>
                  <div className="resume-item-date">
                    Uploaded: {new Date(resume.uploaded_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
              <div className="resume-item-actions">
                <button
                  type="button"
                  className="secondary-btn small"
                  style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                  onClick={() => void downloadFile(`/api/resumes/${resume.id}/download`, resume.file_name).catch((reason: Error) => setResumeMessage(reason.message))}
                >
                  Download
                </button>
                <button
                  type="button"
                  className="delete-resume-btn"
                  onClick={(e) => {
                    e.preventDefault()
                    e.stopPropagation()
                    void deleteResume(resume.id, resume.file_name)
                  }}
                  title="Delete this resume"
                >
                  <Trash2 size={13} style={{ marginRight: '4px' }} /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="metric-grid">
        {metrics.map((metric) => (
          <div className="metric-card" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </div>
        ))}
      </div>
      <div className="dashboard-grid">
        <div className="panel-card wide">
          <div className="panel-header">
            <h3>Application status</h3>
            <span className="pill soft">{applications.length} total</span>
          </div>
          {applications.length ? (
            <div className="table-list">
              {applications.map((application) => (
                <div className="table-row" key={application.id}>
                  <div><strong>{application.job_title || `Job #${application.job_id}`}</strong><span>{new Date(application.submitted_at).toLocaleDateString()}</span></div>
                  <span className="status-pill">{application.status}</span>
                </div>
              ))}
            </div>
          ) : <div className="empty-state compact">Your applications will appear here after you apply to a job.</div>}
        </div>
        <div className="panel-card">
          <div className="panel-header split">
            <h3>Recommended careers</h3>
            <NavLink className="text-link" to="/careers">Skill gaps &amp; roadmaps</NavLink>
          </div>
          <ul className="list-stack">
            {recommendations.slice(0, 4).map((item) => <li key={item.title}><strong>{item.title}</strong><span>{Math.round(item.score * 100)}% fit</span></li>)}
            {!recommendations.length ? <li><strong>No matches yet</strong><span>Add profile skills</span></li> : null}
          </ul>
        </div>
      </div>
      <div className="roadmap-grid">
        <div className="panel-card">
          <div className="panel-header">
            <h3>{recommendations[0] ? `${recommendations[0].title} roadmap` : 'Career roadmap'}</h3>
          </div>
          <ul className="career-roadmap compact-roadmap">
            {(recommendations[0]?.career_roadmap ?? roadmap.map((step) => ({ title: step, description: '' }))).map((step) => (
              <li key={step.title}>
                <CheckCircle2 size={16} />
                <div><strong>{step.title}</strong>{step.description ? <span>{step.description}</span> : null}</div>
              </li>
            ))}
          </ul>
        </div>
        <div className="panel-card">
          <div className="panel-header">
            <h3>Profile checklist</h3>
          </div>
          <ul className="check-list">
            <li><CheckCircle2 size={16} /> {profileCompletion ? `Profile ${profileCompletion}% complete` : 'Complete your profile'}</li>
            <li><CheckCircle2 size={16} /> {skills ? `${skills.split(',').filter(Boolean).length} skills listed` : 'Add skills to improve matches'}</li>
            <li><CheckCircle2 size={16} /> Upload a current resume</li>
          </ul>
        </div>
      </div>
    </main>
  )
}

const demoAccounts = [
  { role: 'job_seeker', email: 'seeker@careercompass.ai', password: 'career123', name: 'Aisha Sharma' },
  { role: 'recruiter', email: 'recruiter@careercompass.ai', password: 'career123', name: 'Rohan Mehta' },
  { role: 'admin', email: 'admin@careercompass.ai', password: 'career123', name: 'Platform Admin' },
] as const

function AuthPage() {
  const navigate = useNavigate()
  const [selectedRole, setSelectedRole] = useState<(typeof demoAccounts)[number]['role']>('job_seeker')
  const [email, setEmail] = useState('seeker@careercompass.ai')
  const [password, setPassword] = useState('career123')
  const [fullName, setFullName] = useState('')
  const [companyName, setCompanyName] = useState('')
  const [registering, setRegistering] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const handleRoleSwitch = (role: (typeof demoAccounts)[number]['role']) => {
    const account = demoAccounts.find((item) => item.role === role)
    setSelectedRole(role)
    if (account) {
      setEmail(account.email)
      setPassword(account.password)
      setError('')
    }
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      if (registering) {
        if (selectedRole === 'admin') throw new Error('Admin accounts cannot be self-registered.')
        await apiRequest('/api/auth/register', {
          method: 'POST',
          body: jsonBody({
            full_name: fullName,
            email,
            password,
            confirm_password: password,
            role: selectedRole,
            company_name: selectedRole === 'recruiter' ? companyName : undefined,
            recruiter_name: selectedRole === 'recruiter' ? fullName : undefined,
          }),
        })
      }
      const response = await apiRequest<LoginResponse>('/api/auth/login', {
        method: 'POST',
        body: jsonBody({ email, password }),
      })
      if (response.user.role !== selectedRole) throw new Error(`This account belongs to the ${response.user.role.replace('_', ' ')} role.`)
      setSession(response)
      if (response.user.role === 'job_seeker') navigate('/dashboard')
      else if (response.user.role === 'recruiter') navigate('/recruiter-dashboard')
      else if (response.user.role === 'admin') navigate('/admin-dashboard')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Authentication failed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="page-shell auth-shell">
      <div className="auth-card">
        <div className="auth-header">
          <span className="section-kicker">Secure Access</span>
          <h1>Sign in or Create Your Account</h1>
        </div>

        {registering ? (
          <div className="role-toggle" aria-label="Account role">
            {demoAccounts.filter((account) => account.role !== 'admin').map((account) => (
              <button
                key={account.role}
                type="button"
                className={selectedRole === account.role ? 'role-chip active' : 'role-chip'}
                onClick={() => setSelectedRole(account.role)}
              >
                {account.role.replace('_', ' ')}
              </button>
            ))}
          </div>
        ) : (
          <div className="role-toggle" aria-label="Demo account roles">
          {demoAccounts.map((account) => (
            <button
              key={account.role}
              type="button"
              className={selectedRole === account.role ? 'role-chip active' : 'role-chip'}
              onClick={() => handleRoleSwitch(account.role)}
            >
              {account.role.replace('_', ' ')}
            </button>
          ))}
          </div>
        )}

        <form className="auth-form" onSubmit={(event) => void handleSubmit(event)}>
          {registering ? (
            <label>
              Full name
              <input required autoComplete="name" value={fullName} onChange={(event) => setFullName(event.target.value)} />
            </label>
          ) : null}
          <label>
            Email
            <input required autoComplete="email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          {registering && selectedRole === 'recruiter' ? (
            <label>
              Company name
              <input required value={companyName} onChange={(event) => setCompanyName(event.target.value)} />
            </label>
          ) : null}
          <label>
            Password
            <input required minLength={8} autoComplete={registering ? 'new-password' : 'current-password'} type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          {error ? <div className="form-error">{error}</div> : null}
          <button disabled={submitting} type="submit" className="primary-btn large">{submitting ? 'Please wait…' : registering ? 'Create account' : 'Login'}</button>
        </form>

        {!registering ? <div className="demo-list">
          {demoAccounts.map((account) => (
            <div key={account.email} className="demo-row">
              <span>{account.name}</span>
              <code>{account.email}</code>
            </div>
          ))}
        </div> : null}

        <div className="auth-footer">
          <span>{registering ? 'Already have an account?' : 'Need an account?'}</span>
          <button type="button" className="text-link text-button" onClick={() => {
            const nextMode = !registering
            setRegistering(nextMode)
            if (nextMode && selectedRole === 'admin') setSelectedRole('job_seeker')
            setError('')
          }}>{registering ? 'Sign in' : 'Create a profile'}</button>
        </div>
      </div>
    </main>
  )
}

function RecruiterJobPostPage() {
  const navigate = useNavigate()
  const session = getSession()
  const role = session?.user.role
  const [company, setCompany] = useState<{ id: number; name: string } | null>(null)
  const [loading, setLoading] = useState(role === 'recruiter')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [form, setForm] = useState({
    title: '',
    description: '',
    responsibilities: '',
    required_skills: '',
    preferred_qualifications: '',
    education: "Bachelor's degree",
    experience: '0-2 years',
    employment_type: 'Full-time',
    salary_range: '',
    location: '',
    work_mode: 'Hybrid',
    deadline: '',
    openings: 1,
  })

  useEffect(() => {
    if (role !== 'recruiter') return
    apiRequest<{ id: number; name: string }>('/api/jobs/company')
      .then(setCompany)
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false))
  }, [role])

  const updateField = (field: keyof typeof form, value: string | number) => {
    setForm((current) => ({ ...current, [field]: value }))
  }

  const submitJob = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!company) return
    setSubmitting(true)
    setError('')
    try {
      await apiRequest('/api/jobs', {
        method: 'POST',
        body: jsonBody({ ...form, company_id: company.id, deadline: form.deadline || null, is_active: true }),
      })
      navigate('/recruiter-dashboard')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not publish this job.')
    } finally {
      setSubmitting(false)
    }
  }

  if (session?.user.role !== 'recruiter') {
    return <main className="page-shell"><div className="empty-state">Sign in as a recruiter to post a job. <NavLink className="text-link" to="/auth">Sign in</NavLink></div></main>
  }

  return (
    <main className="page-shell">
      <div className="page-head">
        <div>
          <span className="section-kicker">Talent Acquisition</span>
          <h1>Post a New Job Opening</h1>
        </div>
        <NavLink className="secondary-btn small" to="/recruiter-dashboard">Back to dashboard</NavLink>
      </div>
      {loading ? <div className="state-message">Checking your company profile…</div> : null}
      {error ? <div className="state-message error-message">{error}</div> : null}
      {company ? <div className="company-context">Posting as <strong>{company.name}</strong></div> : null}
      {company ? (
        <form className="panel-card job-post-form" onSubmit={(event) => void submitJob(event)}>
          <label>Job title<input required maxLength={200} value={form.title} onChange={(event) => updateField('title', event.target.value)} /></label>
          <label>Job description<textarea required rows={4} value={form.description} onChange={(event) => updateField('description', event.target.value)} /></label>
          <label>Responsibilities<textarea required rows={3} value={form.responsibilities} onChange={(event) => updateField('responsibilities', event.target.value)} /></label>
          <label>Required skills<input required placeholder="Python, SQL, communication" value={form.required_skills} onChange={(event) => updateField('required_skills', event.target.value)} /></label>
          <label>Preferred qualifications<input value={form.preferred_qualifications} onChange={(event) => updateField('preferred_qualifications', event.target.value)} /></label>
          <div className="form-grid">
            <label>Location<input required value={form.location} onChange={(event) => updateField('location', event.target.value)} /></label>
            <label>Work mode<select value={form.work_mode} onChange={(event) => updateField('work_mode', event.target.value)}><option>Onsite</option><option>Hybrid</option><option>Remote</option></select></label>
            <label>Employment type<select value={form.employment_type} onChange={(event) => updateField('employment_type', event.target.value)}><option>Full-time</option><option>Part-time</option><option>Internship</option><option>Contract</option></select></label>
            <label>Experience<input required value={form.experience} onChange={(event) => updateField('experience', event.target.value)} /></label>
            <label>Salary range<input required value={form.salary_range} onChange={(event) => updateField('salary_range', event.target.value)} /></label>
            <label>Openings<input required min={1} type="number" value={form.openings} onChange={(event) => updateField('openings', Number(event.target.value))} /></label>
            <label>Education<input value={form.education} onChange={(event) => updateField('education', event.target.value)} /></label>
            <label>Application deadline<input type="date" value={form.deadline} onChange={(event) => updateField('deadline', event.target.value)} /></label>
          </div>
          <button disabled={submitting || loading} className="primary-btn large" type="submit">{submitting ? 'Publishing…' : 'Publish job'}</button>
        </form>
      ) : null}
    </main>
  )
}

function RecruiterDashboardPage() {
  const session = getSession()
  const role = session?.user.role
  const [stats, setStats] = useState({ active_roles: 0, qualified_applicants: 0, interviews: 0 })
  const [applications, setApplications] = useState<Application[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(role === 'recruiter')

  useEffect(() => {
    if (role !== 'recruiter') return
    let cancelled = false
    Promise.all([
      apiRequest<typeof stats>('/api/admin/dashboard'),
      apiRequest<Application[]>('/api/applications/recruiter'),
      apiRequest<Job[]>('/api/jobs/mine'),
    ]).then(([dashboard, applicantRows, companyJobs]) => {
      if (cancelled) return
      setStats(dashboard)
      setApplications(applicantRows)
      setJobs(companyJobs)
    }).catch((reason: Error) => {
      if (!cancelled) setError(reason.message)
    }).finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [session?.access_token, role])

  const updateApplication = async (applicationId: number, status: string) => {
    try {
      await apiRequest(`/api/applications/${applicationId}/status`, { method: 'PATCH', body: jsonBody({ status }) })
      setApplications((items) => items.map((item) => item.id === applicationId ? { ...item, status } : item))
      setStats((current) => ({ ...current, interviews: applications.filter((item) => item.id === applicationId ? status === 'Interview' : item.status === 'Interview').length }))
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not update application.')
    }
  }

  if (session?.user.role !== 'recruiter') {
    return <main className="page-shell"><div className="empty-state">Sign in with a recruiter account to view hiring tools. <NavLink className="text-link" to="/auth">Sign in</NavLink></div></main>
  }

  const statusCounts = ['Applied', 'Reviewing', 'Shortlisted', 'Interview', 'Rejected'].map((status) => ({
    month: status,
    value: applications.filter((application) => application.status === status).length,
  }))
  const roleCounts = jobs.map((job) => ({
    title: job.title,
    count: applications.filter((application) => application.job_id === job.id).length,
  }))

  return (
    <main className="page-shell dashboard-layout">
      <div className="page-head">
        <div>
          <span className="section-kicker">Recruiter Portal</span>
          <h1>Hiring Pipeline & Candidate Shortlist</h1>
        </div>
        <NavLink to="/recruiter/jobs/new" className="primary-btn small">Post a role</NavLink>
      </div>
      {loading ? <div className="state-message">Loading hiring activity…</div> : null}
      {error ? <div className="state-message error-message">{error}</div> : null}

      <div className="metric-grid">
        {[
          { label: 'Open roles', value: stats.active_roles },
          { label: 'Applicants', value: stats.qualified_applicants },
          { label: 'Interviews', value: stats.interviews },
          { label: 'Company roles', value: jobs.length },
        ].map((metric) => (
          <div className="metric-card" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </div>
        ))}
      </div>

      <div className="dashboard-grid">
        <div className="panel-card wide">
          <div className="panel-header">
            <h3>Hiring pipeline</h3>
            <span className="pill soft">Application stages</span>
          </div>
          {applications.length ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={statusCounts}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="month" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#14b8a6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <div className="empty-state compact">Applications for your job posts will appear here.</div>}
        </div>

        <div className="panel-card">
          <div className="panel-header">
            <h3>Top roles</h3>
          </div>
          <ul className="list-stack">
            {roleCounts.map((role) => <li key={role.title}><strong>{role.title}</strong><span>{role.count} applicants</span></li>)}
            {!roleCounts.length ? <li><strong>No posted roles</strong><span>Post your first job</span></li> : null}
          </ul>
        </div>
      </div>

      <div className="panel-card">
        <div className="panel-header">
          <h3>Applicant shortlist</h3>
          <span className="pill soft">{applications.length} applicants</span>
        </div>
        <div className="table-list">
          {applications.map((applicant) => (
            <div className="table-row recruiter-applicant" key={applicant.id}>
              <div>
                <strong>{applicant.applicant_name}</strong>
                <span>{applicant.job_title} · {applicant.applicant_email}</span>
                {applicant.notes ? <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: '4px' }}>📋 {applicant.notes}</div> : null}
                {applicant.cover_letter ? <div style={{ fontSize: '0.78rem', color: 'var(--text)', fontStyle: 'italic', marginTop: '2px' }}>💬 "{applicant.cover_letter}"</div> : null}
              </div>
              <select aria-label={`Status for ${applicant.applicant_name}`} value={applicant.status} onChange={(event) => void updateApplication(applicant.id, event.target.value)}>
                {['Applied', 'Reviewing', 'Shortlisted', 'Interview', 'Rejected', 'Hired'].map((status) => <option key={status}>{status}</option>)}
              </select>
            </div>
          ))}
          {!applications.length ? <div className="empty-state compact">No applicants yet. Share your open roles to get started.</div> : null}
        </div>
      </div>
    </main>
  )
}

function AdminDashboardPage() {
  const session = getSession()
  const role = session?.user.role
  const [stats, setStats] = useState<{ total_users: number; active_jobs: number; verified_companies: number; total_posts: number; pending_companies: number } | null>(null)
  const [pendingCompanies, setPendingCompanies] = useState<Array<{ id: number; name: string; website: string | null; industry: string | null }>>([])
  const [error, setError] = useState('')

  useEffect(() => {
    if (role !== 'admin') return
    Promise.all([
      apiRequest<NonNullable<typeof stats>>('/api/admin/dashboard'),
      apiRequest<typeof pendingCompanies>('/api/admin/companies/pending'),
    ]).then(([dashboard, companies]) => {
      setStats(dashboard)
      setPendingCompanies(companies)
    }).catch((reason: Error) => setError(reason.message))
  }, [session?.access_token, role])

  if (session?.user.role !== 'admin') {
    return <main className="page-shell"><div className="empty-state">Sign in with an admin account to view platform operations. <NavLink className="text-link" to="/auth">Sign in</NavLink></div></main>
  }

  const approveCompany = async (companyId: number) => {
    try {
      await apiRequest(`/api/admin/companies/${companyId}/verify`, { method: 'PATCH' })
      setPendingCompanies((companies) => companies.filter((company) => company.id !== companyId))
      setStats((current) => current ? {
        ...current,
        pending_companies: Math.max(0, current.pending_companies - 1),
        verified_companies: current.verified_companies + 1,
      } : current)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not verify company.')
    }
  }

  const exportStats = () => {
    if (!stats) {
      setError('Wait for the platform summary to load before exporting.')
      return
    }
    const csv = [
      ['Metric', 'Value'],
      ['Total users', stats.total_users],
      ['Active jobs', stats.active_jobs],
      ['Verified companies', stats.verified_companies],
      ['Pending company verification', stats.pending_companies],
      ['Community posts', stats.total_posts],
    ].map((row) => row.join(',')).join('\r\n')
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'careercompass-platform-summary.csv'
    link.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  return (
    <main className="page-shell dashboard-layout">
      <div className="page-head">
        <div>
          <span className="section-kicker">Platform Administration</span>
          <h1>Operations & Company Verification Overview</h1>
        </div>
        <button disabled={!stats} type="button" className="secondary-btn small" onClick={exportStats}>Export summary</button>
      </div>

      <div className="metric-grid">
        {[
          { label: 'Total users', value: stats?.total_users ?? '—' },
          { label: 'Active jobs', value: stats?.active_jobs ?? '—' },
          { label: 'Verified companies', value: stats?.verified_companies ?? '—' },
          { label: 'Pending verification', value: stats?.pending_companies ?? '—' },
        ].map((metric) => (
          <div className="metric-card" key={metric.label}>
            <span>{metric.label}</span>
            <strong>{metric.value}</strong>
          </div>
        ))}
      </div>
      {error ? <div className="state-message error-message">{error}</div> : null}

      <div className="dashboard-grid">
        <div className="panel-card wide">
          <div className="panel-header">
            <h3>Platform health</h3>
            <span className="pill soft">Healthy</span>
          </div>
          <ul className="check-list">
            <li><CheckCircle2 size={16} /> API and database metrics loaded from the live platform.</li>
            <li><CheckCircle2 size={16} /> Counts update from persisted users, roles, companies, and posts.</li>
          </ul>
        </div>

        <div className="panel-card">
          <div className="panel-header">
            <h3>Priority actions</h3>
          </div>
          <ul className="list-stack">
            <li><strong>Total platform users</strong><span>{stats?.total_users ?? 'Loading'}</span></li>
            <li><strong>Active job listings</strong><span>{stats?.active_jobs ?? 'Loading'}</span></li>
            <li><strong>Community posts</strong><span>{stats?.total_posts ?? 'Loading'}</span></li>
          </ul>
        </div>
      </div>

      <div className="panel-card">
        <div className="panel-header">
          <h3>Company verification</h3>
          <span className="pill soft">{pendingCompanies.length} pending</span>
        </div>
        <div className="table-list">
          {pendingCompanies.map((company) => (
            <div className="table-row" key={company.id}>
              <div><strong>{company.name}</strong><span>{company.industry || 'Industry not specified'}{company.website ? ` · ${company.website}` : ''}</span></div>
              <button className="primary-btn small" type="button" onClick={() => void approveCompany(company.id)}>Verify company</button>
            </div>
          ))}
          {!pendingCompanies.length ? <div className="empty-state compact">No companies are waiting for verification.</div> : null}
        </div>
      </div>
    </main>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/jobs" element={<JobsPage />} />
          <Route path="/careers" element={<CareerPage />} />
          <Route path="/community" element={<CommunityPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/recruiter-dashboard" element={<RecruiterDashboardPage />} />
          <Route path="/admin-dashboard" element={<AdminDashboardPage />} />
          <Route path="/recruiter/jobs/new" element={<RecruiterJobPostPage />} />
          <Route path="/auth" element={<AuthPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}

function SparklesIcon() {
  return <span className="sparkles-icon">✦</span>
}

export default App
