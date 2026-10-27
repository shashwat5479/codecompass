import { useState, useEffect, type FormEvent, type ChangeEvent } from 'react'
import { apiRequest, jsonBody, getSession } from './api'
import {
  X,
  Send,
  Building2,
  MapPin,
  Clock,
  FileText,
  CheckCircle2,
  UploadCloud,
  Sparkles,
  User,
  Mail,
  Phone,
  Briefcase,
  GraduationCap,
  Globe,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react'

export type JobApplyTarget = {
  id: number
  title: string
  company?: string
  location?: string
  salary_range?: string
  employment_type?: string
  experience?: string
}

const NOTICE_PERIOD_OPTIONS = [
  { id: 'Immediate', label: '⚡ Immediate Joiner' },
  { id: '15 Days', label: '15 Days' },
  { id: '30 Days', label: '30 Days (1 Mo)' },
  { id: '60 Days', label: '60 Days (2 Mo)' },
  { id: '90 Days', label: '90 Days' },
]

const EXPERIENCE_OPTIONS = [
  'Fresher / Entry level (< 1 yr)',
  '1 - 2 years',
  '3 - 5 years',
  '5 - 8 years',
  '8+ years',
]

const QUICK_STARTERS = [
  'Excited to contribute my technical strengths and fast-learning ability to your engineering team.',
  'Experienced in building scalable and performant web applications that deliver measurable impact.',
  'Strong foundation in software design, problem solving, and modern best practices.',
]

export function JobApplicationModal({
  job,
  onClose,
  onSuccess,
}: {
  job: JobApplyTarget
  onClose: () => void
  onSuccess: (message: string) => void
}) {
  const session = getSession()

  // Form Fields
  const [fullName, setFullName] = useState(session?.user.name ?? '')
  const [email, setEmail] = useState(session?.user.email ?? '')
  const [phone, setPhone] = useState('')
  const [location, setLocation] = useState('')
  const [experience, setExperience] = useState('Fresher / Entry level (< 1 yr)')
  const [education, setEducation] = useState('')
  const [skills, setSkills] = useState('')
  const [portfolioUrl, setPortfolioUrl] = useState('')
  const [noticePeriod, setNoticePeriod] = useState('Immediate')
  const [coverLetter, setCoverLetter] = useState('')
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)

  // Resumes list & upload state
  const [resumes, setResumes] = useState<Array<{ id: number; file_name: string; uploaded_at?: string }>>([])
  const [uploadingResume, setUploadingResume] = useState(false)
  const [uploadMessage, setUploadMessage] = useState('')

  // Submission state
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [appliedSuccess, setAppliedSuccess] = useState(false)

  // Load existing resumes and candidate profile on mount
  useEffect(() => {
    let cancelled = false

    apiRequest<Array<{ id: number; file_name: string; uploaded_at?: string }>>('/api/resumes')
      .then((items) => {
        if (!cancelled && items.length > 0) {
          setResumes(items)
          setSelectedResumeId(items[0].id)
        }
      })
      .catch(() => {})

    apiRequest<{ user: { full_name: string }; profile: { education_level?: string; skills_summary?: string } | null }>('/api/profiles/me')
      .then((res) => {
        if (!cancelled && res) {
          if (res.user?.full_name && !fullName) setFullName(res.user.full_name)
          if (res.profile?.education_level && !education) setEducation(res.profile.education_level)
          if (res.profile?.skills_summary && !skills) setSkills(res.profile.skills_summary)
        }
      })
      .catch(() => {})

    return () => {
      cancelled = true
    }
  }, [])

  // Quick Inline Resume Upload
  const handleQuickUpload = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploadingResume(true)
    setUploadMessage('Uploading & analyzing resume...')
    const body = new FormData()
    body.append('file', file)

    try {
      const res = await apiRequest<{ message: string; resume_id: number; file_name: string; extracted_skills: string[] }>(
        '/api/resumes/upload',
        { method: 'POST', body }
      )
      const newResume = { id: res.resume_id, file_name: res.file_name, uploaded_at: new Date().toISOString() }
      setResumes((prev) => [newResume, ...prev])
      setSelectedResumeId(res.resume_id)
      setUploadMessage(`Attached: "${res.file_name}"`)
      if (res.extracted_skills.length && !skills) {
        setSkills(res.extracted_skills.join(', '))
      }
    } catch (err) {
      setUploadMessage(err instanceof Error ? err.message : 'Upload failed.')
    } finally {
      setUploadingResume(false)
    }
  }

  // Handle Form Submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    try {
      const payload = {
        job_id: job.id,
        resume_id: selectedResumeId,
        full_name: fullName.trim(),
        email: email.trim(),
        phone: phone.trim(),
        experience,
        education: education.trim(),
        skills: skills.trim(),
        portfolio_url: portfolioUrl.trim()
          ? location.trim()
            ? `${portfolioUrl.trim()} (Location: ${location.trim()})`
            : portfolioUrl.trim()
          : location.trim()
          ? `Location: ${location.trim()}`
          : undefined,
        notice_period: noticePeriod,
        cover_letter: coverLetter.trim(),
      }

      await apiRequest('/api/applications', {
        method: 'POST',
        body: jsonBody(payload),
      })

      setAppliedSuccess(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not submit your application. Please check your inputs.')
      setSubmitting(false)
    }
  }

  const addQuickStarter = (starterText: string) => {
    setCoverLetter((prev) => (prev ? `${prev} ${starterText}` : starterText))
  }

  const companyLetter = (job.company || 'C').trim().charAt(0).toUpperCase()

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content app-pro-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header Banner */}
        <div className="app-pro-header">
          <div className="app-pro-header-main">
            <div className="company-logo-badge">{companyLetter}</div>
            <div>
              <div className="app-pro-kicker-row">
                <span className="app-pro-kicker">Job Application</span>
                <span className="app-pro-badge-fast">⚡ Direct Apply</span>
              </div>
              <h2 className="app-pro-title">{job.title}</h2>
              <div className="app-pro-meta-chips">
                <span className="app-meta-chip">
                  <Building2 size={13} /> {job.company || 'Confidential'}
                </span>
                {job.location ? (
                  <span className="app-meta-chip">
                    <MapPin size={13} /> {job.location}
                  </span>
                ) : null}
                {job.salary_range ? (
                  <span className="app-meta-chip highlight-salary">
                    💰 {job.salary_range}
                  </span>
                ) : null}
              </div>
            </div>
          </div>
          <button type="button" className="app-pro-close-btn" onClick={onClose} aria-label="Close dialog">
            <X size={18} />
          </button>
        </div>

        {appliedSuccess ? (
          <div className="app-success-screen">
            <div className="app-success-icon-wrap">
              <CheckCircle2 size={56} className="app-success-icon" />
            </div>
            <h3>Application Submitted Successfully!</h3>
            <p className="app-success-lead">
              Your profile, contact details, and resume have been delivered to the hiring team at{' '}
              <strong>{job.company || 'the employer'}</strong>.
            </p>
            <div className="app-success-card">
              <div className="success-card-row">
                <span>Target Position:</span>
                <strong>{job.title}</strong>
              </div>
              <div className="success-card-row">
                <span>Applicant:</span>
                <span>{fullName} ({email})</span>
              </div>
              <div className="success-card-row">
                <span>Availability:</span>
                <span>{noticePeriod}</span>
              </div>
              <div className="success-card-row">
                <span>Status:</span>
                <span className="status-badge-applied">✓ Applied</span>
              </div>
            </div>
            <div className="app-success-actions">
              <button
                type="button"
                className="primary-btn"
                onClick={() => {
                  onSuccess(`Applied to ${job.title} successfully!`)
                  onClose()
                }}
              >
                Done & Continue Browsing <ArrowRight size={15} style={{ marginLeft: '6px' }} />
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={(e) => void handleSubmit(e)} className="app-pro-form">
            {error ? (
              <div className="app-error-banner">
                <span>⚠️ {error}</span>
              </div>
            ) : null}

            {/* SECTION 1: Personal & Contact Information */}
            <div className="app-form-section">
              <div className="app-section-header">
                <div className="section-step-num">1</div>
                <div>
                  <h4>Contact & Identity</h4>
                  <p>How the recruitment team will reach out to you</p>
                </div>
              </div>

              <div className="app-input-grid">
                <div className="app-input-group">
                  <label>
                    <User size={14} className="input-icon" /> Full Name <span className="req">*</span>
                  </label>
                  <input
                    required
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="e.g. Aisha Sharma"
                  />
                </div>

                <div className="app-input-group">
                  <label>
                    <Mail size={14} className="input-icon" /> Email Address <span className="req">*</span>
                  </label>
                  <input
                    required
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="e.g. aisha@example.com"
                  />
                </div>

                <div className="app-input-group">
                  <label>
                    <Phone size={14} className="input-icon" /> Phone Number <span className="req">*</span>
                  </label>
                  <input
                    required
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="e.g. +91 98765 43210"
                  />
                </div>

                <div className="app-input-group">
                  <label>
                    <MapPin size={14} className="input-icon" /> Current City / Location
                  </label>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="e.g. Bangalore, India (or Remote)"
                  />
                </div>
              </div>
            </div>

            {/* SECTION 2: Professional Details & Skills */}
            <div className="app-form-section">
              <div className="app-section-header">
                <div className="section-step-num">2</div>
                <div>
                  <h4>Experience & Availability</h4>
                  <p>Highlight your career stage and readiness</p>
                </div>
              </div>

              <div className="app-input-grid">
                <div className="app-input-group">
                  <label>
                    <Briefcase size={14} className="input-icon" /> Total Experience <span className="req">*</span>
                  </label>
                  <select value={experience} onChange={(e) => setExperience(e.target.value)}>
                    {EXPERIENCE_OPTIONS.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="app-input-group">
                  <label>
                    <GraduationCap size={14} className="input-icon" /> Highest Qualification
                  </label>
                  <input
                    type="text"
                    value={education}
                    onChange={(e) => setEducation(e.target.value)}
                    placeholder="e.g. B.Tech Computer Science / MCA"
                  />
                </div>
              </div>

              {/* Notice Period Pills */}
              <div className="app-notice-section">
                <label className="section-sublabel">
                  <Clock size={14} className="input-icon" /> Notice Period / Availability <span className="req">*</span>
                </label>
                <div className="notice-pill-wrap">
                  {NOTICE_PERIOD_OPTIONS.map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      className={`notice-pill-btn ${noticePeriod === opt.id ? 'active' : ''}`}
                      onClick={() => setNoticePeriod(opt.id)}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="app-input-group">
                <label>
                  <Sparkles size={14} className="input-icon" /> Relevant Skills / Tech Stack
                </label>
                <input
                  type="text"
                  value={skills}
                  onChange={(e) => setSkills(e.target.value)}
                  placeholder="e.g. React, TypeScript, Python, FastAPI, SQL, Tailwind"
                />
                <span className="field-hint">Comma-separated skills matched against job requirements</span>
              </div>

              <div className="app-input-group">
                <label>
                  <Globe size={14} className="input-icon" /> Portfolio / GitHub / LinkedIn
                </label>
                <input
                  type="url"
                  value={portfolioUrl}
                  onChange={(e) => setPortfolioUrl(e.target.value)}
                  placeholder="https://github.com/... or https://linkedin.com/in/..."
                />
              </div>
            </div>

            {/* SECTION 3: Resume Attachment */}
            <div className="app-form-section">
              <div className="app-section-header">
                <div className="section-step-num">3</div>
                <div className="section-title-between">
                  <div>
                    <h4>Attach Resume</h4>
                    <p>Select which resume to send or upload a tailored version</p>
                  </div>
                  <label className="quick-upload-label">
                    <UploadCloud size={14} />
                    <span>{uploadingResume ? 'Uploading...' : '+ Upload Resume'}</span>
                    <input
                      type="file"
                      accept=".pdf,.docx"
                      style={{ display: 'none' }}
                      disabled={uploadingResume}
                      onChange={(e) => void handleQuickUpload(e)}
                    />
                  </label>
                </div>
              </div>

              {uploadMessage ? <div className="resume-upload-status">{uploadMessage}</div> : null}

              {resumes.length > 0 ? (
                <div className="resume-cards-grid">
                  {resumes.map((r) => {
                    const isSelected = selectedResumeId === r.id
                    return (
                      <div
                        key={r.id}
                        className={`resume-card-item ${isSelected ? 'selected' : ''}`}
                        onClick={() => setSelectedResumeId(r.id)}
                        role="button"
                        tabIndex={0}
                      >
                        <div className="resume-card-left">
                          <div className={`resume-card-icon ${isSelected ? 'active' : ''}`}>
                            <FileText size={18} />
                          </div>
                          <div>
                            <strong className="resume-card-name" title={r.file_name}>
                              {r.file_name}
                            </strong>
                            <div className="resume-card-meta">
                              {r.uploaded_at ? `Added ${new Date(r.uploaded_at).toLocaleDateString()}` : 'Ready to submit'}
                            </div>
                          </div>
                        </div>
                        <div className="resume-card-check">
                          <div className={`custom-radio ${isSelected ? 'checked' : ''}`}>
                            {isSelected ? <div className="radio-dot" /> : null}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              ) : (
                <div className="no-resumes-prompt">
                  <FileText size={24} color="var(--primary)" />
                  <div>
                    <strong>No resumes uploaded yet</strong>
                    <p>Click the button above to upload your PDF or DOCX resume, or submit with your profile info.</p>
                  </div>
                </div>
              )}
            </div>

            {/* SECTION 4: Pitch / Cover Note */}
            <div className="app-form-section">
              <div className="app-section-header">
                <div className="section-step-num">4</div>
                <div>
                  <h4>Pitch to the Hiring Manager</h4>
                  <p>Briefly share what excites you about this specific opportunity</p>
                </div>
              </div>

              <div className="quick-starter-chips">
                <span className="chips-label">Quick Ideas:</span>
                {QUICK_STARTERS.map((starter) => (
                  <button
                    key={starter}
                    type="button"
                    className="quick-chip-btn"
                    onClick={() => addQuickStarter(starter)}
                  >
                    + {starter.substring(0, 36)}…
                  </button>
                ))}
              </div>

              <div className="app-input-group">
                <textarea
                  rows={4}
                  maxLength={800}
                  value={coverLetter}
                  onChange={(e) => setCoverLetter(e.target.value)}
                  placeholder="Share a short note on why you'd be a great match for this role and what projects or skills make you stand out..."
                />
                <div className="char-counter">{coverLetter.length} / 800 characters</div>
              </div>
            </div>

            {/* Trust & Submit Footer */}
            <div className="app-pro-footer">
              <div className="trust-note">
                <ShieldCheck size={16} color="#16a34a" />
                <span>Your details are encrypted and shared exclusively with the verified employer.</span>
              </div>
              <div className="app-footer-buttons">
                <button type="button" className="secondary-btn" onClick={onClose} disabled={submitting}>
                  Cancel
                </button>
                <button type="submit" className="primary-btn app-submit-btn" disabled={submitting}>
                  <Send size={15} />
                  <span>{submitting ? 'Submitting Application...' : 'Submit Application'}</span>
                </button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
