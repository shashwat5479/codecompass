import { useEffect, useState } from 'react'
import { apiRequest, jsonBody, type CustomRoadmap } from './api'
import { X } from 'lucide-react'

export function JobRoadmapModal({
  jobTitle,
  requiredSkills,
  jobId,
  onClose,
}: {
  jobTitle: string
  requiredSkills?: string
  jobId?: number
  onClose: () => void
}) {
  const [data, setData] = useState<CustomRoadmap | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    apiRequest<CustomRoadmap>('/api/recommendations/roadmap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ job_id: jobId, target_role: jobTitle, required_skills: requiredSkills }),
    })
      .then((res) => {
        if (!cancelled) {
          setData(res)
          setError('')
        }
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [jobTitle, requiredSkills, jobId])

  return (
    <div className="modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span className="section-kicker">Career Roadmap & Knowledge Guide</span>
            <h2>How to become a {jobTitle}</h2>
          </div>
          <button className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        {loading ? <div className="state-message">Analyzing skills and assembling your personalized roadmap…</div> : null}
        {error ? <div className="state-message error-message">{error}</div> : null}

        {data ? (
          <div>
            <div className="fit-summary-banner">
              <div>
                <strong>Profile Fit: {Math.round(data.fit_score * 100)}%</strong>
                <p>
                  {data.missing_skills.length === 0
                    ? 'You have matched all primary skills for this job!'
                    : `Focus on bridging ${data.missing_skills.length} core knowledge gap${data.missing_skills.length > 1 ? 's' : ''} to become job-ready.`}
                  {data.estimated_weeks ? ` Estimated time: about ${data.estimated_weeks} weeks.` : ''}
                </p>
              </div>
              <div className="progress-bar" style={{ width: '140px' }}>
                <span style={{ width: `${Math.round(data.fit_score * 100)}%` }} />
              </div>
            </div>

            <div className="career-skill-grid">
              <div className="career-skill-group">
                <h4>Skills you already have</h4>
                <div className="pill-list">
                  {data.matched_skills.length ? (
                    data.matched_skills.map((s) => (
                      <span key={s} className="skill-chip resume-chip">
                        ✓ {s}
                      </span>
                    ))
                  ) : (
                    <span className="career-note">None matched yet. Follow the roadmap below to start learning.</span>
                  )}
                  {data.partial_skills?.map((p) => (
                    <span key={p.skill} className="skill-chip partial-chip" title={p.via ? `Likely covered via ${p.via}` : undefined}>
                      ≈ {p.skill} ({p.coverage}%)
                    </span>
                  ))}
                </div>
              </div>
              <div className="career-skill-group">
                <h4>Necessary Knowledge & Skills to Acquire</h4>
                <div className="pill-list">
                  {data.missing_skills.length ? (
                    data.missing_skills.map((s) => (
                      <span key={s} className="skill-chip gap-chip">
                        + {s}
                      </span>
                    ))
                  ) : (
                    <span className="skill-chip resume-chip">All key prerequisites fulfilled!</span>
                  )}
                </div>
              </div>
            </div>

            <div className="roadmap-modal-section">
              <h4>Step-by-Step Learning & Acquisition Roadmap</h4>
              <div className="roadmap-timeline">
                {data.roadmap.map((phase) => (
                  <div key={phase.step} className="timeline-step-card">
                    <div className="timeline-step-badge">{phase.step}</div>
                    <div className="timeline-step-body">
                      <h4>{phase.title}</h4>
                      <p>{phase.description}</p>
                      <span className="timeline-duration">{phase.estimated_timeline}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {data.suggested_projects?.length ? (
              <div className="roadmap-modal-section">
                <h4>Suggested Showcase Projects</h4>
                <div className="modal-project-list">
                  {data.suggested_projects.map((proj) => (
                    <span key={proj} className="modal-project-pill">
                      📁 {proj}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}

            {data.suggested_certifications?.length ? (
              <div className="roadmap-modal-section">
                <h4>Recommended Certifications</h4>
                <div className="modal-cert-list">
                  {data.suggested_certifications.map((cert) => (
                    <span key={cert} className="modal-cert-pill">
                      🎖️ {cert}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  )
}
