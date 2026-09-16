"""Local browser annotation tool for the SpotifyCares golden candidates."""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATES = ROOT / "data" / "processed" / "golden_annotation_candidates.jsonl"
DEFAULT_ANNOTATIONS = ROOT / "data" / "annotations"
HOST = "127.0.0.1"
PORT = 8765

INTENTS = [
    "Playback reliability",
    "App, device, and platform behavior",
    "Content or catalog availability",
    "Playlist, library, and music organization",
    "Premium, subscription, and plan status",
    "Billing, payment, refund, and card issues",
    "Account access, identity, and security",
    "Family and student eligibility",
    "Downloads and offline listening",
    "Ads and free-tier experience",
]
STATES = [
    "SYMPTOM_REPORTED",
    "CONTEXT_COLLECTED",
    "FIRST_LINE_ACTION_PROPOSED",
    "ACTION_RESULT_REPORTED",
    "REPEATED_FAILURE_OR_BROADER_INCIDENT",
    "PRIVATE_ACCOUNT_CONTEXT_REQUIRED",
    "SPECIALIST_OR_PRODUCT_INVESTIGATION",
    "RESOLVED",
    "MONITORING",
]
ACTIONS = [
    "ASK_PLATFORM_CONTEXT",
    "ASK_SYMPTOM_EVIDENCE",
    "ASK_SCOPE_OR_ENVIRONMENT",
    "ASK_CATALOG_CONTEXT",
    "SESSION_RESET",
    "REINSTALL_OR_CLEAN_INSTALL",
    "BROWSER_REMEDIATION",
    "NETWORK_REMEDIATION",
    "PROVIDE_HELP_RESOURCE",
    "REQUEST_SECURE_ACCOUNT_DETAILS",
    "MOVE_TO_DM_OR_SECURE_CHANNEL",
    "ESCALATE_TECHNICAL_OR_PRODUCT_ISSUE",
    "CONFIRM_AND_MONITOR",
]
REQUIREMENTS = [
    "PLATFORM_CONTEXT",
    "SYMPTOM_EVIDENCE",
    "SCOPE_OR_ENVIRONMENT",
    "CATALOG_CONTEXT",
    "SECURE_ACCOUNT_CONTEXT",
    "PRIOR_ATTEMPTS_AND_TIMING",
]
REQUIREMENT_STATUSES = ["missing", "present", "conflicting", "private", "unknown", "not_required"]
ACTION_RESULTS = ["attempted", "failed", "partially_helped", "improved", "resolved", "unknown"]
EXPLICITNESS = ["explicit", "inferred", "ambiguous"]
OUTCOMES = ["resolved", "monitoring_or_improved", "unresolved", "escalated_or_handoff", "dm_ended", "unknown"]
ESCALATION = ["yes", "no", "uncertain"]
EVIDENCE = ["visible", "partial", "dm_ended", "unknown"]
CONFIDENCE = ["high", "medium", "low"]
INTENT_STATUSES = ["labelled", "ambiguous", "insufficient_evidence", "unlabelled"]
STATE_STATUSES = ["labelled", "ambiguous", "insufficient_evidence", "unlabelled"]
REASON_CODES = [
    "PRIVATE_ACCOUNT_CONTEXT", "SECURITY_OR_ACCOUNT_ACCESS", "BILLING_PAYMENT_OR_REFUND",
    "REPEATED_FAILURE_OR_RELAPSE", "BROADER_INCIDENT", "SPECIALIST_OR_PRODUCT_INVESTIGATION",
    "INSUFFICIENT_EVIDENCE", "CONFLICTING_EVIDENCE", "HISTORICAL_POLICY_OR_CATALOG_LIMITATION",
    "OTHER_HIGH_RISK",
]
SAFE_ID = re.compile(r"^[A-Za-z0-9_.-]{1,80}$")


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def escape(value: object) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def options(values: list[str], blank: str = "Select...") -> str:
    return '<option value="">' + blank + '</option>' + "".join(
        f'<option value={escape(value)}>{value}</option>' for value in values
    )


