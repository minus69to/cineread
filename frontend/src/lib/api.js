const API = 'http://localhost:8000';

export async function* streamChat(message, sessionId) {
  const res = await fetch(`${API}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId }),
  });

  if (!res.ok) throw new Error(`HTTP ${res.status}`);

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
      if (!line.startsWith('data: ')) continue;
      const raw = line.slice(6).trim();
      if (raw === '[DONE]') return;
      try {
        yield JSON.parse(raw);
      } catch {
        // skip malformed lines
      }
    }
  }
}

export async function searchMedia(q, type = 'all') {
  const res = await fetch(`${API}/media/search?q=${encodeURIComponent(q)}&type=${type}`);
  return res.json();
}

export async function getMedia(mediaId) {
  const res = await fetch(`${API}/media/${mediaId}`);
  return res.json();
}
