# ruff: noqa: E501
"""Self-contained presentation UI for the BuildSignal live demo."""


def build_demo_html() -> str:
    return r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>BuildSignal GTM</title>
  <style>
    :root{--ink:#0d1b1e;--panel:#13272b;--line:#284247;--mint:#6ee7b7;--gold:#f2c66d;--text:#edf7f5;--muted:#91aaa6;--danger:#fb7185}
    *{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at 82% 0,#193b3c 0,transparent 32%),#091416;color:var(--text);font:15px/1.45 Inter,ui-sans-serif,system-ui,sans-serif}
    .shell{max-width:1240px;margin:auto;padding:38px 28px 60px}.eyebrow{color:var(--mint);font-size:12px;font-weight:800;letter-spacing:.18em;text-transform:uppercase}
    h1{font-size:clamp(36px,6vw,70px);line-height:.95;letter-spacing:-.055em;margin:12px 0 16px;max-width:850px}h1 span{color:var(--gold)}
    .lede{font-size:18px;color:var(--muted);max-width:700px;margin-bottom:30px}.grid{display:grid;grid-template-columns:.88fr 1.12fr;gap:18px}.card{background:rgba(19,39,43,.88);border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:0 20px 55px rgba(0,0,0,.2)}
    h2{margin:0 0 16px;font-size:17px}.fields{display:grid;grid-template-columns:1fr 1fr;gap:12px}.wide{grid-column:1/-1}label{display:block;color:var(--muted);font-size:12px;margin:0 0 5px}input,textarea{width:100%;border:1px solid var(--line);background:#0b1c1f;color:var(--text);border-radius:9px;padding:10px 11px;font:inherit;outline:none}input:focus,textarea:focus{border-color:var(--mint)}textarea{min-height:88px;resize:vertical}
    button{width:100%;margin-top:15px;border:0;border-radius:10px;padding:13px;background:var(--mint);color:#082019;font-weight:900;cursor:pointer}button:disabled{opacity:.55;cursor:wait}.placeholder{color:var(--muted);padding:85px 20px;text-align:center;border:1px dashed var(--line);border-radius:12px}
    .topline{display:flex;justify-content:space-between;gap:12px;align-items:flex-start}.score{font-size:48px;font-weight:900;letter-spacing:-.05em;color:var(--gold)}.pill{display:inline-block;padding:5px 9px;border-radius:99px;background:#173f35;color:var(--mint);font-size:12px;font-weight:800}.section{border-top:1px solid var(--line);padding-top:15px;margin-top:15px}.trace{display:flex;flex-wrap:wrap;gap:7px}.step{padding:6px 8px;background:#0b1c1f;border:1px solid var(--line);border-radius:7px;font-size:12px}.finding{margin:9px 0;padding:11px;background:#0b1c1f;border-left:3px solid var(--mint);border-radius:5px}.finding b{display:block;text-transform:capitalize;margin-bottom:3px}.muted{color:var(--muted)}pre{white-space:pre-wrap;background:#0b1c1f;padding:13px;border-radius:9px;border:1px solid var(--line);font:13px/1.5 ui-monospace,SFMono-Regular,monospace}.error{color:var(--danger)}
    @media(max-width:850px){.grid{grid-template-columns:1fr}.fields{grid-template-columns:1fr}.wide{grid-column:auto}}
  </style>
</head>
<body><main class="shell">
  <div class="eyebrow">Agentic revenue intelligence</div>
  <h1>Turn project signals into <span>qualified pipeline.</span></h1>
  <p class="lede">Three specialist agents research every building-material opportunity in parallel. A critic checks the evidence before sales strategy is generated.</p>
  <div class="grid">
    <section class="card"><h2>Opportunity intake</h2><form id="form"><div class="fields">
      <div><label>Contact</label><input name="contact_name" value="Maria Chen"></div>
      <div><label>Business email</label><input name="email" type="email" required value="maria@northstarbuild.com"></div>
      <div><label>Company</label><input name="company" required value="Northstar Construction"></div>
      <div><label>Source</label><input name="source" value="architect referral"></div>
      <div><label>Project</label><input name="project_name" value="Riverfront Residences"></div>
      <div><label>Location</label><input name="project_location" value="Minneapolis, MN"></div>
      <div><label>Product category</label><input name="product_category" value="fiber cement facade panels"></div>
      <div><label>Project stage</label><input name="project_stage" value="design development"></div>
      <div><label>Estimated value ($)</label><input name="estimated_value" type="number" value="425000"></div>
      <div><label>Decision deadline</label><input name="deadline" value="2026-09-18"></div>
      <div class="wide"><label>Buyer role</label><input name="decision_maker_role" value="Preconstruction Director"></div>
      <div class="wide"><label>Inbound message</label><textarea name="message" required>We need a quote and technical review for facade panels on a 240-unit residential project. The architect is finalizing the specification this month.</textarea></div>
    </div><button id="run">Run multi-agent analysis</button></form></section>
    <section class="card"><h2>Decision room</h2><div id="result" class="placeholder">Run the example to watch the agent team qualify the opportunity.</div></section>
  </div>
</main>
<script>
const form=document.getElementById('form'), result=document.getElementById('result'), run=document.getElementById('run');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
form.addEventListener('submit',async e=>{e.preventDefault();run.disabled=true;run.textContent='Agents are working…';result.innerHTML='<div class="placeholder">Researching account, project, and intent signals…</div>';
  const raw=Object.fromEntries(new FormData(form));raw.estimated_value=raw.estimated_value?Number(raw.estimated_value):null;
  Object.keys(raw).forEach(k=>{if(raw[k]==='')raw[k]=null});
  try{const res=await fetch('/opportunities/sync',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(raw)});if(!res.ok)throw new Error(await res.text());const d=await res.json();
    result.innerHTML=`<div class="topline"><div><span class="pill">${esc(d.decision.tier)}</span><h2>${esc(d.brief.executive_summary)}</h2></div><div class="score">${d.decision.score}</div></div>
      <div class="section"><div class="trace">${d.agent_trace.map(x=>`<span class="step">${esc(x)}</span>`).join('')}</div></div>
      <div class="section"><b>Specialist evidence</b>${d.findings.map(f=>`<div class="finding"><b>${esc(f.agent.replaceAll('_',' '))}</b><span class="muted">${esc(f.summary)}</span></div>`).join('')}</div>
      <div class="section"><b>Recommended angle</b><p>${esc(d.brief.recommended_angle)}</p></div>
      <div class="section"><b>Draft response · ${esc(d.routing_status.replaceAll('_',' '))}</b><pre>${esc(d.brief.response_body)}</pre></div>
      <div class="muted">Completed in ${d.latency_ms} ms · ${esc(d.opportunity_id)}</div>`;
  }catch(err){result.innerHTML=`<p class="error">${esc(err.message)}</p>`}finally{run.disabled=false;run.textContent='Run multi-agent analysis'}});
</script></body></html>"""
