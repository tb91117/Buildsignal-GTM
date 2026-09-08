import { useEffect, useState, type FormEvent, type ReactNode } from "react"
import {
  Activity,
  ArrowRight,
  Bot,
  Building2,
  Check,
  CheckCircle2,
  CircleDot,
  ClipboardCheck,
  Copy,
  FileSearch,
  Gauge,
  Layers3,
  LoaderCircle,
  Mail,
  Network,
  RefreshCcw,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  Users,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { apiUrl } from "@/lib/api"
import { cn } from "@/lib/utils"
import type { HealthStatus, OpportunityForm, OpportunityOutcome } from "@/types"

const INITIAL_FORM: OpportunityForm = {
  contact_name: "Maria Chen",
  email: "maria@northstarbuild.com",
  company: "Northstar Construction",
  source: "architect referral",
  project_name: "Riverfront Residences",
  project_location: "Minneapolis, MN",
  product_category: "fiber cement facade panels",
  project_stage: "design development",
  estimated_value: "425000",
  deadline: "2026-09-18",
  decision_maker_role: "Preconstruction Director",
  message:
    "We need a quote and technical review for facade panels on a 240-unit residential project. The architect is finalizing the specification this month.",
}

const NAV_ITEMS = [
  { label: "Opportunity Lab", icon: Target, active: true },
  { label: "Agent Runs", icon: Network, active: false },
  { label: "Evidence", icon: FileSearch, active: false },
  { label: "Analytics", icon: Gauge, active: false },
]

type ResultTab = "overview" | "evidence" | "trace" | "response"

const RESULT_TABS: { id: ResultTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "evidence", label: "Evidence" },
  { id: "trace", label: "Agent trace" },
  { id: "response", label: "Response" },
]

function Field({
  id,
  label,
  children,
  className,
  required,
}: {
  id: string
  label: string
  children: ReactNode
  className?: string
  required?: boolean
}) {
  return (
    <div className={cn("space-y-2", className)}>
      <Label htmlFor={id}>
        {label}
        {required && <span className="text-primary">*</span>}
      </Label>
      {children}
    </div>
  )
}

function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: typeof Activity
  label: string
  value: string
  detail: string
}) {
  return (
    <div className="rounded-xl border border-border/70 bg-card/55 p-4 backdrop-blur-sm">
      <div className="mb-4 flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">{label}</span>
        <Icon className="size-4 text-primary" />
      </div>
      <div className="text-xl font-semibold tracking-tight">{value}</div>
      <p className="mt-1 text-xs text-muted-foreground">{detail}</p>
    </div>
  )
}

function AnalysisSkeleton() {
  return (
    <div className="space-y-6 py-2">
      <div className="flex items-center gap-3 rounded-lg border border-primary/20 bg-primary/5 p-4">
        <LoaderCircle className="size-5 animate-spin text-primary" />
        <div>
          <p className="text-sm font-medium">Specialist agents are working</p>
          <p className="text-xs text-muted-foreground">
            Researching account, project, and intent signals in parallel.
          </p>
        </div>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        {[0, 1, 2].map((item) => (
          <div key={item} className="space-y-3 rounded-lg border border-border/60 p-4">
            <Skeleton className="h-8 w-8 rounded-lg" />
            <Skeleton className="h-3 w-2/3" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-4/5" />
          </div>
        ))}
      </div>
      <Skeleton className="h-28 w-full" />
    </div>
  )
}

function EmptyResult() {
  return (
    <div className="flex min-h-[430px] flex-col items-center justify-center rounded-xl border border-dashed border-border/80 bg-background/25 px-8 text-center">
      <div className="relative mb-6">
        <div className="absolute inset-0 scale-150 rounded-full bg-primary/10 blur-xl" />
        <div className="relative grid size-14 place-items-center rounded-2xl border border-primary/25 bg-primary/10">
          <Network className="size-6 text-primary" />
        </div>
      </div>
      <h3 className="text-base font-semibold">Your decision room is ready</h3>
      <p className="mt-2 max-w-sm text-sm leading-6 text-muted-foreground">
        Run the prefilled opportunity to see specialist evidence, qualification logic, agent trace,
        and a response ready for human review.
      </p>
      <div className="mt-7 flex items-center gap-2 text-xs text-muted-foreground">
        <Bot className="size-3.5" />
        Three specialists · one auditable decision
      </div>
    </div>
  )
}

