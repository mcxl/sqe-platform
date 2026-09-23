from pathlib import Path
import json
base=Path(__file__).resolve().parent
items=[]; events=[]
def item(id,subject,status,requested=None,response=None,receipt=None,remaining='None recorded for this request',pages=None,question=None):
    items.append(dict(id=id,subject=subject,status=status,requested=requested,response=response,receipt=receipt,remaining=remaining,pages=pages or [],question=question))
def event(id,date,kind,sender,recipient,notes,source,receipt=None,receipt_basis=None,time=None,source_label=None,item_kinds=None):
    events.append(dict(id=id,date=date,time=time,kind=kind,sender=sender,recipient=recipient,notes=notes,source=source,source_label=source_label,received=receipt,receipt_basis=receipt_basis,item_kinds=item_kinds or {}))
subjects=['Ground-gas plan and roles','Loading-bay release basis','Crane maintenance date','Concrete docket traceability','RFI 39 design query','Internal-audit evidence','Structural steel SSI46 / SSI49','Subcontractor meeting minutes','Design declarations and Portal timing','CC4 facade and cladding','Final DBP package']
for n,title in enumerate(subjects,1):
    id=f'RFI-{n:02}'
    status='Closed as clarification' if n in [1,2,6] else 'Closed'
    remaining='None recorded for this request'
    if n==1:remaining='Ground-gas completion verification remains FVI-01.'
    if n==3:remaining='Separate pre-start-record finding NCR-03 remains open.'
    if n==5:remaining='Drawing issue and declaration questions are separate from the closed design query.'
    if n==6:remaining='OFI-01 remains open; supplying the records did not resolve programme traceability.'
    if n==7:status='Clarification closed / future checks';remaining='Final structural certificate and SSI49 remain future verification. Follow-up inspection outcome has no separate retained record.'
    if n==9:status='Partly resolved';remaining='Hydraulic declaration date and Planning Portal timing remain unresolved.'
    if n in [10,11]:status='Future verification';remaining='Future control in the report; no separate dated request/response sequence established.'
    item(id,title,status,'2026-07-16' if n<=8 else ('2026-07-20' if n==9 else None),'2026-07-17' if n<=8 else ('2026-07-22' if n==9 else None),'By 20 Jul 2026' if n<=8 else ('By 22 Jul 2026' if n==9 else None),remaining,{1:[14],2:[13],3:[9,14],4:[13],5:[12],6:[14,15],7:[13,19],8:[7],9:[8,19,20],10:[3],11:[3]}[n])
original=json.loads((base/'presentation/content.json').read_text())
for f in original['findings']:
    item(f['id'],f['title'],'Open in report',remaining='No dated corrective-action correspondence or closure decision was established in the reviewed chains.',pages=f['source_pages'])
item('FVI-01','Ground-gas completion package','Future verification',remaining='Completion-stage inspection, testing and specialist validation package; not yet due at audit date.',pages=[3,14,19])
questions={
    'RFI-01':'Clarify the final ground-gas plan, roles and completion evidence.',
    'RFI-02':'Clarify the loading-bay release basis.',
    'RFI-03':'Confirm the crane maintenance due date.',
    'RFI-04':'Trace the concrete dockets to the strength report.',
    'RFI-05':'Confirm the status of Procore RFI 39.',
    'RFI-06':'Clarify the internal-audit evidence and its scope.',
    'RFI-07':'Clarify SSI46 close-out and structural verification.',
    'RFI-08':'Provide the current subcontractor meeting minutes.',
    'RFI-09':'Trace sampled design changes to declarations and Portal records.',
    'RFI-10':'Future check: facade and cladding pre-start control.',
    'RFI-11':'Future check: final DBP document package.',
    'NCR-01':'Report-recorded live-edge control observation.',
    'NCR-02':'Report-recorded respiratory protection observation.',
    'NCR-03':'Report-recorded tower-crane pre-start evidence gap.',
    'NCR-04':'Report-recorded smoking contrary to the site rule.',
    'OFI-01':'Report-recorded opportunity to improve audit-programme traceability.',
    'OFI-02':'Report-recorded opportunity to improve waterproofing traceability.',
    'FVI-01':'Future check: ground-gas completion verification package.'
}
for i in items:
    i['question']=questions[i['id']]
