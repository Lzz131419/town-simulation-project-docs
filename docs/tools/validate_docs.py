#!/usr/bin/env python3
"""Check documentation structure and traceability; no business implementation test."""
from pathlib import Path
from collections import Counter
import json, re, sys
from urllib.parse import unquote
ROOT = Path(__file__).resolve().parents[2]
errors = []
def check(ok, message):
    if not ok: errors.append(message)
required = ['README.md','context.md','agent-rules.md','spec/mvp1-scope.md','docs/architecture.md','docs/dependency.md','docs/spike/plan.md','plans/mvp1-plan.md','plans/branch-plan.md','docs/review/pr-checklist.md','docs/test/cold-start-01.md', 'docs/v2/product-design.md', 'docs/v2/spec.md', 'docs/v2/architecture.md', 'docs/v2/implementation-plan.md', 'docs/v2/verification.md', 'adr/ADR-003-shared-town-v2.md']
for rel in required: check((ROOT/rel).is_file(), f'missing: {rel}')
mds = sorted(p for p in ROOT.rglob('*.md') if not any(part in {'.git','.venv','.local','node_modules','test-results','playwright-report','dist','.pytest_cache'} for part in p.relative_to(ROOT).parts))
link_count = 0
for p in mds:
    text = p.read_text()
    check(text.count('```') % 2 == 0, f'unclosed code fence: {p.relative_to(ROOT)}')
    for dest in re.findall(r'\[[^\]]+\]\(([^)]+)\)', text):
        dest = unquote(dest.split('#')[0].strip('<>'))
        if not dest or re.match(r'[a-z]+://|mailto:', dest): continue
        target = ROOT/dest.lstrip('/') if dest.startswith('/') else p.parent/dest
        resolved = target.resolve()
        relative_parts = resolved.relative_to(ROOT).parts if resolved.is_relative_to(ROOT) else Path(dest).parts
        check(not any(part in {'.local', '.venv', 'node_modules'} for part in relative_parts), f'local-only link cannot be published: {p.relative_to(ROOT)} -> {dest}')
        check(target.exists(), f'broken link: {p.relative_to(ROOT)} -> {dest}')
        link_count += 1
    # Governance templates and historical records are intentionally exempt.
    if 'cold-start-2026-11-10-history' not in p.name:
        check('/Users/' not in text, f'local machine path exposed: {p.relative_to(ROOT)}')
modules = sorted((ROOT/'spec').glob('module-*.md'))
check(len(modules) == 5, 'must have five module specs')
all_acs = set()
for p in modules:
    s=p.read_text(); acs=re.findall(r'^### (M\d-AC-\d{2})',s,re.M)
    check(len(acs)>=3, f'not enough AC: {p.name}')
    check(not all_acs.intersection(acs), f'duplicate AC ID: {p.name}'); all_acs.update(acs)
    for section in ['摘要','用户故事','验收标准（Given/When/Then）','功能需求','非功能需求','边界与异常','Non-Goals','变更记录']:
        check('## '+section in s, f'missing section {section}: {p.name}')
    gwt=re.findall(r'```gherkin\n(.*?)```',s,re.S)
    check(len(gwt)==len(acs), f'AC without GWT block: {p.name}')
    for block in gwt:
        check(all(re.search(r'^'+word+r'\s+\S',block,re.M) for word in ['Given','When','Then']), f'incomplete GWT: {p.name}')
    stories=set(re.findall(r'\*\*(M\d-US-\d+)',s))
    story_refs=set(re.findall(r'^### .*?（(M\d-US-\d+)）',s,re.M))
    check(stories==story_refs, f'uncovered user story: {p.name}')
    boundary=s.split('## 边界与异常')[1].split('## Non-Goals')[0]
    for ac in re.findall(r'M\d-AC-\d{2}',boundary): check(ac in acs,f'undefined boundary AC: {ac}')
    for row in boundary.splitlines():
        if row.startswith('|') and not row.startswith('| 场景') and not re.match(r'^\|[ -]+\|',row):
            check(bool(re.search(r'M\d-AC-\d{2}',row)),f'boundary without AC: {p.name}')
tasks=json.loads((ROOT/'plans/tasks.json').read_text())
check(8<=len(tasks)<=12,'task count out of course range')
byid={t['id']:t for t in tasks}; check(len(byid)==len(tasks),'duplicate task')
people={'张果','王崛','李展博','孙祥','钱俊昊','姚富恩'}
covered=set(); branches=[]
for t in tasks:
    check(t['owner'] in people and t['reviewer'] in people,'unknown person '+t['id'])
    check(t['owner']!=t['reviewer'],'self review '+t['id'])
    check(1<=t['estimateDays']<=3,'task too large '+t['id'])
    check(1<=len(t['refs'])<=2,'invalid binding count '+t['id'])
    check(bool(t['files']) and bool(t['acceptance']),'missing task scope '+t['id'])
    for ref in t['refs']:
        check(ref in all_acs or ref in {'ADR-001','ADR-002','DEMO-01'},'unknown ref '+ref)
        if ref in all_acs: covered.add(ref)
    for dep in t['dependsOn']: check(dep in byid,'unknown dependency '+dep)
    check(re.fullmatch(r'(feature|test|spike|docs|fix)/issue-\{number\}-[a-z0-9-]+',t['branchTemplate']) is not None,'bad branch '+t['id'])
    branches.append(t['branchTemplate'])
    issue=ROOT/'plans/issues'/f"{t['id']}.md"
    check(issue.exists(),'missing issue '+t['id'])
    if issue.exists():
        body=issue.read_text()
        for section in ['背景','对应spec/AC','验收标准','负责人','分支名','标签']:
            check('## '+section in body,'missing issue section '+t['id']+' '+section)
        check(all(ref in body for ref in t['refs']), 'Issue refs mismatch '+t['id'])
