// Builds SYSTEM.md and atlas.html from data.mjs in this folder.
// Derived files are not hand-editable. Edit data.mjs, then run this script.
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { META, DECISIONS, GROUPS, NODES, FLOWS, CH, HOW_HTML } from './data.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const outDir = here;

// ---------- data validation ----------
const fail = (path, message) => {
  throw new Error(`Validation error at ${path}: ${message}`);
};
const isObject = (value) => value !== null && typeof value === 'object' && !Array.isArray(value);
const stringAt = (value, path) => {
  if (typeof value !== 'string' || !value.trim()) fail(path, 'must be a non-empty string');
};
const arrayAt = (value, path) => {
  if (!Array.isArray(value)) fail(path, 'must be an array');
};
const objectAt = (value, path) => {
  if (!isObject(value)) fail(path, 'must be an object');
};
const uniqueIds = (items, path, key = 'id') => {
  const seen = new Set();
  items.forEach((item, index) => {
    const value = item[key];
    stringAt(value, `${path}[${index}].${key}`);
    if (seen.has(value)) fail(`${path}[${index}].${key}`, `duplicate ${key} "${value}"`);
    seen.add(value);
  });
  return seen;
};
const isJsonValue = (value, seen = new Set()) => {
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return true;
  if (typeof value === 'number') return Number.isFinite(value);
  if (Array.isArray(value)) {
    if (seen.has(value)) return false;
    seen.add(value);
    const valid = value.every((item) => isJsonValue(item, seen));
    seen.delete(value);
    return valid;
  }
  if (isObject(value)) {
    if (seen.has(value)) return false;
    seen.add(value);
    const valid = Object.values(value).every((item) => isJsonValue(item, seen));
    seen.delete(value);
    return valid;
  }
  return false;
};
const serialisableAt = (value, path) => {
  if (!isJsonValue(value)) fail(path, 'must be JSON-serialisable');
  try {
    const json = JSON.stringify(value);
    if (json === undefined) fail(path, 'must be JSON-serialisable');
    JSON.parse(json);
  } catch (error) {
    if (error.message.startsWith('Validation error at ')) throw error;
    fail(path, 'must be JSON-serialisable');
  }
};
const validateHop = (hop, path, nodeIds) => {
  arrayAt(hop, path);
  if (hop.length < 4 || hop.length > 5) fail(path, 'must have four or five values');
  stringAt(hop[0], `${path}[0]`);
  stringAt(hop[1], `${path}[1]`);
  if (!nodeIds.has(hop[0])) fail(`${path}[0]`, `unknown node "${hop[0]}"`);
  if (!nodeIds.has(hop[1])) fail(`${path}[1]`, `unknown node "${hop[1]}"`);
  stringAt(hop[2], `${path}[2]`);
  serialisableAt(hop[3], `${path}[3]`);
  if (hop.length === 5 && !['xy', 'yx'].includes(hop[4])) fail(`${path}[4]`, 'must be "xy" or "yx"');
};
const validateQuestion = (question, path) => {
  if (typeof question === 'string') {
    stringAt(question, path);
    return;
  }
  objectAt(question, path);
  stringAt(question.q, `${path}.q`);
  if (Object.hasOwn(question, 'r')) stringAt(question.r, `${path}.r`);
  if (Object.hasOwn(question, 'to')) stringAt(question.to, `${path}.to`);
  if (question.r && question.to) fail(path, 'cannot have both r and to');
};
function validateData(data) {
  objectAt(data, 'data');
  const { META, DECISIONS, GROUPS, NODES, FLOWS, CH, HOW_HTML } = data;

  objectAt(META, 'META');
  ['title', 'sourcePath', 'buildCmd', 'intro', 'onePara', 'platformGives', 'weOwn', 'filesystem'].forEach((key) => stringAt(META[key], `META.${key}`));
  arrayAt(META.stats, 'META.stats');
  META.stats.forEach((stat, index) => {
    objectAt(stat, `META.stats[${index}]`);
    stringAt(stat.k, `META.stats[${index}].k`);
    stringAt(stat.v, `META.stats[${index}].v`);
  });
  arrayAt(META.costModel, 'META.costModel');
  META.costModel.forEach((line, index) => stringAt(line, `META.costModel[${index}]`));
  if (Object.hasOwn(META, 'deepDive') && META.deepDive !== undefined) stringAt(META.deepDive, 'META.deepDive');
  if (Object.hasOwn(META, 'artifactUrl') && META.artifactUrl !== undefined) stringAt(META.artifactUrl, 'META.artifactUrl');

  arrayAt(DECISIONS, 'DECISIONS');
  DECISIONS.forEach((decision, index) => {
    objectAt(decision, `DECISIONS[${index}]`);
    ['axis', 'decision', 'adr'].forEach((key) => stringAt(decision[key], `DECISIONS[${index}].${key}`));
  });

  arrayAt(GROUPS, 'GROUPS');
  GROUPS.forEach((group, index) => {
    objectAt(group, `GROUPS[${index}]`);
    stringAt(group.title, `GROUPS[${index}].title`);
  });
  const groupIds = uniqueIds(GROUPS, 'GROUPS');

  arrayAt(NODES, 'NODES');
  NODES.forEach((node, index) => {
    objectAt(node, `NODES[${index}]`);
    ['id', 'code', 'name', 'short', 'group', 'state', 'kind', 'one', 'what', 'how'].forEach((key) => stringAt(node[key], `NODES[${index}].${key}`));
    ['gx', 'gy', 'w', 'd', 'h'].forEach((key) => {
      if (typeof node[key] !== 'number' || !Number.isFinite(node[key])) fail(`NODES[${index}].${key}`, 'must be a finite number');
    });
    ['w', 'd', 'h'].forEach((key) => {
      if (node[key] <= 0) fail(`NODES[${index}].${key}`, 'must be greater than zero');
    });
    if (!groupIds.has(node.group)) fail(`NODES[${index}].group`, `unknown group "${node.group}"`);
    if (!['current', 'external', 'planned'].includes(node.state)) fail(`NODES[${index}].state`, 'must be current, external, or planned');
    if (Object.hasOwn(node, 'ghost') && typeof node.ghost !== 'boolean') fail(`NODES[${index}].ghost`, 'must be a boolean');
    const planned = node.state === 'planned';
    if (planned !== (node.ghost === true)) fail(`NODES[${index}].ghost`, 'must match planned state');
    if (planned !== (node.group === 'planned')) fail(`NODES[${index}].group`, 'must match planned state');
    if (Object.hasOwn(node, 'steps')) {
      arrayAt(node.steps, `NODES[${index}].steps`);
      node.steps.forEach((step, stepIndex) => {
        arrayAt(step, `NODES[${index}].steps[${stepIndex}]`);
        if (step.length !== 2) fail(`NODES[${index}].steps[${stepIndex}]`, 'must have two values');
        stringAt(step[0], `NODES[${index}].steps[${stepIndex}][0]`);
        stringAt(step[1], `NODES[${index}].steps[${stepIndex}][1]`);
      });
    }
    arrayAt(node.cond, `NODES[${index}].cond`);
    node.cond.forEach((question, questionIndex) => validateQuestion(question, `NODES[${index}].cond[${questionIndex}]`));
  });
  const nodeIds = uniqueIds(NODES, 'NODES');
  const nodeCodes = new Set();
  NODES.forEach((node, index) => {
    if (nodeCodes.has(node.code)) fail(`NODES[${index}].code`, `duplicate code "${node.code}"`);
    nodeCodes.add(node.code);
  });

  arrayAt(FLOWS, 'FLOWS');
  FLOWS.forEach((flow, index) => {
    objectAt(flow, `FLOWS[${index}]`);
    stringAt(flow.name, `FLOWS[${index}].name`);
    arrayAt(flow.hops, `FLOWS[${index}].hops`);
    if (!flow.hops.length) fail(`FLOWS[${index}].hops`, 'must not be empty');
    flow.hops.forEach((hop, hopIndex) => validateHop(hop, `FLOWS[${index}].hops[${hopIndex}]`, nodeIds));
  });
  uniqueIds(FLOWS, 'FLOWS');

  arrayAt(CH, 'CH');
  if (CH.length < 2) fail('CH', 'must include progressive and final chapters');
  CH.forEach((chapter, index) => {
    objectAt(chapter, `CH[${index}]`);
    ['title', 'lede', 'story'].forEach((key) => stringAt(chapter[key], `CH[${index}].${key}`));
    arrayAt(chapter.reveal, `CH[${index}].reveal`);
    chapter.reveal.forEach((nodeId, revealIndex) => {
      stringAt(nodeId, `CH[${index}].reveal[${revealIndex}]`);
      if (!nodeIds.has(nodeId)) fail(`CH[${index}].reveal[${revealIndex}]`, `unknown node "${nodeId}"`);
    });
  });
  uniqueIds(CH, 'CH');
  const finalIndex = CH.length - 1;
  const finalChapter = CH[finalIndex];
  if (finalChapter.reveal.length) fail(`CH[${finalIndex}].reveal`, 'must be empty in the final chapter');
  if (finalChapter.flow !== null) fail(`CH[${finalIndex}].flow`, 'must be null in the final chapter');
  const revealed = new Set();
  CH.slice(0, -1).forEach((chapter, index) => {
    if (chapter.reveal.length > 3) fail(`CH[${index}].reveal`, 'must add no more than three structures');
    chapter.reveal.forEach((nodeId, revealIndex) => {
      if (revealed.has(nodeId)) fail(`CH[${index}].reveal[${revealIndex}]`, `duplicate progressive reveal "${nodeId}"`);
      revealed.add(nodeId);
    });
    arrayAt(chapter.flow, `CH[${index}].flow`);
    chapter.flow.forEach((hop, hopIndex) => {
      const path = `CH[${index}].flow[${hopIndex}]`;
      validateHop(hop, path, nodeIds);
      if (!revealed.has(hop[0]) || !revealed.has(hop[1])) fail(path, 'endpoints must be revealed by this chapter');
    });
  });
  NODES.forEach((node, index) => {
    if (!revealed.has(node.id)) fail(`NODES[${index}].id`, 'must appear once in a progressive reveal');
  });

  stringAt(HOW_HTML, 'HOW_HTML');
}
const cloneData = (data) => JSON.parse(JSON.stringify(data));
const selfTest = () => {
  const current = { META, DECISIONS, GROUPS, NODES, FLOWS, CH, HOW_HTML };
  validateData(current);
  const cases = [
    ['missing META field', (data) => { delete data.META.title; }],
    ['duplicate node ID', (data) => { data.NODES[1].id = data.NODES[0].id; }],
    ['invalid group reference', (data) => { data.NODES[0].group = 'missing'; }],
    ['invalid flow endpoint', (data) => { data.FLOWS[0].hops[0][0] = 'missing'; }],
    ['question with both states', (data) => { data.NODES[0].cond = [{ q: 'Question?', r: 'Resolved.', to: 'Route.' }]; }],
    ['progressive chapter over three reveals', (data) => { data.CH[0].reveal = ['SRC', 'WB', 'STORE', 'SCOPE']; }],
    ['invalid final chapter', (data) => { data.CH.at(-1).flow = []; }],
  ];
  cases.forEach(([name, change]) => {
    const malformed = cloneData(current);
    change(malformed);
    try {
      validateData(malformed);
    } catch (error) {
      console.log(`self-test rejected: ${name}`);
      return;
    }
    throw new Error(`Self-test accepted malformed data: ${name}`);
  });
  console.log(`self-test passed: valid current data and ${cases.length} malformed cases rejected`);
};

