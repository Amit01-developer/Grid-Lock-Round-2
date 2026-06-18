import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js';
import { useEffect, useRef } from 'react';

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Legend, Tooltip);

export default function WeeklyStatisticsChart({ data = [] }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!canvasRef.current) {
      return undefined;
    }

    const chart = new Chart(canvasRef.current, {
      type: 'bar',
      data: {
        labels: data.map((item) => item.week_start),
        datasets: [
          {
            label: 'Severity score',
            data: data.map((item) => item.severity_score),
            backgroundColor: '#b45309',
          },
          {
            label: 'Violations',
            data: data.map((item) => item.total),
            backgroundColor: '#1f4e79',
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#64748b', boxWidth: 12 } },
          tooltip: {
            callbacks: {
              afterLabel: (context) => {
                const item = data[context.dataIndex];
                return item ? `Safety Index: ${item.safety_index}/100` : '';
              },
            },
          },
        },
        scales: {
          x: { stacked: false, grid: { display: false }, ticks: { color: '#64748b' } },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(148, 163, 184, 0.2)' },
            ticks: { precision: 0, color: '#64748b' },
          },
        },
      },
    });

    return () => chart.destroy();
  }, [data]);

  return <canvas ref={canvasRef} aria-label="Weekly statistics chart" role="img" />;
}

