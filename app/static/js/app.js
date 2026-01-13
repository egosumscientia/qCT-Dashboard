const initCharts = () => {
  if (!window.QCT_DATA) {
    return;
  }

  const riskColors = {
    low: '#5cb85c',
    medium: '#f0ad4e',
    high: '#d9534f',
  };

  const buildRiskFallback = (labels, values) => {
    const total = values.reduce((sum, value) => sum + value, 0);
    const rows = labels
      .map((label, index) => {
        const value = values[index];
        const percent = total ? Math.round((value / total) * 100) : 0;
        const color = riskColors[label] || '#94a3b8';
        return `
          <div class="risk-row">
            <div class="risk-name">${label}</div>
            <div class="risk-bar">
              <span style="width: ${percent}%; background: ${color};"></span>
            </div>
            <div class="risk-meta">${value}</div>
          </div>
        `;
      })
      .join('');
    return `<div class="risk-list">${rows}</div>`;
  };

  const buildTrendFallback = (labels, values) => {
    if (!labels.length) {
      return '<p class="chart-empty">No trend data available.</p>';
    }
    const width = 320;
    const height = 140;
    const padding = 16;
    const max = Math.max(...values, 1);
    const min = Math.min(...values, 0);
    const range = max - min || 1;
    const step = values.length > 1 ? (width - padding * 2) / (values.length - 1) : 0;
    const points = values
      .map((value, index) => {
        const x = padding + index * step;
        const y = padding + (height - padding * 2) * (1 - (value - min) / range);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      })
      .join(' ');
    const first = labels[0];
    const last = labels[labels.length - 1];
    return `
      <div class="trend-wrapper">
        <svg viewBox="0 0 ${width} ${height}" class="trend-spark" role="img" aria-label="Average volume trend">
          <polyline points="${points}" />
        </svg>
        <div class="trend-meta">
          <span>${first}</span>
          <span>${last}</span>
        </div>
      </div>
    `;
  };

  const riskCtx = document.getElementById('riskChart');
  if (riskCtx) {
    const labels = window.QCT_DATA.riskBreakdown.map((item) => item.label);
    const values = window.QCT_DATA.riskBreakdown.map((item) => item.value);
    const fallback = document.getElementById('riskFallback');
    if (typeof Chart !== 'undefined') {
      new Chart(riskCtx, {
        type: 'doughnut',
        data: {
          labels,
          datasets: [
            {
              data: values,
              backgroundColor: ['#5cb85c', '#f0ad4e', '#d9534f'],
            },
          ],
        },
        options: {
          maintainAspectRatio: false,
          plugins: {
            legend: { position: 'bottom' },
          },
        },
      });
    } else if (fallback) {
      riskCtx.style.display = 'none';
      fallback.innerHTML = buildRiskFallback(labels, values);
    }
  }

  const volumeCtx = document.getElementById('volumeChart');
  if (volumeCtx) {
    const labels = window.QCT_DATA.volumeTrend.map((item) => item.label);
    const values = window.QCT_DATA.volumeTrend.map((item) => item.value);
    const fallback = document.getElementById('volumeFallback');
    if (typeof Chart !== 'undefined') {
      new Chart(volumeCtx, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'Average Volume (mm3)',
              data: values,
              borderColor: '#1f9d96',
              backgroundColor: 'rgba(31, 157, 150, 0.2)',
              tension: 0.35,
              fill: true,
            },
          ],
        },
        options: {
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
          },
          scales: {
            y: { beginAtZero: true },
          },
        },
      });
    } else if (fallback) {
      volumeCtx.style.display = 'none';
      fallback.innerHTML = buildTrendFallback(labels, values);
    }
  }
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initCharts);
} else {
  initCharts();
}
