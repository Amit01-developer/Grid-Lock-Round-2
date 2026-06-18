import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Legend,
  LinearScale,
  LineController,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js';
import { useEffect, useRef } from 'react';

Chart.register(
  BarController,
  BarElement,
  LineController,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Legend,
  Tooltip,
);

export default function DailyStatisticsChart({ data = [] }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) {
      return undefined;
    }

    const chart = new Chart(canvasRef.current, {
      type: 'bar',
      data: {
        labels: data.map((item) => item.date),
        datasets: [
          {
            type: 'bar',
            label: 'Violations',
            data: data.map((item) => item.total),
            backgroundColor: '#1f4e79',
            yAxisID: 'y',
          },
          {
            type: 'line',
            label: 'Safety Index',
            data: data.map((item) => item.safety_index),
            borderColor: '#0f766e',
            backgroundColor: '#0f766e',
            tension: 0.35,
            yAxisID: 'y1',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: { labels: { color: '#64748b', boxWidth: 12 } },
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: '#64748b', maxTicksLimit: 8 } },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(148, 163, 184, 0.2)' },
            ticks: { precision: 0, color: '#64748b' },
          },
          y1: {
            beginAtZero: true,
            max: 100,
            position: 'right',
            grid: { display: false },
            ticks: { precision: 0, color: '#64748b' },
          },
        },
      },
    });

    return () => chart.destroy();
  }, [data]);

  return <canvas ref={canvasRef} aria-label="Daily statistics chart" role="img" />;
}

