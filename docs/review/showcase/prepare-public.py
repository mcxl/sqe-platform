from pathlib import Path
import hashlib, json, re

base = Path(__file__).resolve().parent
source = base / 'presentation'
target = base / 'public-site'
target.mkdir(exist_ok=True)
(target / 'dist').mkdir(exist_ok=True)
data = json.loads((source / 'content.json').read_text(encoding='utf-8'))
data.pop('source_path')
data.pop('report_uri')
data['use'] = 'Public read-only presentation authorised by the user on 23 September 2026'
data['source_reference'] = 'Zauner IMS Audit Report, issued 24 July 2026; full report not published on this site'
data['register'] = json.loads((base / 'correspondence/register.json').read_text(encoding='utf-8'))

model = (source / 'model.js').read_text(encoding='utf-8')
model = re.sub(r'  function reportUrl\(data, page\) \{.*?\n  \}', '', model, flags=re.S)
model = model.replace("    if (!data.report_uri.startsWith('file:///')) throw new Error('Source must remain a local file');", "    if (data.source_path || data.report_uri) throw new Error('Local paths must not be published');")
model = model.replace('getFinding, reportUrl, validate', 'getFinding, validate')

app = (source / 'app.js').read_text(encoding='utf-8')
old = '  const source = (page, label = `Report p. ${page}`) => `<a href="${escape(model.reportUrl(data,page))}" target="_blank" rel="noopener">${escape(label)}</a>`;'
new = '  const source = page => `<span class="report-reference">Report p. ${Number(page)}</span>`;'
if old not in app:
    raise ValueError('Source-reference transformation did not match')
app = app.replace(old, new)
old = '<a class="source-link" href="${escape(model.reportUrl(data,1))}" target="_blank" rel="noopener">Open source report <span aria-hidden="true">↗</span></a>'
if old not in app:
    raise ValueError('Report-header transformation did not match')
app = app.replace(old, '<span class="small">Source report · 24 July 2026</span>')
app = app.replace('Private, read-only presentation.', 'Public, read-only presentation. Report page references are retained; the full report is not published here.')
app = app.replace('available beside each conclusion', 'summarised beside each conclusion')
app = app.replace('  function render(focusHeading=false) {', (base/'register-ui.js').read_text(encoding='utf-8')+'\n  function render(focusHeading=false) {')
app = app.replace('evidence:evidenceView,client:clientView', 'evidence:evidenceView,client:clientView,register:registerView')
app = app.replace("client:'Client Summary'", "client:'Client Summary',register:'RFIs & Closeouts'")
app = app.replace("    if (button.dataset.view)", "    if (button.dataset.registerItem) { registerSelected=button.dataset.registerItem; registerMode='items'; view='register'; render(); const target=document.getElementById('register-heading'); target.focus(); target.scrollIntoView({block:'start'}); }\n    else if (button.dataset.registerMode) { registerMode=button.dataset.registerMode; render(true); }\n    else if (button.dataset.view)")

template = (source / 'template.html').read_text(encoding='utf-8')
template = template.replace('Prepared for private review', 'Public audit presentation')
template = template.replace('Private presentation', 'Public presentation')
template = template.replace('</nav>', '<button data-view="register"><span class="index">06</span>RFIs &amp; closeouts</button></nav>')
template = re.sub(r'<svg aria-hidden="true".*?</svg>', '', template, flags=re.S)
template = template.replace('This local presentation requires JavaScript. Read the original report in the ZNR folder.', 'This presentation requires JavaScript to display its six views.')
style = (source / 'style.css').read_text(encoding='utf-8')+'\n'+(base/'register-style.css').read_text(encoding='utf-8')
for key, value in {'STYLE': style, 'DATA': json.dumps(data, ensure_ascii=False).replace('<', '\\u003c'), 'MODEL': model, 'APP': app}.items():
    marker = '/*' + key + '*/'
    if template.count(marker) != 1:
        raise ValueError('Missing or duplicate template marker: ' + marker)
    template = template.replace(marker, value)
if re.search(r'file:///|C:\\\\|AlanRichardson|OneDrive|report_uri|source_path|Private presentation|private review', template):
    # The model intentionally checks for forbidden metadata keys.
    check = template.replace('data.source_path || data.report_uri', '')
    if re.search(r'file:///|C:\\\\|AlanRichardson|OneDrive|report_uri|source_path|Private presentation|private review', check):
        raise ValueError('Local metadata remains')
(target / 'dist' / 'index.html').write_text(template, encoding='utf-8')
print(json.dumps({'output': str(target / 'dist' / 'index.html'), 'sha256': hashlib.sha256(template.encode()).hexdigest(), 'bytes': len(template.encode()), 'findings': len(data['findings'])}))