def load_annotations(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    annotations = {}
    for record in read_jsonl(path):
        if record.get("journey_id"):
            annotations[record["journey_id"]] = record
    return annotations


def save_annotations(path: Path, annotations: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in annotations.values())
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", dir=path.parent, delete=False) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    temporary.replace(path)


def validate_annotation(record: dict, candidates_by_id: dict[str, dict], annotator_id: str) -> list[str]:
    errors: list[str] = []
    journey_id = record.get("journey_id")
    candidate = candidates_by_id.get(journey_id)
    if candidate is None:
        errors.append("journey_id is not a golden annotation candidate")
        return errors
    if record.get("annotator_id") != annotator_id:
        errors.append("annotator_id does not match the selected annotation file")
    if not record.get("annotation_id"):
        errors.append("annotation_id is required")
    if record.get("root_tweet_id") != candidate.get("root_tweet_id"):
        errors.append("root_tweet_id does not match the source journey")
    if record.get("intent") and record["intent"] not in INTENTS:
        errors.append("intent is not in the frozen vocabulary")
    if record.get("current_state") and record["current_state"] not in STATES:
        errors.append("current_state is not in the frozen vocabulary")
    if record.get("intent_status") not in INTENT_STATUSES:
        errors.append("intent_status is required")
    if record.get("state_status") not in STATE_STATUSES:
        errors.append("state_status is required")
    for field, allowed in (("observed_next_action", ACTIONS + ["UNKNOWN", "UNLABELLED"]),
                           ("ideal_next_action", ACTIONS), ("outcome", OUTCOMES),
                           ("escalation_eligible", ESCALATION), ("evidence_visibility", EVIDENCE),
                           ("confidence", CONFIDENCE)):
        if field == "ideal_next_action" and record.get(field) in (None, ""):
            continue
        if record.get(field) not in allowed:
            errors.append(f"{field} is required and must use the allowed vocabulary")
    if not isinstance(record.get("missing_information"), list):
        errors.append("missing_information must be a list")
    if not isinstance(record.get("attempted_actions"), list):
        errors.append("attempted_actions must be a list")
    for item in record.get("missing_information", []):
        if item.get("requirement") not in REQUIREMENTS or item.get("status") not in REQUIREMENT_STATUSES:
            errors.append("missing-information items must use the guide vocabularies")
    for item in record.get("attempted_actions", []):
        if item.get("action") not in ACTIONS or item.get("explicitness") not in EXPLICITNESS or item.get("result") not in ACTION_RESULTS:
            errors.append("attempted actions must use the guide vocabularies")
    for action in record.get("observed_next_actions", []):
        if action not in ACTIONS:
            errors.append("observed_next_actions contains an invalid action")
    if record.get("ambiguity_flag") and not record.get("ambiguity_reason", "").strip():
        errors.append("ambiguity_reason is required when ambiguity is enabled")
    if record.get("confidence") == "low" and not (record.get("ambiguity_reason") or record.get("insufficient_evidence_reason")):
        errors.append("low confidence requires an ambiguity or insufficient-evidence reason")
    return errors


def page() -> str:
    intent_options = options(INTENTS)
    state_options = options(STATES)
    action_options = options(ACTIONS)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SpotifyCares Annotation Workspace</title>
<style>
:root {{ --ink:#17252b; --muted:#68777d; --line:#d9e2e1; --paper:#eef3f1; --panel:#fff; --teal:#086b68; --teal-dark:#123d40; --gold:#d69b2b; --customer:#fff5da; --support:#e4f2ef; --future:#789092; }}
* {{ box-sizing:border-box; }} body {{ margin:0; color:var(--ink); background:linear-gradient(135deg,#eef3f1 0%,#f8f8f4 55%,#e9f0ed 100%); font:15px/1.5 Georgia,serif; }}
header {{ position:sticky;top:0;z-index:5; padding:13px 24px; background:var(--teal-dark); color:white; box-shadow:0 3px 16px #102f3333; }}
header .bar, main {{ max-width:1540px; margin:auto; }} header .bar {{ display:flex; align-items:center; gap:18px; flex-wrap:wrap; }}
h1 {{ font:700 22px/1.1 Georgia,serif; margin:0; letter-spacing:.01em; }} .subtitle {{ color:#b8d6d1; font:13px/1.2 Arial,sans-serif; margin-top:4px; }} .brand {{ min-width:245px; }} .meta {{ margin-left:auto; display:flex; gap:8px; align-items:center; flex-wrap:wrap; }}
input, select, textarea, button {{ font:inherit; }} input, select, textarea {{ border:1px solid var(--line); border-radius:5px; padding:8px 9px; background:white; color:var(--ink); }}
header input {{ width:130px; }} button {{ border:0; border-radius:5px; padding:9px 13px; cursor:pointer; background:var(--teal); color:white; font-weight:bold; }} button.secondary {{ background:#e3ecea;color:var(--ink); }} button.warn {{ background:#a44935; }}
main {{ display:grid; grid-template-columns:minmax(0,1.65fr) minmax(380px,1fr); gap:24px; padding:25px 24px 40px; align-items:start; }} .card {{ background:rgba(255,255,255,.94); border:1px solid var(--line); border-radius:8px; padding:20px; margin-bottom:18px; box-shadow:0 8px 24px #24494d0b; }}
.conversation-panel {{ min-width:0; }} .decision-panel {{ min-width:0; position:sticky; top:92px; max-height:calc(100vh - 108px); overflow:auto; padding-right:3px; }} .journey-head {{ display:flex; justify-content:space-between; gap:12px; align-items:start; border-bottom:1px solid var(--line); padding-bottom:14px; margin-bottom:18px; }} h2,h3 {{ margin:0 0 8px; }} h2 {{ font-size:20px; }} h3 {{ font-size:15px; color:var(--teal); text-transform:uppercase; letter-spacing:.07em; }} .small {{ color:var(--muted); font-size:13px; }}
.notice {{ background:#fff7dd; border-left:4px solid var(--gold); padding:12px 14px; margin-bottom:20px; }} .future-note {{ color:var(--future); font-size:13px; margin:7px 0 14px; }} .conversation {{ padding:0 4px; }} .message {{ max-width:82%; border:1px solid var(--line); padding:13px 15px; margin:14px 0; white-space:pre-wrap; overflow-wrap:anywhere; box-shadow:0 3px 10px #24494d0c; }} .message.customer {{ margin-right:auto; background:var(--customer); border-radius:4px 14px 14px 14px; border-left:4px solid var(--gold); }} .message.support {{ margin-left:auto; background:var(--support); border-radius:14px 4px 14px 14px; border-right:4px solid var(--teal); }} .message.current {{ outline:3px solid #d69b2b99; box-shadow:0 0 0 7px #d69b2b1c,0 7px 16px #24494d18; }} .message.future {{ opacity:.52; filter:saturate(.65); }} .role {{ font:700 12px/1.2 Arial,sans-serif; text-transform:uppercase; letter-spacing:.08em; }} .message.current .role {{ color:#8d5d00; }} .message.future .role {{ color:var(--future); }} .divider {{ display:flex; align-items:center; gap:10px; color:var(--teal); font:700 11px/1 Arial,sans-serif; letter-spacing:.12em; text-transform:uppercase; margin:25px 0 10px; }} .divider::before,.divider::after {{ content:""; height:1px; background:var(--teal); opacity:.45; flex:1; }}
.decision {{ padding:0 2px; }} .decision > h2 {{ margin-bottom:3px; }} .decision-intro {{ margin:0 0 18px; }} .decision-section {{ border-top:1px solid var(--line); padding:17px 0 4px; }} .decision-section:first-of-type {{ border-top:0; padding-top:4px; }} .section-kicker {{ display:flex; justify-content:space-between; align-items:baseline; gap:12px; margin-bottom:9px; }} .section-kicker .small {{ font-family:Arial,sans-serif; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px 12px; }} label {{ display:block; font-weight:bold; margin:7px 0 4px; }} .full {{ grid-column:1/-1; }} textarea {{ width:100%; min-height:70px; resize:vertical; }} .repeat {{ border-top:1px dashed var(--line); margin-top:12px; padding-top:12px; }} .repeat h3 {{ margin-bottom:4px; }} .repeat-row {{ display:grid; grid-template-columns:1.3fr 1fr 1fr auto; gap:7px; align-items:center; margin:7px 0; }} .repeat-row input, .repeat-row select {{ min-width:0; width:100%; }} .status {{ min-height:24px; margin:12px 0 4px; }} .done {{ color:#146b42; font-weight:bold; }} .error {{ color:#a32920; white-space:pre-line; font-weight:bold; }}
@media(max-width:950px) {{ header {{ position:static; }} main {{ grid-template-columns:1fr; padding:14px; }} .meta {{ margin-left:0; width:100%; }} .decision-panel {{ position:static; max-height:none; overflow:visible; }} .message {{ max-width:94%; }} .repeat-row {{ grid-template-columns:1fr 1fr; }} }}
</style></head><body>
<header><div class="bar"><div class="brand"><h1>SpotifyCares Support Review</h1><div class="subtitle">Hiver SDE Intern Take-Home</div></div><div class="meta"><span>Progress: <strong id="progress">0 / 240</strong></span><label for="annotator" style="margin:0;color:white">Annotator</label><input id="annotator" value="annotator_1" pattern="[A-Za-z0-9_.\-]+"><button class="secondary" onclick="previous()">Previous</button><button class="secondary" onclick="next()">Next</button><button class="secondary" onclick="jump()">Jump to example</button><button onclick="save(event);return false">Save</button><button onclick="exportFile()">Export</button></div></div></header>
<main><section class="conversation-panel"><div class="card"><div class="journey-head"><div><h2 id="journey-id">Loading...</h2><div class="small" id="journey-meta"></div></div></div><div class="notice"><strong>Evaluation rule:</strong> Determine current state and intent from the current customer message and preceding context. Future support replies are used only for observed next action and later outcome. Do not use future replies to label the current state or intent.</div><div id="conversation" class="conversation"></div></div></section>
<section class="decision-panel"><form id="annotation-form" class="card decision" onsubmit="save(event)"><h2>Support decision</h2><div class="small decision-intro">Blank controls are intentional. Nothing is prefilled as a ground-truth prediction.</div>
<div class="decision-section"><div class="section-kicker"><h3>Understand the case</h3><span class="small">Current message + prior context</span></div><div class="grid"><div class="full"><label for="evaluation-point">Evaluation-point customer message</label><select id="evaluation-point"></select></div><div><label for="intent">Intent</label><select id="intent">{intent_options}</select></div><div><label for="intent-status">Intent status</label><select id="intent-status">{options(INTENT_STATUSES)}</select></div>
<div><label for="state">Current state</label><select id="state">{state_options}</select></div><div><label for="state-status">State status</label><select id="state-status">{options(STATE_STATUSES)}</select></div>
<div><label for="confidence">Overall confidence</label><select id="confidence">{options(CONFIDENCE)}</select></div></div></div>
<div class="decision-section"><div class="section-kicker"><h3>What has happened?</h3><span class="small">Keep the journey visible</span></div><div class="repeat"><h3>Missing information</h3><div id="missing-list"></div><button type="button" class="secondary" onclick="addMissing()">Add requirement</button></div><div class="repeat"><h3>Attempted actions (chronological)</h3><div id="attempted-list"></div><button type="button" class="secondary" onclick="addAttempt()">Add attempted action</button></div></div>
<div class="decision-section"><div class="section-kicker"><h3>What should happen next?</h3><span class="small">Separate history from recommendation</span></div><div class="grid"><div><label for="ideal">Ideal next action (optional)</label><select id="ideal">{options(ACTIONS, "None selected")}</select></div><div><label for="observed">Historical observed action</label><select id="observed">{options(ACTIONS + ["UNKNOWN", "UNLABELLED"])}</select></div></div></div>
<div class="decision-section"><div class="section-kicker"><h3>Trust / escalation</h3></div><div class="grid"><div><label for="escalation">Escalation eligible</label><select id="escalation">{options(ESCALATION)}</select></div><div><label for="visibility">Evidence visibility</label><select id="visibility">{options(EVIDENCE)}</select></div><div class="full"><label>Escalation reason codes</label><div id="reasons">''' + ''.join(f'<label style="display:inline-block;margin-right:12px;font-weight:normal"><input type="checkbox" value="{reason}"> {reason}</label>' for reason in REASON_CODES) + fr'''</div></div></div></div>
<div class="decision-section"><div class="section-kicker"><h3>Outcome</h3></div><div class="grid"><div><label for="outcome">Outcome</label><select id="outcome">{options(OUTCOMES)}</select></div><div><label for="ambiguity">Ambiguity</label><select id="ambiguity"><option value="">Select...</option><option value="false">No</option><option value="true">Yes</option></select></div><div class="full"><label for="ambiguity-reason">Ambiguity reason</label><textarea id="ambiguity-reason"></textarea></div><div class="full"><label for="insufficient-reason">Insufficient-evidence reason</label><textarea id="insufficient-reason"></textarea></div><div class="full"><label for="notes">Notes</label><textarea id="notes"></textarea></div></div></div>
<div class="status" id="status"></div><button type="submit">Save annotation</button> <button type="button" class="secondary" onclick="clearForm()">Clear unsaved fields</button></form></section></main>
<script>
const ACTIONS={json.dumps(ACTIONS)}; const REQUIREMENTS={json.dumps(REQUIREMENTS)}; const REQ_STATUS={json.dumps(REQUIREMENT_STATUSES)}; const RESULTS={json.dumps(ACTION_RESULTS)}; const EXPLICIT={json.dumps(EXPLICITNESS)};
let state={{records:[], annotations:{{}}, index:0, annotator:"annotator_1"}}; let dirty=false;
const $=id=>document.getElementById(id); const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
async function loadState(){{ if(dirty&&!confirm('You have unsaved changes. Continue without saving?')){{return}} const id=$('annotator').value.trim(); if(!/^[A-Za-z0-9_.-]{{1,80}}$/.test(id)){{alert('Use only letters, numbers, dot, underscore, or hyphen for annotator ID.');return}} state=await (await fetch('/api/state?annotator_id='+encodeURIComponent(id))).json(); state.annotator=id; dirty=false; render(); }}
function current(){{return state.records[state.index]}} function render(){{const r=current(); $('progress').textContent=(state.index+1)+' / '+state.records.length; $('journey-id').textContent=r.journey_id; $('journey-meta').textContent='Root '+r.root_tweet_id+' · '+r.message_count+' messages · '+r.reconstruction_status; const messages=r.messages||[]; const customers=messages.map((m,i)=>m.role==='customer'?i:-1).filter(i=>i>=0); const saved=state.annotations[r.journey_id]||{{}}; const selectedPoint=$('evaluation-point').value; const point=saved.evaluation_point_message_id||selectedPoint|| (messages[customers[customers.length-1]] && messages[customers[customers.length-1]].tweet_id); const pointIndex=messages.findIndex(x=>x.tweet_id===point); $('evaluation-point').innerHTML=customers.map(i=>'<option value="'+esc(messages[i].tweet_id)+'">'+esc(messages[i].tweet_id)+' · customer message '+(i+1)+'</option>').join(''); $('evaluation-point').value=point||''; $('conversation').innerHTML=messages.map((m,i)=>{{const isCurrent=i===pointIndex; const future=pointIndex>=0&&i>pointIndex; const divider=isCurrent?'<div class="divider">Current evaluation point</div>':i===pointIndex+1?'<div class="divider">Future evidence</div><p class="future-note">Future replies may be used for observed next action and later outcome only. Do not use them to label current intent or state.</p>':''; return divider+'<article class="message '+(m.role==='customer'?'customer':'support')+(isCurrent?' current':'')+(future?' future':'')+'"><div class="role">'+(m.role==='customer'?'Customer':'Spotify support')+(isCurrent?' · CURRENT CUSTOMER MESSAGE':'')+(future?' · FUTURE REPLY':'')+'</div><div class="small">'+esc(m.created_at)+' · '+esc(m.tweet_id)+'</div><div>'+esc(m.text)+'</div></article>'}}).join(''); fill(saved); }}
function set(id,value){{$(id).value=value??''}} function get(id){{return $(id).value}} function fill(a){{set('confidence',a.confidence);set('intent',a.intent);set('intent-status',a.intent_status);set('state',a.current_state);set('state-status',a.state_status);set('observed',a.observed_next_action);set('ideal',a.ideal_next_action);set('outcome',a.outcome);set('visibility',a.evidence_visibility);set('escalation',a.escalation_eligible);set('ambiguity',a.ambiguity_flag===true?'true':a.ambiguity_flag===false?'false':'');set('ambiguity-reason',a.ambiguity_reason);set('insufficient-reason',a.insufficient_evidence_reason);set('notes',a.notes); document.querySelectorAll('#reasons input').forEach(x=>x.checked=(a.escalation_reason_codes||[]).includes(x.value)); $('missing-list').innerHTML=''; (a.missing_information||[]).forEach(addMissing); $('attempted-list').innerHTML=''; (a.attempted_actions||[]).forEach(addAttempt); }}
function selectHtml(values,blank='Select...'){{return '<select>'+options(values,blank)+'</select>'}} function options(values,blank='Select...'){{return '<option value="">'+blank+'</option>'+values.map(x=>'<option value="'+esc(x)+'">'+esc(x)+'</option>').join('')}}
function addMissing(item={{}}){{const d=document.createElement('div');d.className='repeat-row missing';d.innerHTML=selectHtml(REQUIREMENTS,'Requirement')+selectHtml(REQ_STATUS,'Status')+'<input placeholder="Why needed" value="'+esc(item.why_needed)+'"><input placeholder="Candidate action / evidence refs" value="'+esc((item.candidate_action||[]).join(', '))+'"><button type="button" class="warn" onclick="this.parentElement.remove()">Remove</button>';d.querySelectorAll('select')[0].value=item.requirement||'';d.querySelectorAll('select')[1].value=item.status||'';$('missing-list').appendChild(d)}}
function addAttempt(item={{}}){{const d=document.createElement('div');d.className='repeat-row attempted';d.innerHTML=selectHtml(ACTIONS,'Action')+selectHtml(EXPLICIT,'Explicitness')+selectHtml(RESULTS,'Result')+'<input placeholder="Source message ID / result evidence / equivalence group" value="'+esc([item.source_message_id,item.result_evidence,item.equivalence_group].filter(Boolean).join(' | '))+'"><button type="button" class="warn" onclick="this.parentElement.remove()">Remove</button>';d.querySelectorAll('select')[0].value=item.action||'';d.querySelectorAll('select')[1].value=item.explicitness||'';d.querySelectorAll('select')[2].value=item.result||'';$('attempted-list').appendChild(d)}}
function collect(){{const r=current();const missing=[...document.querySelectorAll('.missing')].map(x=>{{const s=x.querySelectorAll('select'),i=x.querySelectorAll('input');return {{requirement:s[0].value,status:s[1].value,why_needed:i[0].value,safely_requestable:'unknown',candidate_action:i[1].value?i[1].value.split(',').map(v=>v.trim()).filter(Boolean):[],evidence_references:[]}}}});const attempted=[...document.querySelectorAll('.attempted')].map((x,n)=>{{const s=x.querySelectorAll('select'),i=x.querySelector('input'),parts=i.value.split('|').map(v=>v.trim());return {{action:s[0].value,order:n+1,source_message_id:parts[0]||'',explicitness:s[1].value,result:s[2].value,result_evidence:parts[1]||'',equivalence_group:parts[2]||''}}}});return {{annotation_id:'annotation-'+state.annotator+'-'+r.journey_id,journey_id:r.journey_id,root_tweet_id:r.root_tweet_id,annotator_id:state.annotator,evaluation_point_message_id:get('evaluation-point'),evaluation_point_timestamp:(r.messages.find(m=>m.tweet_id===get('evaluation-point'))||{{}}).created_at||'',reconstruction_status:r.reconstruction_status,intent:get('intent')||null,intent_alternatives:[],intent_status:get('intent-status'),intent_confidence:get('confidence'),current_state:get('state')||null,state_status:get('state-status'),state_confidence:get('confidence'),missing_information:missing,attempted_actions:attempted,primary_observed_next_action:get('observed'),observed_next_action:get('observed'),observed_next_actions:[],observed_action_quality:'unknown',ideal_next_action:get('ideal')||null,outcome:get('outcome'),escalation_eligible:get('escalation'),escalation_reason_codes:[...document.querySelectorAll('#reasons input:checked')].map(x=>x.value),escalation_reason:'',evidence_visibility:get('visibility'),ambiguity_flag:get('ambiguity')==='true',ambiguity_reason:get('ambiguity-reason'),insufficient_evidence_reason:get('insufficient-reason'),confidence:get('confidence'),notes:get('notes'),exclude_from_golden:'no',exclusion_reason:'',annotation_timestamp:new Date().toISOString(),adjudication_status:'unadjudicated',adjudication_notes:''}}}}
async function save(e){{e.preventDefault();const record=collect();const response=await fetch('/api/save',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(record)}});const result=await response.json();if(!response.ok){{$('status').className='status error';$('status').textContent=result.errors.join('\n');return}}state.annotations[record.journey_id]=record;dirty=false;$('status').className='status done';$('status').textContent='Saved '+record.annotation_id;renderProgressOnly()}}
function renderProgressOnly(){{const done=Object.keys(state.annotations).length;$('progress').textContent=(state.index+1)+' / '+state.records.length+' · '+done+' saved'}} function clearForm(){{fill({{}});dirty=true;$('status').textContent='Unsaved fields cleared'}} function canNavigate(){{return !dirty||confirm('You have unsaved changes. Continue without saving?')}} function previous(){{if(canNavigate()&&state.index>0){{state.index--;dirty=false;render()}}}} function next(){{if(canNavigate()&&state.index<state.records.length-1){{state.index++;dirty=false;render()}}}} function jump(){{if(!canNavigate()){{return}} const n=prompt('Example number (1-'+state.records.length+')');const i=Number(n)-1;if(Number.isInteger(i)&&i>=0&&i<state.records.length){{state.index=i;dirty=false;render()}}}} function exportFile(){{window.location='/api/export?annotator_id='+encodeURIComponent(state.annotator)}} $('annotator').addEventListener('change',loadState); $('evaluation-point').addEventListener('change',render); $('annotation-form').addEventListener('input',()=>dirty=true); window.addEventListener('beforeunload',e=>{{if(dirty){{e.preventDefault();e.returnValue='';}}}}); loadState();
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    server_version = "SpotifyAnnotationTool/1.0"

    @property
    def app(self):
        return self.server.app  # type: ignore[attr-defined]

    def send_json(self, value: object, status: int = 200, download: bool = False) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        if download:
            self.send_header("Content-Disposition", f'attachment; filename="{self.app.annotator_id}.jsonl"')
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = page().encode("utf-8")
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        params = parse_qs(parsed.query)
        if parsed.path == "/api/state":
            try:
                annotator_id = self.app.safe_annotator(params.get("annotator_id", ["annotator_1"])[0])
            except ValueError as exc:
                self.send_json({"error": str(exc)}, 400); return
            self.app.annotator_id = annotator_id
            self.send_json({"records": self.app.records, "annotations": load_annotations(self.app.annotation_path(annotator_id)), "index": 0, "annotator": annotator_id}); return
        if parsed.path == "/api/export":
            try: annotator_id = self.app.safe_annotator(params.get("annotator_id", ["annotator_1"])[0])
            except ValueError as exc: self.send_json({"error": str(exc)}, 400); return
            path = self.app.annotation_path(annotator_id); body = "".join(json.dumps(v, ensure_ascii=False, sort_keys=True)+"\n" for v in load_annotations(path).values()).encode("utf-8")
            self.send_response(200); self.send_header("Content-Type", "application/x-ndjson; charset=utf-8"); self.send_header("Content-Disposition", f'attachment; filename="{annotator_id}.jsonl"'); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body); return
        self.send_error(404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/save": self.send_error(404); return
        try: record = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0"))))
        except (ValueError, json.JSONDecodeError): self.send_json({"errors": ["Request must contain valid JSON"]}, 400); return
        try: annotator_id = self.app.safe_annotator(record.get("annotator_id", ""))
        except ValueError as exc: self.send_json({"errors": [str(exc)]}, 400); return
        errors = validate_annotation(record, self.app.candidates_by_id, annotator_id)
        if errors: self.send_json({"errors": errors}, 400); return
        path = self.app.annotation_path(annotator_id); annotations = load_annotations(path); annotations[record["journey_id"]] = record; save_annotations(path, annotations); self.send_json({"ok": True})


class App:
    def __init__(self, candidates: Path, annotations: Path):
        self.records = read_jsonl(candidates)
        if len(self.records) != 240: raise ValueError(f"Expected 240 candidates, found {len(self.records)}")
        self.candidates_by_id = {record["journey_id"]: record for record in self.records}
        self.annotations = annotations
        self.annotator_id = "annotator_1"

    def safe_annotator(self, value: str) -> str:
        if not SAFE_ID.fullmatch(value): raise ValueError("Invalid annotator ID")
        return value

    def annotation_path(self, annotator_id: str) -> Path:
        return self.annotations / f"{annotator_id}.jsonl"


def self_test(app: App) -> None:
    assert len(app.records) == 240
    assert all(record["messages"] for record in app.records)
    assert all(message["role"] in {"customer", "support"} for record in app.records for message in record["messages"])
    assert INTENTS == [
        "Playback reliability", "App, device, and platform behavior", "Content or catalog availability",
        "Playlist, library, and music organization", "Premium, subscription, and plan status",
        "Billing, payment, refund, and card issues", "Account access, identity, and security",
        "Family and student eligibility", "Downloads and offline listening", "Ads and free-tier experience",
    ]
    assert len(STATES) == 9 and len(ACTIONS) == 13
    print(f"Self-test passed: {len(app.records)} candidates, valid roles, 10 intents, 9 states, 13 actions")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    app = App(args.candidates, args.annotations)
    if args.self_test: self_test(app); return
    server = ThreadingHTTPServer((args.host, args.port), Handler); server.app = app  # type: ignore[attr-defined]
    print(f"Annotation tool: http://{args.host}:{args.port}/")
    print(f"Candidates: {args.candidates}")
    print(f"Annotations directory: {args.annotations}")
    try: server.serve_forever()
    except KeyboardInterrupt: print("\nAnnotation tool stopped")
    finally: server.server_close()


if __name__ == "__main__": main()