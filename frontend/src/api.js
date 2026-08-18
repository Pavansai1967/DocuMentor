const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export function parseSseLine(line) {
  const trimmed = line.trim();
  if (!trimmed.startsWith('data:')) return null;
  const payload = trimmed.slice(5).trim();
  if (payload === '[DONE]') return { type: 'done' };
  try {
    return JSON.parse(payload);
  } catch {
    return null;
  }
}

export async function uploadPdf(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? 'Upload failed');
  }
  return res.json();
}

export async function listDocuments() {
  const res = await fetch(`${BASE}/documents`);
  if (!res.ok) throw new Error('Failed to load document library');
  return res.json();
}

export async function streamChat({ question, onToken, onSources, onTrace, onDone, onError, signal }) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
    signal,
  });
  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? 'Chat request failed');
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';
    for (const line of lines) {
      const event = parseSseLine(line);
      if (!event) continue;
      if (event.type === 'token') onToken?.(event.text);
      else if (event.type === 'sources') onSources?.(event.sources);
      else if (event.type === 'trace') onTrace?.(event.trace);
      else if (event.type === 'done') onDone?.();
      else if (event.type === 'error') onError?.(new Error(event.message));
    }
  }
}
