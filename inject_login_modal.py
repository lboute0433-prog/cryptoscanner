#!/usr/bin/env python3
"""Inject login modal + onboarding wizard into index.html"""
import os

FILE = os.path.join(os.path.dirname(__file__), "templates", "index.html")
content = open(FILE, "r", encoding="utf-8").read()

LOGIN_MODAL_HTML = r"""
<!-- ── LOGIN / REGISTER MODAL ──────────────────────────────── -->
<div id="login-modal" style="display:none;position:fixed;inset:0;z-index:10000;background:rgba(0,0,0,.72);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);align-items:center;justify-content:center" onclick="if(event.target===this)closeLoginModal()">
  <div style="background:linear-gradient(160deg,rgba(13,24,40,.98),rgba(9,18,30,.99));border:1px solid rgba(62,231,255,.2);border-radius:24px;padding:36px 32px;width:min(440px,95vw);box-shadow:0 32px 80px rgba(0,0,0,.5),0 0 0 1px rgba(62,231,255,.08);position:relative;animation:tabFadeIn .28s ease">
    <button onclick="closeLoginModal()" style="position:absolute;top:14px;right:18px;background:none;border:none;color:var(--muted);font-size:1.3rem;cursor:pointer;line-height:1;padding:4px 8px">&#x00D7;</button>
    <div style="text-align:center;margin-bottom:24px">
      <div style="font-family:var(--title);font-size:1.1rem;color:var(--accent);letter-spacing:3px;margin-bottom:6px">&#9674; CRYPTOSCANNER PRO</div>
      <div style="font-size:.78rem;color:var(--muted)">Plateforme d&apos;analyse crypto tout-en-un</div>
    </div>
    <!-- Tabs -->
    <div style="display:flex;background:rgba(8,16,28,.6);border-radius:12px;padding:3px;margin-bottom:22px;gap:3px">
      <button id="lm-tab-login" onclick="lmSwitch('login')" style="flex:1;padding:9px;border:none;border-radius:9px;background:linear-gradient(135deg,var(--accent),#72f1ff);color:#04101c;font-family:var(--title);font-size:.68rem;font-weight:700;cursor:pointer;letter-spacing:.8px;transition:.2s">SE CONNECTER</button>
      <button id="lm-tab-register" onclick="lmSwitch('register')" style="flex:1;padding:9px;border:none;border-radius:9px;background:transparent;color:var(--muted);font-family:var(--title);font-size:.68rem;font-weight:700;cursor:pointer;letter-spacing:.8px;transition:.2s">CR&Eacute;ER UN COMPTE</button>
    </div>
    <!-- Login panel -->
    <div id="lm-panel-login">
      <div style="margin-bottom:14px">
        <label style="display:block;font-size:.65rem;color:var(--muted);letter-spacing:1px;margin-bottom:6px">NOM D&apos;UTILISATEUR</label>
        <input id="lm-username" class="form-input" style="width:100%" placeholder="ton_username" autocomplete="username" onkeydown="if(event.key==='Enter')doLmLogin()">
      </div>
      <div style="margin-bottom:8px">
        <label style="display:block;font-size:.65rem;color:var(--muted);letter-spacing:1px;margin-bottom:6px">MOT DE PASSE</label>
        <div style="position:relative">
          <input id="lm-password" class="form-input" style="width:100%;padding-right:38px" type="password" placeholder="&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;" autocomplete="current-password" onkeydown="if(event.key==='Enter')doLmLogin()">
          <button onclick="var i=document.getElementById('lm-password');i.type=i.type==='password'?'text':'password'" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--muted);font-size:.9rem">&#128065;</button>
        </div>
      </div>
      <div id="lm-panel-2fa" style="display:none;margin-bottom:14px;padding:14px;background:rgba(62,231,255,.06);border:1px solid rgba(62,231,255,.15);border-radius:12px">
        <div style="font-size:.68rem;color:var(--accent);margin-bottom:8px;letter-spacing:1px">&#128272; CODE 2FA REQUIS</div>
        <input id="lm-2fa-code" class="form-input" style="width:100%;text-align:center;font-size:1.1rem;letter-spacing:8px" type="text" placeholder="000000" maxlength="6" autocomplete="one-time-code">
      </div>
      <div id="lm-login-error" style="color:var(--red);font-size:.7rem;margin-bottom:10px;min-height:14px"></div>
      <button onclick="doLmLogin()" class="btn btn-primary" style="width:100%;padding:12px;font-size:.82rem">&rarr; SE CONNECTER</button>
      <div style="text-align:center;margin-top:12px">
        <a href="#" onclick="lmSwitch('forgot');return false" style="color:var(--muted);font-size:.68rem;text-decoration:none;border-bottom:1px solid rgba(122,145,179,.3)">Mot de passe oubli&eacute; ?</a>
      </div>
    </div>
    <!-- Forgot panel -->
    <div id="lm-panel-forgot" style="display:none">
      <p style="font-size:.75rem;color:var(--muted);margin-bottom:16px;line-height:1.6">Entrez votre email pour recevoir un lien de r&eacute;initialisation valable 1 heure.</p>
      <div style="margin-bottom:14px">
        <label style="display:block;font-size:.65rem;color:var(--muted);letter-spacing:1px;margin-bottom:6px">EMAIL</label>
        <input id="lm-forgot-email" class="form-input" style="width:100%" type="email" placeholder="jean@gmail.com">
      </div>
      <div id="lm-forgot-msg" style="font-size:.7rem;margin-bottom:10px;min-height:14px"></div>
      <button onclick="doLmForgot()" class="btn btn-primary" style="width:100%;padding:12px">&rarr; ENVOYER LE LIEN</button>
      <div style="text-align:center;margin-top:12px">
        <a href="#" onclick="lmSwitch('login');return false" style="color:var(--muted);font-size:.68rem;text-decoration:none">&larr; Retour &agrave; la connexion</a>
      </div>
    </div>
    <!-- Register panel -->
    <div id="lm-panel-register" style="display:none">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px">
        <div>
          <label style="display:block;font-size:.65rem;color:var(--muted);letter-spacing:1px;margin-bottom:6px">PR&Eacute;NOM</label>
          <input id="lm-reg-firstname" class="form-input" style="width:100%" placeholder="Jean">
        </div>
        <div>
          <label style="display:block;font-size:.65rem;color:var(--muted);letter-spacing:1px;margin-bottom:6px">NOM</label>
          <input id="lm-reg-lastname" class="form-input" style="width:100%" placeholder="Dupont">
        </div>
      </div>
      <div style="margin-bottom:12px">
        <label style="display:block;font-size:.65rem;color:var(--muted);letter-spacing:1px;margin-bottom:6px">EMAIL <span style="color:var(--red)">*</span></label>
        <input id="lm-reg-email" class="form-input" style="width:100%" type="email" placeholder="jean@gmail.com" required>
      </div>
      <div style="margin-bottom:12px">
        <label style="display:block;font-size:.65rem;color:var(--muted);letter-spacing:1px;margin-bottom:6px">NOM D&apos;UTILISATEUR <span style="color:var(--red)">*</span></label>
        <input id="lm-reg-username" class="form-input" style="width:100%" placeholder="jean_crypto" required>
      </div>
      <div style="margin-bottom:8px">
        <label style="display:block;font-size:.65rem;color:var(--muted);letter-spacing:1px;margin-bottom:6px">MOT DE PASSE <span style="color:var(--red)">*</span></label>
        <div style="position:relative">
          <input id="lm-reg-password" class="form-input" style="width:100%;padding-right:38px" type="password" placeholder="Min. 8 caract&egrave;res" required>
          <button onclick="var i=document.getElementById('lm-reg-password');i.type=i.type==='password'?'text':'password'" style="position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;color:var(--muted);font-size:.9rem">&#128065;</button>
        </div>
      </div>
      <div id="lm-reg-error" style="color:var(--red);font-size:.7rem;margin-bottom:10px;min-height:14px"></div>
      <button onclick="doLmRegister()" class="btn btn-primary" style="width:100%;padding:12px;font-size:.82rem">&#x2736; CR&Eacute;ER MON COMPTE</button>
      <div style="text-align:center;margin-top:10px;font-size:.65rem;color:var(--muted)">Inscription gratuite &middot; Aucune carte requise</div>
    </div>
  </div>
</div>

<!-- ── ONBOARDING WIZARD ────────────────────────────────────── -->
<div id="onboarding-modal" style="display:none;position:fixed;inset:0;z-index:10001;background:rgba(0,0,0,.82);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);align-items:center;justify-content:center">
  <div style="background:linear-gradient(160deg,rgba(12,22,38,.99),rgba(8,16,28,.99));border:1px solid rgba(62,231,255,.22);border-radius:24px;padding:36px 32px;width:min(500px,95vw);box-shadow:0 40px 100px rgba(0,0,0,.6);position:relative;animation:tabFadeIn .3s ease">
    <div id="ob-progress" style="display:flex;gap:6px;margin-bottom:28px"></div>
    <div id="ob-content"></div>
    <div style="display:flex;gap:10px;margin-top:24px">
      <button id="ob-skip" onclick="obSkip()" style="flex:1;padding:11px;background:transparent;border:1px solid rgba(122,145,179,.2);border-radius:999px;color:var(--muted);font-family:var(--font);font-size:.78rem;cursor:pointer">Ignorer</button>
      <button id="ob-next" onclick="obNext()" class="btn btn-primary" style="flex:2;padding:11px">Suivant &rarr;</button>
    </div>
  </div>
</div>
"""