S='Structural-steel email chain dated 24 Jul 2026'
D='Design-declaration email chain dated 24 Jul 2026'
event('H01','2025-11-03','Background request','Zauner project team','Project certifier',{'RFI-09':'Asked when the CC2 re-declaration package should be uploaded to the Planning Portal.'},D+' p. 8',time='11:17')
event('H02','2025-11-03','Background response','Project certifier','Zauner project team',{'RFI-09':'Provided its understanding of project-specific Portal advice and indicated no objection to the described approach. This is correspondence, not a verified legal conclusion.'},D+' p. 7',time='11:26')
event('H03','2026-06-12','Supporting evidence','Steel subcontractor','Zauner project team',{'RFI-07':'Sent the Building B Level 3 ITP and photographs of completed work. The email says the inspection was completed the previous day.'},'Steel subcontractor email dated 12 Jun 2026; quoted in June correspondence')
event('H04','2026-06-15','Supporting request','Zauner site team','Structural engineer',{'RFI-07':'Sent structural-steel inspection photographs and arranged further site inspections.'},'Structural-steel email dated 15 Jun 2026',time='16:22')
event('H05','2026-06-17','Supporting response','Structural engineer','Zauner site team',{'RFI-07':'Accepted photographed items but identified grout and unphotographed instances. Proposed checking remaining items at the next site visit; this email does not record that visit outcome.'},'Structural-engineer email dated 17 Jun 2026',time='10:31')
event('A01','2026-07-16','Audit request','AuditCo auditor','Zauner project team',{f'RFI-{n:02}':f'Record or clarification requested during the site audit: {subjects[n-1].lower()}.' for n in range(1,9)},'Audit report pp. 7, 9, 12–16. No original email timestamp for these on-site requests.')
event('D01','2026-07-16','Evidence forwarded','Zauner project team','AuditCo auditor',{'RFI-09':'Forwarded the previous certifier/Portal correspondence and Crown Certificate material in response to audit questions. Internal forwards at 11:40 and 11:44 precede the auditor-facing forward at 13:24.'},D+' pp. 4–8',time='13:24')
notes17={
'RFI-01':'Linked the ground-gas plan. The subsequent review identified this initial version as a draft.',
'RFI-02':'Linked the loading-bay drawing / certification material requested at audit.',
'RFI-03':'Supplied the maintenance schedule and corrected the next-due date to on or before 14 August 2026.',
'RFI-04':'Linked the concrete dockets.',
'RFI-05':'Supplied the Procore RFI 39 record and advised the design query had closed on 24 June 2026.',
'RFI-06':'Linked the site safety inspection record.',
'RFI-07':'Linked the Building B structural-steel sign-off documents.',
'RFI-08':'Linked subcontractor meeting minutes.'}
event('S01','2026-07-17','Response','Zauner project manager','AuditCo auditor',notes17,S+' pp. 7–8','By 20 Jul 2026','The auditor’s 20 July reply acknowledges and reviews this response; exact receipt time is not recorded.','14:52')
event('D02','2026-07-20','Further request','AuditCo auditor','Zauner project manager',{'RFI-09':'Requested drawing identities, relevant Crown Certificates, declaration/variation records, Portal references and lodgement dates for three sampled changes. Requested the written basis for deferred lodgement.'},D+' pp. 3–4',time='07:48')
notes20={
'RFI-01':'Requested the final approved plan or written construction authority for the draft; asked about verification roles and completion records.',
'RFI-02':'Asked whether Zauner relied on the Scaff-Tag / scaffold handover without a separate engineer’s certificate.',
'RFI-03':'Acknowledged the corrected maintenance dates and apologised for the initial reading error. Did not explicitly state closure in this reply.',
'RFI-04':'Explicitly closed the request after matching the dockets to the concrete strength report.',
'RFI-05':'Closed the design query; expressly left revised drawing issue and DBP review separate.',
'RFI-06':'Asked whether the site inspection completed a scheduled internal audit and requested scope, criteria, findings and conclusion records.',
'RFI-07':'Requested the SSI46 photo close-out, when it was sent, engineer response and the basis for authorising work to proceed.',
'RFI-08':'Explicitly acknowledged and closed the request.'}
event('S02','2026-07-20','Review / further request','AuditCo auditor','Zauner project manager',notes20,S+' pp. 3–6',time='08:03')
event('D03','2026-07-22','Response / counter-request','Zauner project manager','AuditCo auditor',{'RFI-09':'Asked the auditor to identify the architectural and electrical drawing numbers so the traceability request could be answered.'},D+' p. 2','By 22 Jul 2026','The auditor’s 13:35 reply establishes receipt by this date.','10:32')
notes22={
'RFI-01':'Apologised for the wrong initial plan and replaced it with the final version. Clarified BGL / EI roles; completion records had not been requested or received and were expected at scope completion.',
'RFI-02':'Confirmed reliance on the completed Scaff-Tag or handover certificate without a separate engineer’s certificate.',
'RFI-03':'Asked whether the auditor’s acknowledgement meant closure; Zauner’s assumption alone is not a closure decision.',
'RFI-06':'Confirmed the inspection was not intended to fulfil the internal-audit schedule; supplied additional internal-audit material.',
'RFI-07':'Supplied earlier photographic and engineer correspondence, including the 17 June response proposing a further site check.'}
event('S03','2026-07-22','Response','Zauner project manager','AuditCo auditor',notes22,S+' pp. 2–6','By 22 Jul 2026','The auditor’s 14:26 reply establishes receipt by this date.','12:06')
event('D04','2026-07-22','Further request','AuditCo auditor','Zauner project manager',{'RFI-09':'Asked the project team to confirm missing drawing numbers from Procore and complete the Crown Certificate, declaration and Portal-lodgement information.'},D+' pp. 1–2',time='13:35')
event('S04','2026-07-22','Review / further request','AuditCo auditor','Zauner project manager',{
**{f'RFI-{n:02}':'The auditor indicated that this information request could close.' for n in [1,2,3,4,5,6,8]},
'RFI-07':'Asked whether the planned Northrop follow-up inspection took place, how remaining SSI46 items closed and for the inspection or close-out record. Prior evidence described an intended visit, not its result.'},S+' pp. 1–2',time='14:26')
event('D05','2026-07-24','Response / closure requested','Zauner project manager','AuditCo auditor',{'RFI-09':'Supplied marked architectural, hydraulic and electrical declaration packages plus earlier certifier advice. Confirmed the declarations had not been lodged on the Portal and asked whether the query could close.'},D+' p. 1','By 24 Jul 2026','Retained auditor Inbox print and the issued report establish possession by this date; exact delivery time is not separately recorded.','10:32')
event('S05','2026-07-24','Response / closure requested','Zauner project manager','AuditCo auditor',{'RFI-07':'Advised SSI46 items were verified on site and in the subcontractor ITP. Stated the engineer gave no separate follow-up correspondence, attached the ITP email and asked whether this closed the item.'},S+' p. 1','By 24 Jul 2026','Retained auditor Inbox print and the issued report establish possession by this date; exact delivery time is not separately recorded.','10:54')
final={i['id']:f"{i['status']}. {i['remaining']}" for i in items}
event('R01','2026-07-24','Report disposition','AuditCo report','Report record',final,'Audit report issued 24 Jul 2026, pp. 3, 7–20. Report date is not a verified individual closure timestamp.')
events.sort(key=lambda e:(e['date'],e['time'] or '23:59',e['id']))
for i in items:
    if i['id']=='RFI-09':
        i.update(requested='2026-07-16',response='2026-07-16',receipt='By 20 Jul 2026')
