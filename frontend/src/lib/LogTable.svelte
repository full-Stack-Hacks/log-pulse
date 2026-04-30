<script>
  import { fetchLogs } from './api.js';

  const LIMIT = 50;
  const LEVELS = ['', 'DEBUG', 'INFO', 'WARN', 'ERROR'];
  const SERVICES = [
    '',
    'auth-service',
    'api-gateway',
    'payments-service',
    'user-service',
    'notification-service',
  ];
  const LEVEL_CONFIG = {
    DEBUG: { color: '#6b7280', bg: 'rgba(107,114,128,0.1)' },
    INFO:  { color: '#3b82f6', bg: 'rgba(59,130,246,0.1)' },
    WARN:  { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
    ERROR: { color: '#ef4444', bg: 'rgba(239,68,68,0.1)' },
  };

  let logs = $state([]);
  let total = $state(0);
  let loading = $state(false);
  let filters = $state({ level: '', service: '', search: '', offset: 0 });

  // Separate draft for search so we can debounce it
  let searchDraft = $state('');
  let debounceTimer;

  $effect(() => {
    const q = searchDraft;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      filters = { ...filters, search: q, offset: 0 };
    }, 300);
    return () => clearTimeout(debounceTimer);
  });

  $effect(() => {
    const f = { ...filters };
    loading = true;
    fetchLogs({ ...f, limit: LIMIT }).then(r => {
      logs = r.items;
      total = r.total;
      loading = false;
    });
  });

  function setFilter(key, value) {
    filters = { ...filters, [key]: value, offset: 0 };
  }

  function prevPage() {
    filters = { ...filters, offset: Math.max(0, filters.offset - LIMIT) };
  }

  function nextPage() {
    if (filters.offset + LIMIT < total) {
      filters = { ...filters, offset: filters.offset + LIMIT };
    }
  }

  function formatTime(ts) {
    return new Date(ts).toLocaleString();
  }

  const page = $derived(Math.floor(filters.offset / LIMIT) + 1);
  const pageCount = $derived(Math.ceil(total / LIMIT));
</script>

<div class="log-table">
  <div class="toolbar">
    <div class="filters">
      <select value={filters.level} onchange={e => setFilter('level', e.target.value)}>
        {#each LEVELS as l}
          <option value={l}>{l || 'All levels'}</option>
        {/each}
      </select>

      <select value={filters.service} onchange={e => setFilter('service', e.target.value)}>
        {#each SERVICES as s}
          <option value={s}>{s || 'All services'}</option>
        {/each}
      </select>

      <input
        type="text"
        placeholder="Search messages…"
        bind:value={searchDraft}
      />
    </div>

    <span class="total">{loading ? '…' : total.toLocaleString()} logs</span>
  </div>

  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>Timestamp</th>
          <th>Level</th>
          <th>Service</th>
          <th>Message</th>
        </tr>
      </thead>
      <tbody>
        {#if loading}
          <tr><td colspan="4" class="empty">Loading…</td></tr>
        {:else if logs.length === 0}
          <tr><td colspan="4" class="empty">No logs found.</td></tr>
        {:else}
          {#each logs as log (log.id)}
            <tr>
              <td class="time">{formatTime(log.timestamp)}</td>
              <td>
                <span
                  class="badge"
                  style="color: {LEVEL_CONFIG[log.level].color}; background: {LEVEL_CONFIG[log.level].bg}"
                >{log.level}</span>
              </td>
              <td class="service">{log.service}</td>
              <td class="message">{log.message}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>

  <div class="pagination">
    <button onclick={prevPage} disabled={filters.offset === 0}>← Prev</button>
    <span>Page {page} of {pageCount || 1}</span>
    <button onclick={nextPage} disabled={filters.offset + LIMIT >= total}>Next →</button>
  </div>
</div>

<style>
  .log-table {
    background: white;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    overflow: hidden;
  }

  .toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid #e2e8f0;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .filters {
    display: flex;
    gap: 0.75rem;
    flex-wrap: wrap;
  }

  select, input {
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 0.4rem 0.75rem;
    font-size: 0.875rem;
    background: white;
    color: #1e293b;
    outline: none;
  }

  select:focus, input:focus {
    border-color: #3b82f6;
    box-shadow: 0 0 0 2px rgba(59,130,246,0.15);
  }

  input { width: 200px; }

  .total {
    font-size: 0.875rem;
    color: #64748b;
    white-space: nowrap;
  }

  .table-wrap { overflow-x: auto; }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }

  thead th {
    text-align: left;
    padding: 0.6rem 1.25rem;
    font-size: 0.7rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    border-bottom: 1px solid #e2e8f0;
    background: #f8fafc;
  }

  tbody tr { border-bottom: 1px solid #f1f5f9; }
  tbody tr:last-child { border-bottom: none; }
  tbody tr:hover { background: #f8fafc; }

  td {
    padding: 0.65rem 1.25rem;
    vertical-align: top;
  }

  .time {
    color: #64748b;
    white-space: nowrap;
    font-size: 0.8rem;
    font-variant-numeric: tabular-nums;
  }

  .badge {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.05em;
  }

  .service {
    color: #475569;
    white-space: nowrap;
  }

  .message {
    color: #1e293b;
    max-width: 500px;
  }

  .empty {
    text-align: center;
    color: #94a3b8;
    padding: 3rem;
  }

  .pagination {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 0.875rem 1rem;
    border-top: 1px solid #e2e8f0;
    font-size: 0.875rem;
    color: #475569;
  }

  button {
    border: 1px solid #cbd5e1;
    background: white;
    border-radius: 6px;
    padding: 0.35rem 0.85rem;
    cursor: pointer;
    font-size: 0.875rem;
    color: #475569;
  }

  button:hover:not(:disabled) {
    background: #f1f5f9;
    border-color: #94a3b8;
  }

  button:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
</style>