LOGIN_MODAL_JS = """
<script>
// ── LOGIN MODAL ───────────────────────────────────────────────
function showLoginModal() {
  var m = document.getElementById('login-modal');
  if (m) { m.style.display = 'flex'; lmSwitch('login'); }
}
function closeLoginModal() {
  var m = document.getElementById('login-modal');
  if (m) m.style.display = 'none';
}
function lmSwitch(tab) {
  ['login','register','forgot'].forEach(function(t) {
    var p = document.getElementById('lm-panel-' + t);
    if (p) p.style.display = t === tab ? '' : 'none';
  });
  var btnL = document.getElementById('lm-tab-login');
  var btnR = document.getElementById('lm-tab-register');
  var activeStyle = 'linear-gradient(135deg,var(--accent),#72f1ff)';
  var inactiveStyle = 'transparent';
  if (btnL) { btnL.style.background = tab === 'register' ? inactiveStyle : activeStyle; btnL.style.color = tab === 'register' ? 'var(--muted)' : '#04101c'; }
  if (btnR) { btnR.style.background = tab === 'register' ? activeStyle : inactiveStyle; btnR.style.color = tab === 'register' ? '#04101c' : 'var(--muted)'; }
}

async function doLmLogin() {
  var errEl = document.getElementById('lm-login-error');
  var btn = document.querySelector('#lm-panel-login .btn-primary');
  var u = (document.getElementById('lm-username') || {}).value || '';
  var p = (document.getElementById('lm-password') || {}).value || '';
  var code2fa = (document.getElementById('lm-2fa-code') || {}).value || '';
  if (!u || !p) { if (errEl) errEl.textContent = 'Nom d\\'utilisateur et mot de passe requis'; return; }
  if (errEl) errEl.textContent = '';
  if (btn) { btn.disabled = true; btn.textContent = 'Connexion...'; }
  try {
    var body = { username: u, password: p };
    if (code2fa) body.totp_code = code2fa;
    var r = await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    var d = await r.json();
    if (d.totp_required) {
      document.getElementById('lm-panel-2fa').style.display = '';
      if (errEl) errEl.textContent = '';
      if (btn) { btn.disabled = false; btn.textContent = '\\u2192 SE CONNECTER'; }
      return;
    }
    if (d.ok && d.token) {
      localStorage.setItem('auth_token', d.token);
      window.currentUser = window.currentUser || {};
      Object.assign(window.currentUser, { username: d.username, role: d.role, user_id: d.user_id, subscription_status: d.subscription_status || 'inactive' });
      if (typeof cfgUpdateProfile === 'function') cfgUpdateProfile(window.currentUser);
      if (typeof showLoggedIn === 'function') showLoggedIn(window.currentUser.username);
      closeLoginModal();
      if (typeof showToast === 'function') showToast('Bienvenue ' + (d.username || '') + ' !', 'success', 'CONNEXION R\\u00c9USSIE');
      setTimeout(function() { if (typeof showTab === 'function') showTab('dashboard'); }, 600);
    } else {
      if (errEl) errEl.textContent = '\\u274c ' + (d.error || 'Identifiants incorrects');
    }
  } catch(e) {
    if (errEl) errEl.textContent = '\\u274c Erreur r\\u00e9seau: ' + e.message;
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '\\u2192 SE CONNECTER'; }
  }
}

async function doLmForgot() {
  var em = (document.getElementById('lm-forgot-email') || {}).value || '';
  var msgEl = document.getElementById('lm-forgot-msg');
  if (!em || !em.includes('@')) { if (msgEl) { msgEl.textContent = 'Email invalide'; msgEl.style.color = 'var(--red)'; } return; }
  try {
    var r = await fetch('/api/auth/forgot-password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email: em }) });
    var d = await r.json();
    if (msgEl) { msgEl.textContent = d.message || 'Email envoy\\u00e9 si le compte existe'; msgEl.style.color = 'var(--green)'; }
  } catch(e) { if (msgEl) { msgEl.textContent = 'Erreur r\\u00e9seau'; msgEl.style.color = 'var(--red)'; } }
}

async function doLmRegister() {
  var errEl = document.getElementById('lm-reg-error');
  var btn = document.querySelector('#lm-panel-register .btn-primary');
  var fn = (document.getElementById('lm-reg-firstname') || {}).value || '';
  var ln = (document.getElementById('lm-reg-lastname') || {}).value || '';
  var em = (document.getElementById('lm-reg-email') || {}).value || '';
  var us = (document.getElementById('lm-reg-username') || {}).value || '';
  var pw = (document.getElementById('lm-reg-password') || {}).value || '';
  if (!em || !us || !pw) { if (errEl) errEl.textContent = 'Champs obligatoires manquants'; return; }
  if (pw.length < 8) { if (errEl) errEl.textContent = 'Mot de passe trop court (min. 8 caract\\u00e8res)'; return; }
  if (errEl) errEl.textContent = '';
  if (btn) { btn.disabled = true; btn.textContent = 'Cr\\u00e9ation...'; }
  try {
    var r = await fetch('/api/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ firstname: fn, lastname: ln, email: em, username: us, password: pw }) });
    var d = await r.json();
    if (d.ok && d.token) {
      localStorage.setItem('auth_token', d.token);
      window.currentUser = window.currentUser || {};
      Object.assign(window.currentUser, { username: d.username, role: d.role || 'visitor', user_id: d.user_id, subscription_status: 'inactive' });
      if (typeof cfgUpdateProfile === 'function') cfgUpdateProfile(window.currentUser);
      if (typeof showLoggedIn === 'function') showLoggedIn(window.currentUser.username);
      closeLoginModal();
      startOnboarding(d.username || us);
    } else {
      if (errEl) errEl.textContent = '\\u274c ' + (d.error || 'Erreur lors de la cr\\u00e9ation');
    }
  } catch(e) {
    if (errEl) errEl.textContent = '\\u274c Erreur r\\u00e9seau: ' + e.message;
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '\\u2736 CR\\u00c9ER MON COMPTE'; }
  }
}

// ── ONBOARDING WIZARD ─────────────────────────────────────────
var _obStep = 1;
var _obUsername = '';
var _obSteps = [
  { title: 'Bienvenue !', content: function(u) {
    return '<div style="text-align:center;padding:8px 0">'
      + '<div style="font-size:2.8rem;margin-bottom:16px">&#9674;</div>'
      + '<div style="font-family:var(--title);font-size:1.1rem;color:var(--accent);letter-spacing:2px;margin-bottom:10px">BIENVENUE ' + (u||'').toUpperCase() + ' !</div>'
      + '<p style="font-size:.82rem;color:var(--muted);line-height:1.8">CryptoScanner Pro est ta plateforme d\\'analyse crypto tout-en-un. Ce guide rapide te prendra moins de 2 minutes.</p>'
      + '<div style="display:flex;flex-direction:column;gap:8px;margin-top:20px;text-align:left">'
      + '<div style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:rgba(62,231,255,.06);border:1px solid rgba(62,231,255,.1);border-radius:10px"><span>&#128202;</span><span style="font-size:.78rem">Scanner de march\\u00e9 en temps r\\u00e9el</span></div>'
      + '<div style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:rgba(62,231,255,.06);border:1px solid rgba(62,231,255,.1);border-radius:10px"><span>&#9889;</span><span style="font-size:.78rem">Signaux automatiques &amp; alertes</span></div>'
      + '<div style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:rgba(62,231,255,.06);border:1px solid rgba(62,231,255,.1);border-radius:10px"><span>&#129504;</span><span style="font-size:.78rem">IA int\\u00e9gr\\u00e9e pour l\\'analyse</span></div>'
      + '</div></div>';
  }},
  { title: 'Configuration IA', content: function() {
    return '<div>'
      + '<div style="font-family:var(--title);font-size:.85rem;color:var(--accent);letter-spacing:1.5px;margin-bottom:12px">CONFIGURER TON IA (OPTIONNEL)</div>'
      + '<p style="font-size:.78rem;color:var(--muted);line-height:1.7;margin-bottom:16px">Pour utiliser l\\'assistant IA, ajoute ta cl\\u00e9 API Claude ou OpenAI. Tu peux le faire plus tard dans Param\\u00e8tres.</p>'
      + '<div style="margin-bottom:10px"><label style="display:block;font-size:.63rem;color:var(--muted);letter-spacing:1px;margin-bottom:6px">CL\\u00c9 CLAUDE (ANTHROPIC)</label>'
      + '<input id="ob-claude-key" class="form-input" style="width:100%;font-size:.72rem" placeholder="sk-ant-..." type="password"></div>'
      + '<div><label style="display:block;font-size:.63rem;color:var(--muted);letter-spacing:1px;margin-bottom:6px">CL\\u00c9 OPENAI (optionnel)</label>'
      + '<input id="ob-openai-key" class="form-input" style="width:100%;font-size:.72rem" placeholder="sk-..." type="password"></div>'
      + '</div>';
  }},
  { title: 'S\\u00e9curit\\u00e9 2FA', content: function() {
    return '<div>'
      + '<div style="font-family:var(--title);font-size:.85rem;color:var(--accent);letter-spacing:1.5px;margin-bottom:12px">AUTHENTIFICATION 2 FACTEURS</div>'
      + '<p style="font-size:.78rem;color:var(--muted);line-height:1.7;margin-bottom:16px">Active la 2FA pour s\\u00e9curiser ton compte avec une app comme Google Authenticator.</p>'
      + '<div style="padding:20px;background:rgba(255,193,7,.06);border:1px solid rgba(255,193,7,.15);border-radius:14px;text-align:center">'
      + '<div style="font-size:2rem;margin-bottom:8px">&#128737;</div>'
      + '<div style="font-size:.78rem;color:var(--yellow);margin-bottom:14px">Recommand\\u00e9 pour prot\\u00e9ger ton compte</div>'
      + '<button onclick="obSkip();showTab(\\'settings\\');" style="padding:9px 20px;background:rgba(255,193,7,.15);border:1px solid rgba(255,193,7,.3);border-radius:999px;color:var(--yellow);font-family:var(--font);font-size:.75rem;cursor:pointer">&#9881; Configurer maintenant</button>'
      + '</div></div>';
  }},
  { title: "C'est parti !", content: function() {
    return '<div style="text-align:center;padding:8px 0">'
      + '<div style="font-size:3rem;margin-bottom:16px">&#128640;</div>'
      + '<div style="font-family:var(--title);font-size:1rem;color:var(--green);letter-spacing:2px;margin-bottom:12px">TOUT EST PR\\u00caT !</div>'
      + '<p style="font-size:.82rem;color:var(--muted);line-height:1.8;margin-bottom:20px">Ton compte est configur\\u00e9. Explore le dashboard pour d\\u00e9couvrir toutes les fonctionnalit\\u00e9s.</p>'
      + '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;text-align:left">'
      + '<div style="padding:10px;background:rgba(0,255,136,.06);border:1px solid rgba(0,255,136,.12);border-radius:10px;font-size:.72rem"><span style="color:var(--green)">&#10003;</span> Compte cr\\u00e9\\u00e9</div>'
      + '<div style="padding:10px;background:rgba(62,231,255,.06);border:1px solid rgba(62,231,255,.1);border-radius:10px;font-size:.72rem"><span style="color:var(--accent)">&#8594;</span> Dashboard actif</div>'
      + '<div style="padding:10px;background:rgba(106,163,255,.06);border:1px solid rgba(106,163,255,.1);border-radius:10px;font-size:.72rem"><span style="color:var(--accent2)">&#9674;</span> Signaux temps r\\u00e9el</div>'
      + '<div style="padding:10px;background:rgba(255,193,7,.06);border:1px solid rgba(255,193,7,.1);border-radius:10px;font-size:.72rem"><span style="color:var(--yellow)">&#9733;</span> Scanner actif</div>'
      + '</div></div>';
  }}
];

function startOnboarding(username) {
  _obStep = 1;
  _obUsername = username || '';
  var m = document.getElementById('onboarding-modal');
  if (m) { m.style.display = 'flex'; obRender(); }
  if (typeof showToast === 'function') showToast('Bienvenue ' + (_obUsername || '') + ' !', 'success', 'INSCRIPTION R\\u00c9USSIE', 5000);
}

function obRender() {
  var step = _obSteps[_obStep - 1];
  if (!step) { obFinish(); return; }
  var content = document.getElementById('ob-content');
  if (content) content.innerHTML = '<div style="font-family:var(--title);font-size:.72rem;color:var(--muted);letter-spacing:1px;margin-bottom:14px">\\u00c9TAPE ' + _obStep + ' / ' + _obSteps.length + ' \\u2014 ' + step.title + '</div>' + step.content(_obUsername);
  var prog = document.getElementById('ob-progress');
  if (prog) {
    prog.innerHTML = '';
    for (var i = 1; i <= _obSteps.length; i++) {
      var d = document.createElement('div');
      d.style.cssText = 'flex:1;height:3px;border-radius:2px;transition:.3s ease;background:' + (i <= _obStep ? 'var(--accent)' : 'rgba(122,145,179,.2)');
      prog.appendChild(d);
    }
  }
  var nextBtn = document.getElementById('ob-next');
  if (nextBtn) nextBtn.textContent = _obStep === _obSteps.length ? '\\u1f680 Accéder au Dashboard' : 'Suivant \\u2192';
  var skipBtn = document.getElementById('ob-skip');
  if (skipBtn) skipBtn.style.display = _obStep === _obSteps.length ? 'none' : '';
}

function obNext() {
  if (_obStep === 2) {
    var ck = (document.getElementById('ob-claude-key') || {}).value || '';
    var ok = (document.getElementById('ob-openai-key') || {}).value || '';
    if (ck) { var ci = document.getElementById('cfg-claude-key'); if (ci) ci.value = ck; }
    if (ok) { var oi = document.getElementById('cfg-openai-key'); if (oi) oi.value = ok; }
  }
  if (_obStep >= _obSteps.length) { obFinish(); return; }
  _obStep++;
  obRender();
}

function obSkip() { obFinish(); }
function obFinish() {
  var m = document.getElementById('onboarding-modal');
  if (m) m.style.display = 'none';
  if (typeof showTab === 'function') showTab('dashboard');
}

// Polish header login button
(function() {
  var btn = document.getElementById('btn-login-header');
  if (btn) {
    btn.className = 'btn btn-primary';
    btn.style.cssText = 'padding:7px 18px;font-size:.7rem;letter-spacing:.8px;border-radius:999px';
    btn.textContent = '\\u2192 SE CONNECTER';
    btn.onclick = showLoginModal;
  }
})();
</script>
"""

# Insert before </body>
insert_before = "\n</body>\n</html>"
if insert_before in content:
    content = content.replace(insert_before, "\n" + LOGIN_MODAL_HTML + "\n" + LOGIN_MODAL_JS + insert_before, 1)
    open(FILE, "w", encoding="utf-8").write(content)
    print("OK - login modal injected")
else:
    print("ERROR: </body> not found at expected location")
    idx = content.rfind("</body>")
    print(f"Found </body> at position {idx}")