by_id={e['id']:e for e in events}
by_id['A01']['notes']['RFI-09']='Design-change and Portal questions were raised during the audit, as confirmed by the 16 July forwarding chain. The first retained written follow-up request is dated 20 July.'
by_id['A01']['source']+=' Design-declaration email chain dated 24 Jul 2026 pp. 4–6 records the 16 July audit queries.'
bounds={
    'H01':('By 3 Nov 2025','The certifier’s same-day reply H02 establishes receipt.'),
    'H03':('By 15 Jun 2026','The site team’s 15 June forward includes the subcontractor email.'),
    'H04':('By 17 Jun 2026','The engineer’s reply H05 establishes receipt.'),
    'D01':('By 20 Jul 2026','The auditor’s follow-up D02 refers to the forwarded email thread.'),
    'D02':('By 22 Jul 2026','The project manager’s counter-request D03 responds to this request.'),
    'S02':('By 22 Jul 2026','The project manager’s reply S03 answers the auditor’s questions.'),
    'D04':('By 24 Jul 2026','The project manager’s response D05 supplies the requested drawing/declaration trace.'),
    'S04':('By 24 Jul 2026','The project manager’s response S05 answers the SSI46 follow-up.')
}
for id,(date,basis) in bounds.items():
    by_id[id].update(received=date,receipt_basis=basis+' Exact delivery time is not recorded.')
