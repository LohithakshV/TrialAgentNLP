export async function postJSON(path, payload, signal) {
  const response = await fetch(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload), signal, cache: 'no-store' });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw serviceError({ ...data, message: data.error || 'The service is unavailable. Please try again.' });
  }
  return response;
}

export async function readEvents(body, onEvent) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = '', complete = false;
  function consume(block) {
    const lines = block.replaceAll('\r', '').split('\n');
    const kind = lines.find(line => line.startsWith('event:'))?.slice(6).trim();
    const text = lines.filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n');
    if (!text) return;
    const data = JSON.parse(text);
    if (kind === 'error') throw serviceError(data);
    if (kind === 'result') complete = true;
    onEvent(kind, data);
  }
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      buffer = buffer.replaceAll('\r\n', '\n');
      let index;
      while ((index = buffer.indexOf('\n\n')) !== -1) { consume(buffer.slice(0, index)); buffer = buffer.slice(index + 2); }
      if (done) break;
    }
    if (!complete) throw new Error('The connection ended before the search finished. Please try again.');
  } finally { await reader.cancel().catch(() => {}); reader.releaseLock(); }
}

function serviceError(data) {
  let message = data.message;
  if (data.code?.includes('daily_limit') && data.resetsAt) message += ` Resets ${new Date(data.resetsAt).toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZoneName: 'short' })}.`;
  else if (data.retryAfter) message += ` Try again in ${data.retryAfter} seconds.`;
  const error = new Error(message); error.code = data.code; return error;
}
