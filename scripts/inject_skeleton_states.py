#!/usr/bin/env python3
"""Add enhanced skeleton loaders, error states, empty states to index.html"""
import os

FILE = os.path.join(os.path.dirname(__file__), "templates", "index.html")
content = open(FILE, "r", encoding="utf-8").read()

# ── 1. Enhanced CSS - add after existing skeleton CSS ──────────────────
EXTRA_CSS = """
/* ── ERROR STATE ─────────────────────────────────────────────── */
.error-state { display:flex; flex-direction:column; align-items:center; justify-content:center;
               padding:36px 20px; text-align:center; }
.error-state-icon { font-size:2.4rem; margin-bottom:14px; opacity:.7; }
.error-state-title { font-family:var(--title); font-size:.82rem; color:var(--red); letter-spacing:1px; margin-bottom:8px; }
.error-state-msg { font-size:.75rem; color:var(--muted); line-height:1.6; margin-bottom:18px; max-width:320px; }
.error-state-btn { padding:9px 22px; background:rgba(255,51,102,.1); border:1px solid rgba(255,51,102,.3);
                   color:var(--red); border-radius:999px; cursor:pointer; font-family:var(--font);
                   font-size:.75rem; transition:var(--transition); }
.error-state-btn:hover { background:rgba(255,51,102,.18); transform:translateY(-1px); }

/* ── EMPTY STATE ─────────────────────────────────────────────── */
.empty-state { display:flex; flex-direction:column; align-items:center; justify-content:center;
               padding:40px 20px; text-align:center; }
.empty-state-icon { font-size:2.6rem; margin-bottom:14px; opacity:.55; }
.empty-state-title { font-family:var(--title); font-size:.8rem; color:var(--muted); letter-spacing:1.2px; margin-bottom:8px; }
.empty-state-msg { font-size:.74rem; color:var(--muted); line-height:1.6; max-width:300px; opacity:.75; }

/* ── SKELETON KPI CARDS ──────────────────────────────────────── */
.stat-card.is-loading .val { visibility:hidden; }
.stat-card.is-loading::before { background:none; }
.stat-card.is-loading .sk-overlay { display:block !important; }
.sk-overlay { display:none; position:absolute; inset:18px; pointer-events:none; }
.sk-val { height:28px; width:70%; border-radius:6px; margin-bottom:10px; }
.sk-lbl { height:10px; width:50%; border-radius:4px; }

/* ── SKELETON NEWS ───────────────────────────────────────────── */
.news-skeleton-item { display:flex; flex-direction:column; gap:7px; padding:14px 16px;
                      border-bottom:1px solid rgba(26,48,80,.35); }
"""

old_css_anchor = ".count-up { animation:countUpPop .55s cubic-bezier(.34,1.56,.64,1) both; }\n"
new_css_anchor = old_css_anchor + EXTRA_CSS

if old_css_anchor in content:
    content = content.replace(old_css_anchor, new_css_anchor, 1)
    print("CSS OK")
else:
    print("CSS anchor not found")

