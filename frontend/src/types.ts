export type OpportunityForm = {
  email: string
  contact_name: string
  company: string
  message: string
  source: string
  product_category: string
  project_name: string
  project_location: string
  project_stage: string
  estimated_value: string
  deadline: string
  decision_maker_role: string
}

export type AgentFinding = {
  agent: string
  summary: string
  evidence: string[]
  confidence: number
}

export type OpportunityDecision = {
  score: number
  tier: "Pursue" | "Review" | "Pass"
  reasons: string[]
  missing_information: string[]
}

export type SalesBrief = {
  executive_summary: string
  recommended_angle: string
  discovery_questions: string[]
  response_subject: string
  response_body: string
  requires_human_approval: boolean
}

export type OpportunityOutcome = {
  opportunity_id: string
  findings: AgentFinding[]
  decision: OpportunityDecision
  brief: SalesBrief
  routing_status: string
  agent_trace: string[]
  latency_ms: number
}

export type HealthStatus = {
  status: string
  demo_mode: boolean
  queued: number
}
