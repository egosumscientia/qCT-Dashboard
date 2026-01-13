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

const updateMetaIndicators = (uiState = {}) => {
  const metaRefresh = document.getElementById('metaRefresh');
  const metaFilters = document.getElementById('metaFilters');
  const metaDateRange = document.getElementById('metaDateRange');
  if (metaRefresh) {
    metaRefresh.textContent = new Date().toLocaleString();
  }
  const params = new URLSearchParams(window.location.search);
  const filterKeys = ['status', 'risk', 'q', 'start_date', 'end_date'];
  let activeFilters = 0;
  filterKeys.forEach((key) => {
    const value = params.get(key);
    if (value) {
      activeFilters += 1;
    }
  });
  if (uiState.quickLast30) {
    activeFilters += 1;
  }
  if (metaFilters) {
    metaFilters.textContent = String(activeFilters);
  }
  if (metaDateRange) {
    const start = params.get('start_date');
    const end = params.get('end_date');
    if (start || end) {
      metaDateRange.textContent = `${start || '...'} to ${end || '...'}`;
    } else if (uiState.quickLast30) {
      metaDateRange.textContent = 'Last 30 days (page)';
    } else {
      metaDateRange.textContent = 'All time';
    }
  }
};

const updateBanner = () => {
  const banner = document.querySelector('.banner');
  if (!banner) {
    return;
  }
  const isEnabled = banner.dataset.bannerEnabled !== 'false';
  if (!isEnabled) {
    banner.classList.add('is-hidden');
    return;
  }
  const text = banner.dataset.bannerText;
  if (text) {
    banner.textContent = text;
  }
};

const updateQualitySummary = () => {
  const table = document.querySelector('table.table');
  if (!table) {
    return;
  }
  const rows = Array.from(table.querySelectorAll('tbody tr[data-study-date]')).filter(
    (row) => row.style.display !== 'none'
  );
  const total = rows.length;
  const countImage = rows.filter((row) => row.dataset.hasImage === 'true').length;
  const countSummary = rows.filter((row) => row.dataset.hasSummary === 'true').length;
  const format = (count) => {
    if (!total) {
      return '--';
    }
    const percent = Math.round((count / total) * 100);
    return `${percent}% (${count}/${total})`;
  };
  const imageEl = document.getElementById('qualityImage');
  const summaryEl = document.getElementById('qualitySummary');
  if (imageEl) {
    imageEl.textContent = format(countImage);
  }
  if (summaryEl) {
    summaryEl.textContent = format(countSummary);
  }
};

const initStudyQuickFilters = () => {
  const last30Button = document.querySelector('[data-quick-filter="last30"]');
  if (!last30Button) {
    return;
  }
  const clientEmptyState = document.getElementById('clientEmptyState');
  const clearQuickFilter = document.querySelector('[data-clear-quick-filter]');
  const uiState = {
    quickLast30: false,
  };

  const parseDate = (value) => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
  };

  const applyLast30Filter = () => {
    const table = document.querySelector('table.table');
    if (!table) {
      return;
    }
    // Client-side preset: filters only the currently loaded page.
    const rows = Array.from(table.querySelectorAll('tbody tr[data-study-date]'));
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - 30);
    let visibleCount = 0;
    rows.forEach((row) => {
      const dateValue = parseDate(row.dataset.studyDate);
      const isVisible = !uiState.quickLast30 || !dateValue || dateValue >= cutoff;
      row.style.display = isVisible ? '' : 'none';
      if (isVisible) {
        visibleCount += 1;
      }
    });
    if (clientEmptyState) {
      clientEmptyState.classList.toggle(
        'is-hidden',
        !uiState.quickLast30 || visibleCount > 0
      );
    }
    updateQualitySummary();
    updateMetaIndicators(uiState);
  };

  last30Button.addEventListener('click', () => {
    uiState.quickLast30 = !uiState.quickLast30;
    last30Button.classList.toggle('active', uiState.quickLast30);
    applyLast30Filter();
  });

  if (clearQuickFilter) {
    clearQuickFilter.addEventListener('click', () => {
      uiState.quickLast30 = false;
      last30Button.classList.remove('active');
      applyLast30Filter();
    });
  }

  applyLast30Filter();
};

const initCsvExport = () => {
  const exportButton = document.querySelector('[data-export="studies"]');
  if (!exportButton) {
    return;
  }
  exportButton.addEventListener('click', () => {
    const table = document.querySelector('table.table');
    if (!table) {
      return;
    }
    const headers = Array.from(table.querySelectorAll('thead th')).map((th) =>
      th.textContent.trim()
    );
    const rows = Array.from(table.querySelectorAll('tbody tr'))
      .filter((row) => row.style.display !== 'none')
      .map((row) =>
        Array.from(row.querySelectorAll('td')).map((cell) =>
          cell.textContent.trim().replace(/\s+/g, ' ')
        )
      );
    const escapeCell = (value) => `"${value.replace(/"/g, '""')}"`;
    const csv = [headers, ...rows].map((row) => row.map(escapeCell).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const timestamp = new Date().toISOString().slice(0, 10);
    link.href = url;
    link.download = `studies_export_${timestamp}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  });
};

const initUiEnhancements = () => {
  updateBanner();
  updateMetaIndicators();
  updateQualitySummary();
  initStudyQuickFilters();
  initCsvExport();
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    initUiEnhancements();
  });
} else {
  initCharts();
  initUiEnhancements();
}
