<script>
  let { stats } = $props();

  const LEVELS = [
    { key: 'ERROR', color: '#ef4444', bg: 'rgba(239,68,68,0.08)' },
    { key: 'WARN',  color: '#f59e0b', bg: 'rgba(245,158,11,0.08)' },
    { key: 'INFO',  color: '#3b82f6', bg: 'rgba(59,130,246,0.08)' },
    { key: 'DEBUG', color: '#6b7280', bg: 'rgba(107,114,128,0.08)' },
  ];
</script>

<div class="stats-bar">
  {#each LEVELS as { key, color, bg }}
    <div class="card" style="--color: {color}; --bg: {bg}">
      <span class="label">{key}</span>
      <span class="count">{(stats?.by_level?.[key] ?? 0).toLocaleString()}</span>
    </div>
  {/each}
</div>

<style>
  .stats-bar {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
  }

  .card {
    background: var(--bg);
    border-radius: 10px;
    padding: 1.25rem 1.5rem;
    border-left: 4px solid var(--color);
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }

  .label {
    display: block;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: var(--color);
    margin-bottom: 0.4rem;
  }

  .count {
    display: block;
    font-size: 2rem;
    font-weight: 700;
    color: #1e293b;
    line-height: 1;
  }
</style>
