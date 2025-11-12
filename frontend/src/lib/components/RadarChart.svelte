<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Chart, RadarController, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend } from 'chart.js';

  // Register Chart.js components
  Chart.register(RadarController, RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

  interface Props {
    data: Record<string, number>;
    title?: string;
    height?: number;
  }

  let { data, title = 'Skills', height = 360 }: Props = $props();

  let canvas: HTMLCanvasElement;
  let chart: Chart | null = null;

  // Format skill names for display
  function formatSkillName(skill: string): string {
    return skill
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  function createChart() {
    if (!canvas || !data) return;

    const labels = Object.keys(data).map(formatSkillName);
    const values = Object.values(data);

    chart = new Chart(canvas, {
      type: 'radar',
      data: {
        labels,
        datasets: [
          {
            label: title,
            data: values,
            backgroundColor: 'rgba(20, 184, 166, 0.2)',
            borderColor: 'rgba(20, 184, 166, 1)',
            borderWidth: 2,
            pointBackgroundColor: 'rgba(20, 184, 166, 1)',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: 'rgba(20, 184, 166, 1)',
            pointRadius: 4,
            pointHoverRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            beginAtZero: true,
            max: 100,
            ticks: {
              stepSize: 20,
              color: 'rgba(179, 179, 179, 0.8)',
              backdropColor: 'transparent'
            },
            grid: {
              color: 'rgba(42, 42, 42, 0.8)'
            },
            pointLabels: {
              color: 'rgba(255, 255, 255, 0.9)',
              font: {
                size: 12,
                weight: '500'
              }
            }
          }
        },
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            backgroundColor: 'rgba(31, 31, 31, 0.95)',
            titleColor: '#fff',
            bodyColor: '#b3b3b3',
            borderColor: 'rgba(42, 42, 42, 1)',
            borderWidth: 1,
            padding: 12,
            displayColors: false,
            callbacks: {
              label: function(context) {
                return `${context.parsed.r.toFixed(1)}/100`;
              }
            }
          }
        }
      }
    });
  }

  onMount(() => {
    createChart();
  });

  onDestroy(() => {
    if (chart) {
      chart.destroy();
    }
  });

  // Recreate chart when data changes
  $effect(() => {
    if (chart && data) {
      const labels = Object.keys(data).map(formatSkillName);
      const values = Object.values(data);

      chart.data.labels = labels;
      chart.data.datasets[0].data = values;
      chart.update();
    }
  });
</script>

<div class="radar-chart-container" style="height: {height}px;">
  <canvas bind:this={canvas}></canvas>
</div>

<style>
  .radar-chart-container {
    position: relative;
    width: 100%;
  }
</style>
