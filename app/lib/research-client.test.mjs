import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readEvents, postJSON } from './research-client.mjs';
import { applyPreparedGuide } from './prepared-guide.mjs';
import { promptFeedback } from './prompt-feedback.mjs';
const stream = chunks => new ReadableStream({ start(controller) { for (const chunk of chunks) controller.enqueue(new TextEncoder().encode(chunk)); controller.close(); } });
test('SSE survives arbitrary chunk boundaries and CRLF', async () => {
  const events = [];
  await readEvents(stream(['event: pro', 'gress\r', '\ndata: {"step":1}\r\n\r', '\nevent: result\ndata: {"trials":[]}\n\n']), (kind, data) => events.push([kind, data]));
  assert.deepEqual(events, [['progress', {step: 1}], ['result', { trials: [] }]]);
});
test('EOF without a terminal result is an error, retaining delivered records', async () => {
  const events = [];
  await assert.rejects(readEvents(stream(['event: records\ndata: {"trials":[1]}\n\n']), (kind, data) => events.push(data)), /connection ended/);
  assert.equal(events[0].trials[0], 1);
});
test('upstream error event is surfaced', async () => {
  await assert.rejects(readEvents(stream(['event: error\ndata: {"message":"Retry search"}\n\n']), () => {}), /Retry search/);
});
test('malformed JSON cannot produce a success state', async () => {
  await assert.rejects(readEvents(stream(['event: result\ndata: not-json\n\n']), () => {}));
});
test('daily quota errors show the local reset time', async () => {
  await assert.rejects(readEvents(stream(['event: error\ndata: {"message":"Daily budget reached.","code":"daily_limit","resetsAt":"2026-11-15T08:00:00Z"}\n\n']), () => {}), error => error.code === 'daily_limit' && /Resets/.test(error.message));
});
test('HTTP burst errors include the retry delay', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({error:'Too many requests.',code:'burst_limit',retryAfter:60}), {status:429,headers:{'Content-Type':'application/json'}});
  try { await assert.rejects(postJSON('/api/search',{}), error => error.code === 'burst_limit' && /60 seconds/.test(error.message)); }
  finally { globalThis.fetch = original; }
});
test('editing the extracted profile cannot reuse stale generated questions', () => {
  const profile = {condition:'Lung cancer',city:'Atlanta'};
  const prepared = {profile,guide:[{title:'Original prompt question'}]};
  const result = {guide:[{title:'Updated standard question'}],guideOrigin:'standard'};
  assert.equal(applyPreparedGuide(result,prepared,profile).guideOrigin,'ai');
  assert.equal(applyPreparedGuide(result,prepared,{...profile,city:'Seattle'}).guideOrigin,'standard');
});
test('unrelated prompts get a fixed actionable message and trusted learning link', () => {
  const feedback = promptFeedback('off_topic');
  assert.match(feedback.title, /clinical research/i);
  assert.match(feedback.example, /fictional/i);
  assert.equal(new URL(feedback.resource.href).hostname, 'www.nih.gov');
  assert.equal(promptFeedback('unknown_provider_error'), null);
});
test('missing-condition feedback differs from unrelated-topic feedback', () => {
  assert.notEqual(promptFeedback('needs_details').title, promptFeedback('off_topic').title);
  assert.match(promptFeedback('needs_details').message, /condition/i);
});
test('HTTP semantic rejection keeps its machine code for the input screen', async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => new Response(JSON.stringify({error:'Add a condition.',code:'needs_details'}), {status:422,headers:{'Content-Type':'application/json'}});
  try { await assert.rejects(postJSON('/api/extract',{}), error => error.code === 'needs_details' && error.message === 'Add a condition.'); }
  finally { globalThis.fetch = original; }
});
