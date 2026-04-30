<script>
  import { fetchStats, fetchTimeline } from './lib/api.js';
  import StatsBar from './lib/StatsBar.svelte';
  import Timeline from './lib/Timeline.svelte';
  import LogTable from './lib/LogTable.svelte';

  let stats = $state(null);
  let timeline = $state([]);

  async function load() {
    [stats, timeline] = await Promise.all([fetchStats(), fetchTimeline(24)]);
  }

  load();
</script>

<div class="app">
  <header>
    <span class="logo">◈ Log Pulse</span>
    <span class="sub">Observability Dashboard</span>
  </header>

  <main>
    <StatsBar {stats} />
    <Timeline data={timeline} />
    <LogTable />
  </main>
</div>

<style>
  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  header {
    background: #0f172a;
    padding: 0 2rem;
    height: 56px;
    display: flex;
    align-items: center;
    gap: 1rem;
    position: sticky;
    top: 0;
    z-index: 10;
  }

  .logo {
    color: white;
    font-weight: 700;
    font-size: 1.1rem;
    letter-spacing: -0.01em;
  }

  .sub {
    color: #475569;
    font-size: 0.875rem;
  }

  main {
    flex: 1;
    padding: 1.5rem 2rem;
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    max-width: 1400px;
    width: 100%;
    margin: 0 auto;
  }
</style>