function TierBadge({ tier }: { tier: OpportunityOutcome["decision"]["tier"] }) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "uppercase",
        tier === "Pursue" && "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
        tier === "Review" && "border-amber-400/30 bg-amber-400/10 text-amber-300",
        tier === "Pass" && "border-slate-400/30 bg-slate-400/10 text-slate-300",
      )}
    >
      <CircleDot />
      {tier}
    </Badge>
  )
}

function ResultView({ result }: { result: OpportunityOutcome }) {
  const [tab, setTab] = useState<ResultTab>("overview")
  const [copied, setCopied] = useState(false)

  async function copyResponse() {
    await navigator.clipboard.writeText(
      `${result.brief.response_subject}\n\n${result.brief.response_body}`,
    )
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1800)
  }

  return (
    <div>
      <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="max-w-xl">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <TierBadge tier={result.decision.tier} />
            <Badge variant="outline" className="text-muted-foreground">
              <ShieldCheck />
              {result.routing_status.replaceAll("_", " ")}
            </Badge>
          </div>
          <h3 className="text-xl font-semibold leading-snug tracking-tight">
            {result.brief.executive_summary}
          </h3>
        </div>
        <div className="min-w-28 rounded-xl border border-primary/20 bg-primary/5 p-4 text-center">
          <div className="text-4xl font-semibold tracking-[-0.06em] text-primary">
            {result.decision.score}
          </div>
          <div className="mt-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            Fit score
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-lg bg-secondary/35 p-1">
        <div className="grid grid-cols-2 gap-1 sm:grid-cols-4">
          {RESULT_TABS.map((item) => (
            <Button
              key={item.id}
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => setTab(item.id)}
              className={cn(
                "text-xs text-muted-foreground",
                tab === item.id && "bg-background text-foreground shadow-sm hover:bg-background",
              )}
            >
              {item.label}
            </Button>
          ))}
        </div>
      </div>

      <div className="mt-6 min-h-[340px]">
        {tab === "overview" && (
          <div className="space-y-6">
            <div>
              <div className="mb-2 flex items-center justify-between text-xs">
                <span className="font-medium">Qualification confidence</span>
                <span className="font-mono text-muted-foreground">
                  {result.decision.score}/100
                </span>
              </div>
              <Progress value={result.decision.score} />
            </div>

            <div className="rounded-xl border border-border/70 bg-background/30 p-5">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold">
                <Target className="size-4 text-primary" />
                Recommended angle
              </div>
              <p className="text-sm leading-6 text-muted-foreground">
                {result.brief.recommended_angle}
              </p>
            </div>

            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  Positive signals
                </h4>
                <div className="space-y-2.5">
                  {result.decision.reasons.map((reason) => (
                    <div key={reason} className="flex items-start gap-2.5 text-sm">
                      <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-primary" />
                      <span>{reason}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                  Information gaps
                </h4>
                {result.decision.missing_information.length ? (
                  <div className="space-y-2.5">
                    {result.decision.missing_information.map((gap) => (
                      <div key={gap} className="flex items-start gap-2.5 text-sm">
                        <Search className="mt-0.5 size-4 shrink-0 text-amber-300" />
                        <span>{gap}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No material gaps detected.</p>
                )}
              </div>
            </div>
          </div>
        )}

        {tab === "evidence" && (
          <div className="space-y-3">
            {result.findings.map((finding) => (
              <div
                key={finding.agent}
                className="rounded-xl border border-border/70 bg-background/30 p-5"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <div className="grid size-9 place-items-center rounded-lg bg-primary/10 text-primary">
                      <Bot className="size-4" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold capitalize">
                        {finding.agent.replaceAll("_", " ")}
                      </h4>
                      <p className="text-xs text-muted-foreground">Specialist finding</p>
                    </div>
                  </div>
                  <Badge variant="secondary">{Math.round(finding.confidence * 100)}%</Badge>
                </div>
                <p className="mt-4 text-sm leading-6 text-foreground/90">{finding.summary}</p>
                <div className="mt-4 space-y-2 border-t border-border/60 pt-4">
                  {finding.evidence.map((evidence) => (
                    <div key={evidence} className="flex items-start gap-2 text-xs text-muted-foreground">
                      <Check className="mt-0.5 size-3.5 shrink-0 text-primary" />
                      {evidence}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "trace" && (
          <div className="relative space-y-0 pl-1">
            {result.agent_trace.map((step, index) => (
              <div key={`${step}-${index}`} className="relative flex gap-4 pb-5 last:pb-0">
                {index < result.agent_trace.length - 1 && (
                  <div className="absolute left-[15px] top-8 h-[calc(100%-1rem)] w-px bg-border" />
                )}
                <div className="z-10 grid size-8 shrink-0 place-items-center rounded-full border border-primary/25 bg-primary/10 text-primary">
                  {index === result.agent_trace.length - 1 ? (
                    <ClipboardCheck className="size-3.5" />
                  ) : (
                    <span className="font-mono text-[10px]">{index + 1}</span>
                  )}
                </div>
                <div className="pt-1.5">
                  <p className="text-sm">{step}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "response" && (
          <div className="space-y-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
                  Ready for human review
                </p>
                <h4 className="mt-1 text-base font-semibold">{result.brief.response_subject}</h4>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={copyResponse}>
                {copied ? <Check /> : <Copy />}
                {copied ? "Copied" : "Copy"}
              </Button>
            </div>
            <div className="whitespace-pre-wrap rounded-xl border border-border/70 bg-background/45 p-5 font-mono text-[13px] leading-6 text-foreground/90">
              {result.brief.response_body}
            </div>
            <div>
              <h4 className="mb-3 text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                Discovery questions
              </h4>
              <div className="space-y-2">
                {result.brief.discovery_questions.map((question, index) => (
                  <div
                    key={question}
                    className="flex gap-3 rounded-lg border border-border/60 bg-background/25 p-3 text-sm"
                  >
                    <span className="font-mono text-xs text-primary">0{index + 1}</span>
                    {question}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <Separator className="my-5" />
      <div className="flex flex-wrap items-center justify-between gap-3 text-[11px] text-muted-foreground">
        <span className="font-mono">{result.opportunity_id}</span>
        <span>{result.latency_ms.toLocaleString()} ms end-to-end</span>
      </div>
    </div>
  )
}

function App() {
  const [form, setForm] = useState<OpportunityForm>(INITIAL_FORM)
  const [result, setResult] = useState<OpportunityOutcome | null>(null)
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    fetch(apiUrl("/health"))
      .then((response) => response.json() as Promise<HealthStatus>)
      .then((status) => active && setHealth(status))
      .catch(() => active && setHealth(null))
    return () => {
      active = false
    }
  }, [])

  function updateField<K extends keyof OpportunityForm>(key: K, value: OpportunityForm[K]) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function analyze(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError(null)

    const optional = (value: string) => value.trim() || null
    const payload = {
      ...form,
      contact_name: optional(form.contact_name),
      source: optional(form.source) ?? "website",
      product_category: optional(form.product_category),
      project_name: optional(form.project_name),
      project_location: optional(form.project_location),
      project_stage: optional(form.project_stage),
      estimated_value: form.estimated_value ? Number(form.estimated_value) : null,
      deadline: optional(form.deadline),
      decision_maker_role: optional(form.decision_maker_role),
    }

    try {
      const response = await fetch(apiUrl("/opportunities/sync"), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      })
      if (!response.ok) {
        throw new Error(`Analysis failed (${response.status}). Check the submitted fields.`)
      }
      setResult((await response.json()) as OpportunityOutcome)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to analyze this opportunity.")
    } finally {
      setLoading(false)
    }
  }

  function reset() {
    setForm(INITIAL_FORM)
    setResult(null)
    setError(null)
  }

  return (
    <div className="app-shell relative min-h-screen overflow-hidden">
      <div className="grid-overlay pointer-events-none absolute inset-0" />
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-sidebar-border bg-sidebar/95 px-4 py-5 backdrop-blur-xl xl:flex">
        <div className="flex items-center gap-3 px-2">
          <div className="grid size-9 place-items-center rounded-xl bg-sidebar-primary text-sidebar-primary-foreground shadow-[0_0_28px_-8px_var(--sidebar-primary)]">
            <Layers3 className="size-5" />
          </div>
          <div>
            <div className="font-semibold tracking-tight text-sidebar-foreground">BuildSignal</div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.18em] text-sidebar-foreground/45">
              GTM intelligence
            </div>
          </div>
        </div>

        <nav className="mt-10 space-y-1">
          <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-sidebar-foreground/35">
            Workspace
          </p>
          {NAV_ITEMS.map(({ label, icon: Icon, active }) => (
            <div
              key={label}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm"
                  : "text-sidebar-foreground/50",
              )}
            >
              <Icon className={cn("size-4", active && "text-sidebar-primary")} />
              <span>{label}</span>
              {!active && <span className="ml-auto text-[9px] uppercase tracking-wider">Soon</span>}
            </div>
          ))}
        </nav>

        <div className="mt-auto rounded-xl border border-sidebar-border bg-sidebar-accent/40 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-sidebar-foreground">Agent runtime</span>
            <span
              className={cn(
                "size-2 rounded-full",
                health?.status === "ok"
                  ? "bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,.8)]"
                  : "bg-amber-300",
              )}
            />
          </div>
          <p className="mt-2 text-xs leading-5 text-sidebar-foreground/45">
            {health
              ? `${health.demo_mode ? "Deterministic demo" : "Live OpenAI"} mode · ${health.queued} queued`
              : "Checking API connection…"}
          </p>
        </div>
      </aside>

      <main className="relative z-10 xl:pl-64">
        <header className="border-b border-border/60 bg-background/45 px-5 py-4 backdrop-blur-xl sm:px-8 lg:px-10">
          <div className="mx-auto flex max-w-[1500px] items-center justify-between gap-4">
            <div className="flex items-center gap-3 xl:hidden">
              <div className="grid size-9 place-items-center rounded-xl bg-primary text-primary-foreground">
                <Layers3 className="size-5" />
              </div>
              <span className="font-semibold">BuildSignal</span>
            </div>
            <div className="hidden xl:block">
              <p className="text-sm font-medium">Opportunity intelligence</p>
              <p className="text-xs text-muted-foreground">
                Multi-agent qualification workspace
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="hidden border-primary/20 bg-primary/5 sm:flex">
                <Sparkles className="text-primary" />
                {health?.demo_mode === false ? "OpenAI live" : "Safe demo"}
              </Badge>
              <Button variant="outline" size="icon" aria-label="Refresh status" onClick={() => location.reload()}>
                <RefreshCcw />
              </Button>
              <div className="grid size-9 place-items-center rounded-full border border-border bg-secondary text-xs font-semibold">
                BX
              </div>
            </div>
          </div>
        </header>

        <div className="mx-auto max-w-[1500px] px-5 py-8 sm:px-8 lg:px-10 lg:py-10">
          <section className="mb-8">
            <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-primary">
              <Activity className="size-3.5" />
              Agentic revenue intelligence
            </div>
            <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
              <div>
                <h1 className="max-w-3xl text-3xl font-semibold leading-[1.08] tracking-[-0.04em] sm:text-4xl lg:text-5xl">
                  Turn project signals into
                  <span className="text-primary"> qualified pipeline.</span>
                </h1>
                <p className="mt-4 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
                  Parallel specialists assess the account, project, and buyer intent. Every decision
                  stays evidence-led, scored, and held for human approval.
                </p>
              </div>
              <Badge variant="secondary" className="w-fit px-3 py-1.5 font-mono">
                LangGraph · 3 specialists · 1 critic
              </Badge>
            </div>
          </section>

          <section className="mb-6 grid gap-3 sm:grid-cols-3">
            <MetricCard
              icon={Users}
              label="Specialist agents"
              value="3 in parallel"
              detail="Account, project, and intent research"
            />
            <MetricCard
              icon={ShieldCheck}
              label="Action policy"
              value="Human governed"
              detail="No outbound action without approval"
            />
            <MetricCard
              icon={Activity}
              label="Runtime"
              value={health?.status === "ok" ? "Operational" : "Connecting"}
              detail={health?.demo_mode === false ? "OpenAI synthesis enabled" : "Deterministic demo mode"}
            />
          </section>

          <section className="grid items-start gap-6 min-[1380px]:grid-cols-[minmax(400px,.82fr)_minmax(580px,1.18fr)]">
            <Card>
              <CardHeader className="flex flex-row items-start justify-between gap-4">
                <div>
                  <CardTitle>Opportunity intake</CardTitle>
                  <CardDescription className="mt-2">
                    Add the commercial and project evidence available to the revenue team.
                  </CardDescription>
                </div>
                <div className="grid size-9 shrink-0 place-items-center rounded-lg bg-secondary text-muted-foreground">
                  <Building2 className="size-4" />
                </div>
              </CardHeader>
              <CardContent>
                <form onSubmit={analyze} className="space-y-6">
                  <div>
                    <div className="mb-4 flex items-center gap-2">
                      <span className="font-mono text-[10px] text-primary">01</span>
                      <span className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                        Account
                      </span>
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field id="contact_name" label="Contact">
                        <Input
                          id="contact_name"
                          value={form.contact_name}
                          onChange={(event) => updateField("contact_name", event.target.value)}
                        />
                      </Field>
                      <Field id="email" label="Business email" required>
                        <Input
                          id="email"
                          type="email"
                          required
                          value={form.email}
                          onChange={(event) => updateField("email", event.target.value)}
                        />
                      </Field>
                      <Field id="company" label="Company" required>
                        <Input
                          id="company"
                          required
                          value={form.company}
                          onChange={(event) => updateField("company", event.target.value)}
                        />
                      </Field>
                      <Field id="decision_maker_role" label="Buyer role">
                        <Input
                          id="decision_maker_role"
                          value={form.decision_maker_role}
                          onChange={(event) =>
                            updateField("decision_maker_role", event.target.value)
                          }
                        />
                      </Field>
                    </div>
                  </div>

                  <Separator />

                  <div>
                    <div className="mb-4 flex items-center gap-2">
                      <span className="font-mono text-[10px] text-primary">02</span>
                      <span className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                        Project signal
                      </span>
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <Field id="project_name" label="Project">
                        <Input
                          id="project_name"
                          value={form.project_name}
                          onChange={(event) => updateField("project_name", event.target.value)}
                        />
                      </Field>
                      <Field id="project_location" label="Location">
                        <Input
                          id="project_location"
                          value={form.project_location}
                          onChange={(event) => updateField("project_location", event.target.value)}
                        />
                      </Field>
                      <Field id="product_category" label="Product category">
                        <Input
                          id="product_category"
                          value={form.product_category}
                          onChange={(event) => updateField("product_category", event.target.value)}
                        />
                      </Field>
                      <Field id="project_stage" label="Project stage">
                        <Input
                          id="project_stage"
                          value={form.project_stage}
                          onChange={(event) => updateField("project_stage", event.target.value)}
                        />
                      </Field>
                      <Field id="estimated_value" label="Estimated value ($)">
                        <Input
                          id="estimated_value"
                          type="number"
                          min="0"
                          value={form.estimated_value}
                          onChange={(event) => updateField("estimated_value", event.target.value)}
                        />
                      </Field>
                      <Field id="deadline" label="Decision deadline">
                        <Input
                          id="deadline"
                          type="date"
                          value={form.deadline}
                          onChange={(event) => updateField("deadline", event.target.value)}
                        />
                      </Field>
                      <Field id="source" label="Signal source" className="sm:col-span-2">
                        <Input
                          id="source"
                          value={form.source}
                          onChange={(event) => updateField("source", event.target.value)}
                        />
                      </Field>
                      <Field
                        id="message"
                        label="Inbound message"
                        required
                        className="sm:col-span-2"
                      >
                        <Textarea
                          id="message"
                          required
                          value={form.message}
                          onChange={(event) => updateField("message", event.target.value)}
                        />
                      </Field>
                    </div>
                  </div>

                  {error && (
                    <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-red-200">
                      {error}
                    </div>
                  )}

                  <div className="flex flex-col-reverse gap-3 sm:flex-row">
                    <Button type="button" variant="outline" onClick={reset} className="sm:w-28">
                      Reset
                    </Button>
                    <Button type="submit" size="lg" disabled={loading} className="flex-1">
                      {loading ? (
                        <>
                          <LoaderCircle className="animate-spin" />
                          Agents are working
                        </>
                      ) : (
                        <>
                          Run multi-agent analysis
                          <ArrowRight />
                        </>
                      )}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            <Card className="min-[1380px]:sticky min-[1380px]:top-6">
              <CardHeader className="flex flex-row items-start justify-between gap-4">
                <div>
                  <CardTitle>Decision room</CardTitle>
                  <CardDescription className="mt-2">
                    Evidence, qualification, strategy, and the approval-ready response.
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span className="size-2 rounded-full bg-primary" />
                  Auditable
                </div>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <AnalysisSkeleton />
                ) : result ? (
                  <ResultView key={result.opportunity_id} result={result} />
                ) : (
                  <EmptyResult />
                )}
              </CardContent>
            </Card>
          </section>

          <footer className="mt-8 flex flex-col gap-2 border-t border-border/50 pt-5 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
            <span>BuildSignal GTM · human-governed opportunity intelligence</span>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <Mail className="size-3.5" /> Draft only
              </span>
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="size-3.5" /> No autonomous send
              </span>
            </div>
          </footer>
        </div>
      </main>
    </div>
  )
}

export default App