# ── 2. JS utility functions ────────────────────────────────────────────
# Add after the animateCountUp function block
EXTRA_JS = """
// ── ERROR / EMPTY STATE HELPERS ───────────────────────────────
window.showErrorState = function(containerEl, msg, retryFn) {
  if (!containerEl) return;
  containerEl.innerHTML = '<div class="error-state">'
    + '<div class="error-state-icon">&#x26A0;</div>'
    + '<div class="error-state-title">ERREUR DE CHARGEMENT</div>'
    + '<div class="error-state-msg">' + (msg || 'Impossible de charger les données.') + '</div>'
    + (retryFn ? '<button class="error-state-btn" onclick="(' + retryFn.toString() + ')()">&#8635; Réessayer</button>' : '')
    + '</div>';
};

window.showEmptyState = function(containerEl, title, msg) {
  if (!containerEl) return;
  containerEl.innerHTML = '<div class="empty-state">'
    + '<div class="empty-state-icon">&#9674;</div>'
    + '<div class="empty-state-title">' + (title || 'AUCUN RÉSULTAT') + '</div>'
    + '<div class="empty-state-msg">' + (msg || 'Aucune donnée disponible pour le moment.') + '</div>'
    + '</div>';
};

window.showNewsSkeleton = function(count) {
  var el = document.getElementById('news-list-v7');
  if (!el) return;
  count = count || 6;
  var items = '';
  for (var i = 0; i < count; i++) {
    items += '<div class="news-skeleton-item">'
      + '<div class="skeleton skeleton-text w80"></div>'
      + '<div class="skeleton skeleton-text w60"></div>'
      + '<div class="skeleton skeleton-text w40" style="height:9px"></div>'
      + '</div>';
  }
  el.innerHTML = items;
};

window.showKpiSkeleton = function() {
  document.querySelectorAll('.stat-card').forEach(function(card) {
    card.classList.add('is-loading');
    if (!card.querySelector('.sk-overlay')) {
      var ov = document.createElement('div');
      ov.className = 'sk-overlay';
      ov.innerHTML = '<div class="skeleton sk-val"></div><div class="skeleton sk-lbl"></div>';
      card.appendChild(ov);
    }
  });
};

window.hideKpiSkeleton = function() {
  document.querySelectorAll('.stat-card.is-loading').forEach(function(card) {
    card.classList.remove('is-loading');
  });
};
"""

old_js_anchor = "window.animateCountUp = function(el, end, duration, prefix, suffix) {"
idx = content.find(old_js_anchor)
if idx >= 0:
    # Find end of the animateCountUp function (closing of the script block)
    close_script = content.find("</script>", idx)
    if close_script >= 0:
        content = content[:close_script] + "\n" + EXTRA_JS + "\n" + content[close_script:]
        print("JS OK")
    else:
        print("JS anchor script close not found")
else:
    print("JS anchor not found")

# ── 3. Show news skeleton before data loads ────────────────────────────
old_sk_init = "  var sb = document.getElementById('signals-body');\n  if (sb) sb.innerHTML = skRows;"
new_sk_init = old_sk_init + "\n  // News skeleton\n  if (typeof showNewsSkeleton === 'function') showNewsSkeleton(6);\n  if (typeof showKpiSkeleton === 'function') showKpiSkeleton();"

if old_sk_init in content:
    content = content.replace(old_sk_init, new_sk_init, 1)
    print("Skeleton init OK")
else:
    print("Skeleton init anchor not found")

# ── 4. Hide KPI skeleton when stats update ─────────────────────────────
old_hide_anchor = "  if (typeof _anim === 'undefined') {"
# Actually let's find the updateStats function and add hideKpiSkeleton call
old_update = "function updateStats() {"
idx2 = content.find(old_update)
if idx2 >= 0:
    # find the end of function body
    bracket_pos = content.find("{", idx2)
    content = content[:bracket_pos+1] + "\n  if (typeof hideKpiSkeleton === 'function') hideKpiSkeleton();" + content[bracket_pos+1:]
    print("hideKpiSkeleton OK")
else:
    print("updateStats not found")

# ── 5. Show empty state when news is empty ─────────────────────────────
old_no_news = "var _nl2=document.getElementById('news-list-v7'); if(_nl2) _nl2.innerHTML='<div style=\"color:var(--muted);padding:20px\">Aucune news disponible pour le moment.</div>';"
new_no_news = "var _nl2=document.getElementById('news-list-v7'); if(_nl2&&typeof showEmptyState==='function'){showEmptyState(_nl2,'AUCUNE NEWS','Aucune actualité disponible pour le moment. Réessaie plus tard.');}else if(_nl2){_nl2.innerHTML='<div style=\"color:var(--muted);padding:20px\">Aucune news disponible pour le moment.</div>';}"

if old_no_news in content:
    content = content.replace(old_no_news, new_no_news, 1)
    print("Empty news state OK")
else:
    print("Empty news anchor not found (checking shorter form...)")
    # Fallback: find by shorter key
    alt_key = "Aucune news disponible pour le moment."
    count = content.count(alt_key)
    print(f"Found '{alt_key}' {count} times")

open(FILE, "w", encoding="utf-8").write(content)
print("Done")
