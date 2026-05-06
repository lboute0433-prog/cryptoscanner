// ════════════════════════════════════════════════════════════
// TICKER.JS — Fetch live crypto prices and populate the ticker
// ════════════════════════════════════════════════════════════

function populateTicker() {
  fetch('/api/ticker')
    .then(r => {
      if (!r.ok) throw new Error('API error: ' + r.status);
      return r.json();
    })
    .then(data => {
      const track = document.querySelector('.ticker-track');
      if (!track) {
        console.warn('Ticker: .ticker-track element not found');
        return;
      }

      // API returns {items: [...]}
      const items = data.items || [];

      if (!Array.isArray(items) || items.length === 0) {
        console.warn('Ticker: No data items received from API', data);
        return;
      }

      // Create HTML items from API data
      const html = items.map(item => {
        const sym = item.sym || 'N/A';
        const price = item.price || '—';
        const changeStr = item.change_str || '';
        const trend = (item.trend === 'up' || item.trend === 'Up') ? 'up' : (item.trend === 'down' ? 'dn' : 'neutral');
        const trendClass = trend === 'up' ? 'up' : trend === 'dn' ? 'dn' : '';

        return `<span class="t-item"><span class="sym">${sym}</span><span class="${trendClass}">${price} ${changeStr}</span></span>`;
      }).join('');

      // Duplicate items for seamless infinite scroll
      track.innerHTML = html + html;

      console.log('Ticker populated with', items.length, 'items');
    })
    .catch(err => {
      console.error('Ticker error:', err);
    });
}

// Load on page ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('Ticker.js loaded');
  populateTicker();
  // Refresh every 30 seconds
  setInterval(populateTicker, 30000);
});
