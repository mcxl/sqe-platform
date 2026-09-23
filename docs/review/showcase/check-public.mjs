import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import path from 'node:path';
const base = path.dirname(new URL(import.meta.url).pathname.replace(/^\/(\w:)/, '$1'));
const root = path.join(base, 'public-site');
const html = fs.readFileSync(path.join(root, 'dist/index.html'), 'utf8');
const original = JSON.parse(fs.readFileSync(path.join(base, 'presentation/content.json'), 'utf8'));
const scripts = [...html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length, 3);
const data = JSON.parse(scripts[0][2]);
assert.equal(data.findings.length, Number(process.env.EXPECTED_COUNT || 6), 'Unique findings count');
assert.equal(data.register.items.length, Number(process.env.EXPECTED_REGISTER_COUNT || 18), 'Register item count');
let count = 0;
function check(name, run) { run(); count++; console.log('PASS ' + name); }
const context = vm.createContext({});
vm.runInContext(scripts[1][2], context);
const model = context.ZaunerModel;
check('public model validates', () => assert.equal(model.validate(data), true));
check('report findings and detail text preserved', () => {
  assert.deepEqual(data.findings, original.findings);
  assert.deepEqual(data.details, original.details);
  assert.deepEqual(data.summary_reported_counts, original.summary_reported_counts);
});
check('standards filters retain counts 2 / 1 / 5', () => assert.deepEqual(Array.from(model.standards, s => model.findingsFor(data,s).length), [2,1,5]));
check('six unique findings and correct selection', () => {
  assert.equal(new Set(data.findings.map(f=>f.id)).size,6);
  assert.equal(model.getFinding(data,'NCR-03').id,'NCR-03');
});
check('no local source metadata or file links', () => {
  assert.equal(data.source_path,undefined); assert.equal(data.report_uri,undefined);
  assert.doesNotMatch(html,/file:\/\/\/|AlanRichardson|OneDrive|C:\\\\/i);
});
check('no external assets, forms, network requests or storage', () => {
  assert.doesNotMatch(html,/(?:src|href)=["']https?:|<form\b|fetch\s*\(|XMLHttpRequest|localStorage|sessionStorage|WebSocket|sendBeacon/);
  assert.match(html,/connect-src 'none'/);
});
check('public label and source-report limitation present', () => {
  assert.match(html,/Public presentation/);
  assert.match(html,/full report is not published here/);
  assert.doesNotMatch(html,/Private presentation|Prepared for private review/);
});
const main={innerHTML:'',querySelector(){return {focus(){}}},querySelectorAll(){return model.standards.map(s=>({dataset:{filter:s},focus(){}})).concat([{dataset:{filter:'all'},focus(){}}]);}};
let handler;
const nodes={'main':main,'zauner-data':{textContent:JSON.stringify(data)},announcer:{textContent:''}};
context.document={getElementById(id){return nodes[id] || {focus(){},scrollIntoView(){}};},querySelectorAll(){return [];},addEventListener(type,fn){if(type==='click')handler=fn;}};
context.window={scrollTo(){}};
vm.runInContext(scripts[2][2],context);
function click(dataset){handler({target:{closest(){return {dataset};}}});}
check('six views render through application handlers',()=>{
  for(const [view,text] of Object.entries({overview:'Integrated assurance review',standards:'Standards view',findings:'Findings register',evidence:'Evidence & decisions',client:'Client summary',register:'RFIs & closeouts'})){
    click({view});assert.ok(main.innerHTML.includes(text),view);
  }
});
check('filter and finding handlers update rendered markup',()=>{
  click({standard:'ISO 14001:2015'});assert.match(main.innerHTML,/1 unique finding shown/);assert.match(main.innerHTML,/OFI-01/);
  click({filter:'all'});click({finding:'NCR-03'});assert.match(main.innerHTML,/Tower-crane pre-start evidence/);
});
check('all evidence story handlers render',()=>{
  for(const story of ['coverage','crane','declarations']){click({story});assert.ok(main.innerHTML.includes('story-'+story));}
});
check('rendered views contain no broken report hyperlinks',()=>{
  for(const view of ['overview','standards','findings','evidence','client','register']){click({view});assert.doesNotMatch(main.innerHTML,/<a\b/);}
});
check('register has unique items/events and valid item links',()=>{
  const ids=new Set(data.register.items.map(i=>i.id));assert.equal(ids.size,18);
  assert.equal(new Set(data.register.events.map(e=>e.id)).size,17);
  for(const e of data.register.events){assert.ok(e.source);for(const id of Object.keys(e.notes))assert.ok(ids.has(id));}
});
check('correspondence order is chronological',()=>{
  const keys=data.register.events.map(e=>e.date);
  assert.deepEqual(keys,[...keys].sort());
  const ids=data.register.events.map(e=>e.id);assert.ok(ids.indexOf('A01')<ids.indexOf('D01'));
  assert.equal(data.register.events.find(e=>e.id==='A01').time,null);
});
check('receipt bounds retain their evidence and do not claim exact timestamps',()=>{
  for(const e of data.register.events.filter(e=>e.received)){assert.match(e.received,/^By /);assert.ok(e.receipt_basis);}
  assert.match(data.register.coverage_note,/not delivery timestamps/);
  const expected={H01:'By 3 Nov 2025',H03:'By 15 Jun 2026',H04:'By 17 Jun 2026',D01:'By 20 Jul 2026',D02:'By 22 Jul 2026',S02:'By 22 Jul 2026',D04:'By 24 Jul 2026',S04:'By 24 Jul 2026'};
  for(const [id,bound] of Object.entries(expected))assert.equal(data.register.events.find(e=>e.id===id).received,bound);
});
check('structural-steel trail preserves repeated requests and response sequence',()=>{
  const trail=data.register.events.filter(e=>Object.hasOwn(e.notes,'RFI-07'));
  for(const id of ['H03','H04','H05','A01','S01','S02','S03','S04','S05','R01'])assert.ok(trail.some(e=>e.id===id));
  assert.match(data.register.items.find(i=>i.id==='RFI-07').remaining,/no separate retained record/);
});
check('partial closure and separate NCR remain unresolved',()=>{
  assert.equal(data.register.items.find(i=>i.id==='RFI-09').status,'Partly resolved');
  assert.equal(data.register.items.find(i=>i.id==='NCR-03').status,'Open in report');
  assert.equal(data.register.items.find(i=>i.id==='NCR-03').response,null);
});
check('register selection exposes dated conversations and concise index',()=>{
  click({view:'register'});assert.match(main.innerHTML,/>Requested</);assert.match(main.innerHTML,/>First response</);
  assert.match(main.innerHTML,/UTC message dates are converted to Australia\/Sydney/);
  assert.match(main.innerHTML,/exact same-day timing remains unknown/);
  const rfi09=data.register.items.find(i=>i.id==='RFI-09');assert.equal(rfi09.requested,'2026-07-16');assert.equal(rfi09.response,'2026-07-16');
  assert.match(data.register.events.find(e=>e.id==='A01').notes['RFI-09'],/first retained written follow-up request is dated 20 July/);
  click({registerItem:'RFI-09'});assert.match(main.innerHTML,/RFI-09 correspondence history/);assert.match(main.innerHTML,/Response \/ counter-request/);
  click({registerMode:'all'});assert.match(main.innerHTML,/All retained correspondence/);assert.match(main.innerHTML,/11:17/);
  click({registerItem:'NCR-03'});assert.match(main.innerHTML,/NCR-03 correspondence history/);assert.match(main.innerHTML,/No dated corrective-action correspondence/);
});
check('every item shows its question, outcome, sources and complete event history',()=>{
  for(const item of data.register.items){
    assert.ok(item.question);click({registerItem:item.id});
    const section=main.innerHTML.split('<section class="surface register-detail"')[1].split('</section>')[0];
    const events=data.register.events.filter(e=>Object.hasOwn(e.notes,item.id));
    assert.equal((section.match(/class="correspondence-entry"/g)||[]).length,events.length);
    assert.equal((section.match(/<summary>Evidence details<\/summary>/g)||[]).length,events.length);
    assert.equal((section.match(/class="entry-source"/g)||[]).length,events.length+1);
    assert.match(section,/Outcome recorded in the report/);assert.doesNotMatch(section,/<table/);
    for(const e of events){assert.ok(e.source_label);assert.ok(section.includes(e.notes[item.id].replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#39;')));}
  }
});
check('RFI-06 excludes unrelated shared-email content and distinguishes closure from report outcome',()=>{
  click({registerItem:'RFI-06'});
  const section=main.innerHTML.split('<section class="surface register-detail"')[1].split('</section>')[0];
  const visible=section.replace(/<details[\s\S]*?<\/details>/g,'');
  assert.doesNotMatch(visible,/RFI-07|DBP|remaining non-DBP/);
  assert.match(visible,/Closure indication/);assert.match(visible,/OFI-01/);
  assert.match(visible,/Summary relates to RFI-06 only/);
  assert.match(visible,/Source:.*22 July 2026/);
  assert.match(visible,/Received by 24 Jul 2026/);
  assert.match(visible,/exact receipt date\/time unknown/);
  const s04=data.register.events.find(e=>e.id==='S04');assert.equal(s04.item_kinds['RFI-06'],'Closure indication');assert.equal(s04.item_kinds['RFI-07'],'Further request');
});
check('whole trail retains all events and item navigation',()=>{
  click({registerMode:'all'});
  assert.equal((main.innerHTML.match(/class="correspondence-entry"/g)||[]).length,17);
  assert.equal((main.innerHTML.match(/<summary>Evidence details<\/summary>/g)||[]).length,17);
  assert.match(main.innerHTML,/data-register-item="RFI-06"/);
  assert.doesNotMatch(main.innerHTML,/<table/);
});
check('public correspondence contains no personal contact details or mailbox URLs',()=>{
  assert.doesNotMatch(JSON.stringify(data.register),/@|outlook\.office|041\d|Alan Richardson|Ryan Barnett|C:\\\\/);
});
console.log(`${count} checks passed. DOM stubs exercise render logic, not browser layout or accessibility.`);