source_labels={
    'H01':'Zauner project manager email, 3 Nov 2025 11:17',
    'H02':'Project certifier email, 3 Nov 2025 11:26',
    'H03':'Steel subcontractor email, 12 Jun 2026',
    'H04':'Zauner site team email, 15 Jun 2026 16:22',
    'H05':'Structural engineer email, 17 Jun 2026 10:31',
    'A01':'Zauner IMS Audit Report, issued 24 Jul 2026, and Zauner email, 16 Jul 2026 (record the audit questions)',
    'D01':'Zauner contracts administrator email, 16 Jul 2026 13:24',
    'S01':'Zauner project manager email, 17 Jul 2026 14:52',
    'D02':'AuditCo auditor email, 20 Jul 2026 07:48',
    'S02':'AuditCo auditor email, 20 Jul 2026 08:03',
    'D03':'Zauner project manager email, 22 Jul 2026 10:32',
    'S03':'Zauner project manager email, 22 Jul 2026 12:06',
    'D04':'AuditCo auditor email, 22 Jul 2026 13:35',
    'S04':'AuditCo auditor email, 22 Jul 2026 14:26',
    'D05':'Zauner project manager email, 24 Jul 2026 10:32',
    'S05':'Zauner project manager email, 24 Jul 2026 10:54',
    'R01':'Audit report issued, 24 Jul 2026'
}
for e in events:
    e['source_label']=source_labels[e['id']]
by_id['S04']['item_kinds']={
    **{f'RFI-{n:02}':'Closure indication' for n in [1,2,3,4,5,6,8]},
    'RFI-07':'Further request'
}
by_id['S02']['item_kinds']={
    'RFI-03':'Acknowledgement',
    **{f'RFI-{n:02}':'Closure decision' for n in [4,5,8]},
    **{f'RFI-{n:02}':'Further request' for n in [1,2,6,7]}
}
# Preserve the evidenced request-before-response sequence without inventing a time.
events.sort(key=lambda e:(e['date'], '00:00' if e['id']=='A01' else e['time'] or '23:59',e['id']))
result={'as_of':'2026-07-24','items':items,'events':events,'coverage_note':'Reconstructed from the retained audit and email chains. The record includes all identified substantive exchanges in those chains, not a certified complete mailbox export. Some original PDFs are image-only; quoted copies supplied the readable sequence. Receipt dates are latest evidenced dates, not delivery timestamps. No later closeout correspondence has been established.'}
(base/'correspondence/register.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'{len(items)} items; {len(events)} distinct events')