// ---------- shared helpers ----------
const Q = (c) => (typeof c === 'string' ? { q: c } : c);
const md = (s) =>
  String(s)
    .replace(/<code>(.*?)<\/code>/g, '`$1`')
    .replace(/<mark>(.*?)<\/mark>/g, '**$1**')
    .replace(/<em>(.*?)<\/em>/g, '_$1_')
    .replace(/<b>(.*?)<\/b>/g, '**$1**')
    .replace(/<\/p>\s*<p>/g, '\n\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .trim();
const countQuestions = () => {
  const count = { open: 0, routed: 0, resolved: 0 };
  NODES.forEach((node) => node.cond.map(Q).forEach((question) => {
    if (question.r) count.resolved++;
    else if (question.to) count.routed++;
    else count.open++;
  }));
  return count;
};
let cnt;

// ---------- SYSTEM.md ----------
function buildSystemMd() {
  const out = [];
  out.push(`# ${META.title} — System Definition`, '');
  out.push(META.intro, '');
  out.push(`_Question status: **${cnt.open} open · ${cnt.routed} routed · ${cnt.resolved} resolved**._`, '');
  out.push('## One paragraph', '', META.onePara, '');
  out.push('## Decisions locked', '', '| Axis | Decision | Authority |', '|---|---|---|');
  DECISIONS.forEach((d) => out.push(`| ${d.axis} | ${d.decision} | ${d.adr} |`));
  out.push('');
  out.push('## Cost model', '');
  META.costModel.forEach((l) => out.push(l));
  if (META.deepDive) out.push('## Deep dives', '', META.deepDive, '');
  out.push('## Reading order (the atlas chapters)', '');
  CH.forEach((c, i) => out.push(`${i + 1}. **${c.title}** — ${md(c.lede)}${c.reveal.length ? ` _(adds ${c.reveal.join(', ')})_` : ''}`));
  out.push('');
  out.push('## Structures', '');
  const index = [];
  for (const g of GROUPS) {
    out.push(`### ${g.title}${g.id === 'off' ? ' (designed for, not built)' : ''}`, '');
    for (const n of NODES.filter((n) => n.group === g.id)) {
      const status = n.ghost ? 'planned — not operational' : (n.state === 'external' ? 'external boundary' : 'current pilot');
      out.push(`#### ${n.code} · ${n.name}`, '');
      out.push(`**Status.** ${status}.`, '');
      out.push(`**In one line.** ${md(n.one)}`, '');
      out.push(`**What it does.** ${md(n.what)}`, '');
      out.push(`**How it's built.** ${md(n.how)}`, '');
      if (n.steps) {
        out.push('**Steps in execution.**', '');
        n.steps.forEach((s, i) => out.push(`${i + 1}. **${s[0]}** — ${s[1]}`));
        out.push('');
      }
      const cs = (n.cond || []).map(Q);
      if (cs.length) {
        out.push('**Questions.**', '');
        cs.forEach((c, i) => {
          const id = `Q-${n.code}${i + 1}`;
          out.push(c.r ? `- ~~**${id}** ${md(c.q)}~~ ✓ ${md(c.r)}` : c.to ? `- **${id}** ${md(c.q)} → _${md(c.to)}_` : `- **${id}** ${md(c.q)}`);
          index.push([id, n.code, c]);
        });
        out.push('');
      }
    }
  }
  out.push('## Flows (representative packets)', '', 'Payload shapes are what the design implies, not measured traffic.', '');
  for (const f of FLOWS) {
    out.push(`### ${f.name}`, '', '| # | From → To | Packet | Representative payload |', '|---|---|---|---|');
    f.hops.forEach((h, i) => out.push(`| ${i + 1} | ${h[0]} → ${h[1]} | ${h[2]} | \`${JSON.stringify(h[3]).replace(/\|/g, '\\|')}\` |`));
    out.push('');
  }
  out.push('## Questions — index', '', 'Reference by ID. ✓ resolved (with date) · → routed · otherwise open.', '');
  index.forEach(([id, code, c]) => out.push(
    c.r ? `- ~~**${id}**~~ (${code}) ✓ ${md(c.r)}`
      : c.to ? `- **${id}** (${code}) ${md(c.q)} → _${md(c.to)}_`
        : `- **${id}** (${code}) ${md(c.q)}`
  ));
  out.push('');
  if (META.platformGives || META.weOwn) out.push('## What the platform gives vs what we own', '', `**Platform gives:** ${META.platformGives||''}`, '', `**We own:** ${META.weOwn||''}`, '');
  if (META.filesystem) out.push('## Planned filesystem', '', '```', META.filesystem.trimEnd(), '```', '');
  out.push('## How this file is maintained', '', `Generated from \`${META.sourcePath||'atlas/data.mjs'}\` by \`${META.buildCmd||'node atlas/build.mjs'}\`, which also builds the interactive atlas (\`atlas.html\`${META.artifactUrl?`, published at ${META.artifactUrl}`:''}). Edit the data file and rebuild. Do not edit this generated file directly.`, '');
  return out.join('\n');
}

// ---------- atlas.html ----------
function buildAtlasHtml() {
  const tpl = readFileSync(join(here, 'template.html'), 'utf8');
  const decisionsHtml = DECISIONS.map((d) => `<li><b>${d.axis}.</b> ${md(d.decision).replace(/\*\*(.*?)\*\*/g, '<b>$1</b>').replace(/`(.*?)`/g, '<code>$1</code>').replace(/\[(.*?)\]\((.*?)\)/g, '$1')}</li>`).join('');
  const data = [
    `const GROUPS = ${JSON.stringify(GROUPS)};`,
    `const NODES = ${JSON.stringify(NODES)};`,
    `const FLOWS = ${JSON.stringify(FLOWS)};`,
    `const CH = ${JSON.stringify(CH)};`,
    `const HOW_HTML = ${JSON.stringify(HOW_HTML)};`,
    `const DECISIONS_HTML = ${JSON.stringify(decisionsHtml)};`,
  ].join('\n');
  return '<!-- Generated from data.mjs by build.mjs. Do not edit this file directly. -->\n' + tpl.replace('__TITLE__', META.title).replace('/*__DATA__*/', data + `\nconst STATS = ${JSON.stringify(META.stats||[])};\nconst TITLE = ${JSON.stringify(META.title||'System')};`);
}

const args = new Set(process.argv.slice(2));
if (args.has('--self-test')) {
  selfTest();
} else {
  validateData({ META, DECISIONS, GROUPS, NODES, FLOWS, CH, HOW_HTML });
  cnt = countQuestions();
  if (args.has('--validate-only')) {
    console.log('valid current data');
  } else {
    writeFileSync(join(outDir, 'SYSTEM.md'), buildSystemMd());
    writeFileSync(join(outDir, 'atlas.html'), buildAtlasHtml());
    console.log(`built SYSTEM.md + atlas.html · ${cnt.open} open · ${cnt.routed} routed · ${cnt.resolved} resolved · ${NODES.length} structures · ${DECISIONS.length} decisions`);
  }
}
