const BASE = 'http://localhost:8000';

export async function fetchStats() {
  const res = await fetch(`${BASE}/logs/stats`);
  return res.json();
}

export async function fetchTimeline(hours = 24) {
  const res = await fetch(`${BASE}/logs/timeline?hours=${hours}`);
  return res.json();
}

export async function fetchLogs({ level = '', service = '', search = '', limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit, offset });
  if (level) params.set('level', level);
  if (service) params.set('service', service);
  if (search) params.set('search', search);
  const res = await fetch(`${BASE}/logs?${params}`);
  return res.json();
}
