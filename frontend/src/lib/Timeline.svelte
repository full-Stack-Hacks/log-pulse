<script>
  import Chart from 'chart.js/auto';

  let { data = [] } = $props();

  let canvas = $state();

  const COLORS = { DEBUG: '#6b7280', INFO: '#3b82f6', WARN: '#f59e0b', ERROR: '#ef4444' };
  const LEVELS = ['DEBUG', 'INFO', 'WARN', 'ERROR'];

  $effect(() => {
    if (!canvas || !data.length) return;

    const buckets = [...new Set(data.map(d => d.bucket))].sort();

    const chart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: buckets.map(b =>
          new Date(b).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        ),
        datasets: LEVELS.map(level => ({
          label: level,
          backgroundColor: COLORS[level],
          data: buckets.map(bucket => {
            const match = data.find(d => d.bucket === bucket && d.level === level);
            return match?.count ?? 0;
          }),
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 12, padding: 16 } },
        },
        scales: {
          x: { stacked: true, grid: { display: false } },
          y: { stacked: true, beginAtZero: true },
        },
      },
    });

    return () => chart.destroy();
  });
</script>

<div class="timeline">
  <h2>Activity — last 24h</h2>
  <div class="chart-wrap">
    <canvas bind:this={canvas}></canvas>
  </div>
</div>

<style>
  .timeline {
    background: white;
    border-radius: 10px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }

  h2 {
    font-size: 0.75rem;
    font-weight: 700;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 1rem;
  }

  .chart-wrap {
    height: 220px;
    position: relative;
  }
</style>