check(covered==all_acs,'AC not assigned to tasks: '+str(all_acs-covered))
check(len(set(branches))==len(branches),'duplicate branch')
visiting=set(); finish={}; paths={}
def visit(tid):
    if tid in finish:return finish[tid]
    if tid in visiting:raise ValueError('task cycle at '+tid)
    visiting.add(tid); t=byid[tid]; deps=t['dependsOn']
    for d in deps:visit(d)
    best=max(deps,key=lambda d:finish[d]) if deps else None
    finish[tid]=(finish[best] if best else 0)+t['estimateDays']
    paths[tid]=(paths[best] if best else [])+[tid];visiting.remove(tid);return finish[tid]
try:
    for tid in byid: visit(tid)
except (ValueError,KeyError) as e: errors.append(str(e))
critical=max(finish,key=finish.get) if finish else None
plan=(ROOT/'plans/mvp1-plan.md').read_text()
plan_rows=[line for line in plan.splitlines() if re.match(r'^\| T\d{2} \|',line)]
check(len(plan_rows)==len(tasks),'Plan row count mismatch')
for row in plan_rows:
    check(len(row.split('|'))==10,'Plan must have eight columns')
    tid=row.split('|')[1].strip();t=byid.get(tid,{})
    check(t.get('owner','') in row and all(ref in row for ref in t.get('refs',[])), 'Plan task mismatch '+tid)
check(sum(t['estimateDays'] for t in tasks)==27,'estimate total changed; update plan')
check(critical and finish[critical]==15,'critical duration changed; update plan')
for t in tasks:
    if t.get('issueUrl'):
        check(t['issueUrl'].endswith('/'+str(t.get('issueNumber'))), 'Issue number mismatch '+t['id'])
        check(t.get('branch')==t['branchTemplate'].replace('{number}',str(t['issueNumber'])), 'resolved branch mismatch '+t['id'])
fixture=json.loads((ROOT/'docs/fixtures/scenario-v1.json').read_text())
check(sum(fixture['jobs'].values())==fixture['generatedResidents']==30,'fixture population')
check(fixture['resources']['treasury']+30*fixture['agentDefaults']['cash']==1600,'fixture initial money')
check(fixture['digitalDefaults']['cash']==0,'digital profile mints money')
for m in modules:
    for ac in re.findall(r'^### (M\d-AC-\d{2})',m.read_text(),re.M):
        check(ac in (ROOT/'docs/traceability.md').read_text(),'traceability missing '+ac)
if errors:
    for error in errors:print('FAIL:',error)
    sys.exit(1)
v2spec=(ROOT/'docs/v2/spec.md').read_text()
v2acs=re.findall(r'^### (V2-AC-\d{2})',v2spec,re.M)
check(len(v2acs)==24 and len(set(v2acs))==24, 'v2 requires twenty-four unique acceptance criteria')
v2blocks=re.findall(r'```gherkin\n(.*?)```',v2spec,re.S)
check(len(v2blocks)==len(v2acs), 'v2 AC without GWT block')
for block in v2blocks:
    check(all(re.search(r'^'+word+r'\s+\S',block,re.M) for word in ['Given','When','Then']), 'v2 incomplete GWT')
verification=(ROOT/'docs/v2/verification.md').read_text()
for ac in v2acs:
    check(ac in verification, 'v2 missing verification mapping: '+ac)
if errors:
    for error in errors:print('FAIL:',error)
    sys.exit(1)
print(f'PASS: {len(mds)} Markdown files; {link_count} local links resolve')
print(f'PASS: v2 {len(v2acs)} GWT criteria with verification mappings; current architecture and ADR present')
print(f'PASS: v1 {len(modules)} modules; {len(all_acs)} unique GWT ACs; every story and boundary linked')
print(f'PASS: {len(tasks)} tasks; all ACs covered; owners/reviewers/Issue bodies/branch templates valid')
print('PASS: DAG acyclic; '+ ' -> '.join(paths[critical])+f" = {finish[critical]} working days; 27 person-days")
print('PASS: fixtures match population and money; published task numbers and resolved branches consistent')
print('LIMIT: checks structure and references only, not semantic correctness, implementation, human review or GitHub status')
