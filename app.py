import streamlit as st
import streamlit.components.v1 as components
import json, time, random
from collections import Counter
from firebase_helper import verify_token, load_bookmarks, save_bookmarks

# ── KONFIGURASI ──────────────────────────────────────────────────
st.set_page_config(page_title="CAT MHI", page_icon="🎓", layout="centered")

# ── LOAD DATA ────────────────────────────────────────────────────
@st.cache_data
def load_data():
    with open("soal_pg.json","r",encoding="utf-8") as f: pg=json.load(f)
    with open("soal_essay.json","r",encoding="utf-8") as f: es=json.load(f)
    return pg, es

try:
    soal_pg, soal_essay = load_data()
except FileNotFoundError:
    st.error("Gagal memuat database soal."); st.stop()

SEMUA_KATEGORI  = sorted(set(q.get("kategori","Umum") for q in soal_pg))
JUMLAH_OPSI_SIM = [50, 75, 100]
DURASI_OPSI     = {"60 menit":3600,"90 menit":5400,"120 menit":7200}
PASSING_OPSI    = [70, 75, 80, 85]

# ── CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"]>div:first-child{display:flex;flex-direction:column;align-items:center;text-align:center;padding-top:1.5rem}
[data-testid="stSidebar"] .stMetric,[data-testid="stSidebar"] .stMetric label,[data-testid="stSidebar"] .stMetric>div{text-align:center!important;justify-content:center!important}
[data-testid="stSidebar"] *{font-size:0.96rem}
[data-testid="stSidebar"] .stMetric label{font-size:0.8rem!important}
[data-testid="stSidebar"] [data-testid="stMetricValue"]{font-size:1.45rem!important}
[data-testid="stTabs"] button p{font-size:clamp(0.85rem,2.5vw,1.02rem)!important;font-weight:500!important;white-space:nowrap}
[data-testid="stTabs"] button[aria-selected="true"] p{font-weight:700!important}
.stButton>button{font-size:0.97rem!important;font-weight:500!important;padding:0.5rem 1.1rem!important;border-radius:9px!important;min-height:2.5rem!important}
.stButton>button[kind="primary"]{font-size:1rem!important;font-weight:600!important}
.stSelectbox label,.stTextArea label{font-size:0.97rem!important}
.stRadio [data-testid="stMarkdownContainer"] p{font-size:0.97rem!important}
p,li,.stMarkdown p{font-size:0.97rem;line-height:1.65}
.prog-wrap{background:rgba(128,128,128,.2);border-radius:99px;height:7px;margin:.3rem 0 .7rem;overflow:hidden}
.prog-bar{height:7px;border-radius:99px;background:linear-gradient(90deg,#3b82f6,#7c3aed);transition:width .45s cubic-bezier(.4,0,.2,1)}
.q-card{border:1px solid rgba(128,128,128,.25);border-radius:14px;padding:1.15rem 1.4rem;margin-bottom:1rem;box-shadow:0 2px 14px rgba(0,0,0,.07);font-size:1rem;line-height:1.65;font-weight:500}
.metric-row{display:flex;gap:.6rem;flex-wrap:wrap;justify-content:center;margin:.75rem 0}
.metric-box{border:1px solid rgba(128,128,128,.25);border-radius:12px;padding:.75rem 1rem;text-align:center;flex:1 1 80px;min-width:75px;box-shadow:0 1px 5px rgba(0,0,0,.05)}
.metric-box .mval{font-size:clamp(1.25rem,4vw,1.6rem);font-weight:700;color:#3b82f6;line-height:1.1}
.metric-box .mlbl{font-size:.75rem;opacity:.65;margin-top:.2rem}
.tag{display:inline-flex;align-items:center;gap:4px;background:rgba(59,130,246,.12);color:#3b82f6;border-radius:99px;font-size:.75rem;font-weight:600;padding:.15rem .65rem;margin-bottom:.5rem}
.opsi-item{display:block;padding:.62rem .95rem;border-radius:9px;margin-bottom:.32rem;border:1.5px solid rgba(128,128,128,.25);font-size:.97rem}
.opsi-benar{border-color:#16a34a!important;background:rgba(22,163,74,.1)!important;color:#15803d!important;font-weight:600}
.opsi-salah{border-color:#dc2626!important;background:rgba(220,38,38,.08)!important;color:#b91c1c!important;font-weight:600}
.donut-wrap{display:flex;justify-content:center;margin:.8rem 0}
.skor-item{display:flex;align-items:center;gap:.5rem;padding:.4rem .65rem;border-radius:8px;border:1px solid rgba(128,128,128,.2);margin-bottom:.35rem;font-size:.9rem}
.skor-badge{font-weight:700;font-size:.95rem;min-width:50px;text-align:right}
</style>
""", unsafe_allow_html=True)

# ── STATE ────────────────────────────────────────────────────────
def init_state():
    d={
        "current_q":0,"user":None,"bookmarks":set(),
        "simulasi_started":False,"simulasi_answers":{},"simulasi_submitted":False,
        "simulasi_start_time":None,"simulasi_questions":[],"simulasi_review_idx":0,
        "simulasi_show_review":False,"simulasi_jumlah":100,"simulasi_durasi_label":"120 menit",
        "simulasi_kategori":"Semua Kategori","simulasi_passing":70,"simulasi_histori":[],
        "sim_confirm_kumpul":False,"_hist_saved":False,
        "latihan_pg_questions":[],"latihan_pg_answers":{},"latihan_pg_checked":{},
        "latihan_pg_salah_mode":False,"latihan_pg_salah_list":[],
        "latihan_essay_questions":[],"latihan_essay_shown":{},
    }
    for k,v in d.items():
        if k not in st.session_state: st.session_state[k]=v

init_state()

# ── FIREBASE AUTH ────────────────────────────────────────────────
def get_web_cfg():
    """Return Firebase web config. secrets.toml keys must be camelCase."""
    try:
        return dict(st.secrets["firebase_web"])
    except:
        return {}

def handle_callback():
    p=st.query_params
    if "fb_token" not in p: return
    decoded=verify_token(p["fb_token"])
    if decoded:
        uid=p.get("fb_uid",decoded.get("uid",""))
        st.session_state.user={"uid":uid,"email":p.get("fb_email",""),
                               "name":p.get("fb_name","Pengguna"),"photo":p.get("fb_photo","")}
        st.session_state.bookmarks=load_bookmarks(uid)
    st.query_params.clear(); st.rerun()

handle_callback()

def login_page():
    cfg = get_web_cfg()
    if not cfg:
        st.error("Firebase belum dikonfigurasi. Isi .streamlit/secrets.toml")
        st.stop()

    # Validate camelCase keys required by Firebase JS SDK
    required = ["apiKey", "authDomain", "projectId"]
    missing  = [k for k in required if k not in cfg]
    if missing:
        st.error(f"secrets.toml [firebase_web] harus pakai camelCase. Key yang belum ada: {missing}")
        st.stop()

    cfg_json = json.dumps(cfg)

    login_html = """
<script>
// ── Init Constants ─────────────────────────────────────────────
var firebaseConfig = CFG_JSON;

function setStatus(msg) {
  document.getElementById('status').textContent = msg;
}

function showError(msg) {
  var el = document.getElementById('err');
  el.textContent = msg;
  el.className = 'show';
  var btn = document.getElementById('btn');
  btn.disabled = false;
  btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg> Masuk dengan Google';
  setStatus('');
}

function navigateParent(params) {
  var qs = Object.keys(params).map(function(k) {
    return encodeURIComponent(k) + '=' + encodeURIComponent(params[k]);
  }).join('&');

  var navigated = false;
  try {
    window.parent.location.search = '?' + qs;
    navigated = true;
  } catch(e1) {
    try {
      window.top.location.search = '?' + qs;
      navigated = true;
    } catch(e2) {
      try {
        window.parent.location.href = window.location.origin + '?' + qs;
        navigated = true;
      } catch(e3) {
        showError('Navigasi gagal. Error: ' + e1.message + ' | ' + e2.message);
      }
    }
  }
  if (navigated) setStatus('Login berhasil, memuat aplikasi...');
}

function signIn() {
  var btn = document.getElementById('btn');
  btn.disabled = true;
  btn.textContent = 'Menghubungkan ke Google...';
  document.getElementById('err').className = '';
  setStatus('Menyiapkan Autentikasi...');

  try {
    // Trik Bypass: Akses parent window untuk menghindari batasan protocol 'about:srcdoc'
    var pw = window.parent;
    var pDoc = pw.document;

    function runAuth() {
      if (!pw.firebase.apps.length) {
        pw.firebase.initializeApp(firebaseConfig);
      }
      var provider = new pw.firebase.auth.GoogleAuthProvider();
      provider.addScope('email');
      provider.addScope('profile');
      
      setStatus('Membuka popup login Google...');
      pw.firebase.auth().signInWithPopup(provider)
        .then(function(result) {
          setStatus('Login berhasil, mengambil token...');
          return result.user.getIdToken(true).then(function(token) {
            navigateParent({
              fb_token : token,
              fb_uid   : result.user.uid,
              fb_email : result.user.email || '',
              fb_name  : result.user.displayName || '',
              fb_photo : result.user.photoURL || ''
            });
          });
        })
        .catch(function(error) {
          console.error('Auth error:', error.code, error.message);
          var msg = error.message;
          if (error.code === 'auth/popup-blocked') {
            msg = 'Popup diblokir browser. Izinkan popup untuk situs ini, lalu coba lagi.';
          } else if (error.code === 'auth/popup-closed-by-user' || error.code === 'auth/cancelled-by-user') {
            msg = 'Login dibatalkan. Silakan coba lagi.';
          } else if (error.code === 'auth/network-request-failed') {
            msg = 'Gagal terhubung ke internet. Periksa koneksi Anda.';
          }
          showError(msg);
        });
    }

    // Cek apakah library sudah di-load di parent window sebelumnya
    if (pw.firebase && pw.firebase.auth) {
      runAuth();
    } else {
      setStatus('Memuat dependensi Firebase secara dinamis...');
      var s1 = pDoc.createElement('script');
      s1.src = "https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js";
      pDoc.head.appendChild(s1);
      
      s1.onload = function() {
        var s2 = pDoc.createElement('script');
        s2.src = "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth-compat.js";
        pDoc.head.appendChild(s2);
        
        s2.onload = runAuth;
        s2.onerror = function() { showError("Gagal memuat modul Auth Firebase."); };
      };
      s1.onerror = function() { showError("Gagal memuat core Firebase."); };
    }
  } catch (err) {
    showError("Akses popup terblokir. Error: " + err.message);
  }
}
</script>

<script>
// ── Init Firebase ─────────────────────────────────────────────
var firebaseConfig = CFG_JSON;
try {
  if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
  }
  document.getElementById('status').textContent = '';
} catch(initErr) {
  showError('Firebase init error: ' + initErr.message);
}

function setStatus(msg) {
  document.getElementById('status').textContent = msg;
}

function showError(msg) {
  var el = document.getElementById('err');
  el.textContent = msg;
  el.className = 'show';
  var btn = document.getElementById('btn');
  btn.disabled = false;
  btn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg> Masuk dengan Google';
  setStatus('');
}

function navigateParent(params) {
  // Build query string
  var qs = Object.keys(params).map(function(k) {
    return encodeURIComponent(k) + '=' + encodeURIComponent(params[k]);
  }).join('&');

  // Try multiple ways to navigate parent
  var navigated = false;
  try {
    window.parent.location.search = '?' + qs;
    navigated = true;
  } catch(e1) {
    try {
      window.top.location.search = '?' + qs;
      navigated = true;
    } catch(e2) {
      // Last resort: open in same tab
      try {
        window.parent.location.href = window.location.origin + '?' + qs;
        navigated = true;
      } catch(e3) {
        showError('Navigasi gagal. Error: ' + e1.message + ' | ' + e2.message);
      }
    }
  }
  if (navigated) setStatus('Login berhasil, memuat aplikasi...');
}

function signIn() {
  var btn = document.getElementById('btn');
  btn.disabled = true;
  btn.textContent = 'Menghubungkan ke Google...';
  document.getElementById('err').className = '';
  setStatus('Membuka jendela login Google...');

  var provider = new firebase.auth.GoogleAuthProvider();
  provider.addScope('email');
  provider.addScope('profile');

  firebase.auth().signInWithPopup(provider)
    .then(function(result) {
      setStatus('Login berhasil, mengambil token...');
      return result.user.getIdToken(true);
    })
    .then(function(token) {
      var u = firebase.auth().currentUser;
      setStatus('Token diterima, mengalihkan...');
      navigateParent({
        fb_token : token,
        fb_uid   : u.uid,
        fb_email : u.email || '',
        fb_name  : u.displayName || '',
        fb_photo : u.photoURL || ''
      });
    })
    .catch(function(error) {
      console.error('Auth error:', error.code, error.message);
      var msg = error.message;
      if (error.code === 'auth/popup-blocked') {
        msg = 'Popup diblokir browser. Izinkan popup untuk situs ini, lalu coba lagi.';
      } else if (error.code === 'auth/popup-closed-by-user') {
        msg = 'Jendela login ditutup. Silakan coba lagi.';
      } else if (error.code === 'auth/cancelled-by-user') {
        msg = 'Login dibatalkan. Silakan coba lagi.';
      } else if (error.code === 'auth/network-request-failed') {
        msg = 'Gagal terhubung ke internet. Periksa koneksi Anda.';
      }
      showError(msg);
    });
}
</script>
""".replace("CFG_JSON", cfg_json)

    components.html(login_html, height=380, scrolling=False)

if st.session_state.user is None:
    login_page(); st.stop()

user=st.session_state.user

# ── HELPERS ──────────────────────────────────────────────────────
def filter_pg(kat):
    if kat=="Semua Kategori": return soal_pg
    return [q for q in soal_pg if q.get("kategori","Umum")==kat]

def prog_html(pct,label=""):
    lbl=f'<div style="font-size:.78rem;opacity:.6;margin-bottom:2px">{label}</div>' if label else ""
    return f'{lbl}<div class="prog-wrap"><div class="prog-bar" style="width:{pct*100:.1f}%"></div></div>'

def metrics_html(*items):
    boxes="".join(f'<div class="metric-box"><div class="mval">{v}</div><div class="mlbl">{l}</div></div>' for v,l in items)
    return f'<div class="metric-row">{boxes}</div>'

def donut_html(benar,total):
    pct=benar/total*100 if total else 0
    R=66;circ=2*3.14159*R;dash=circ*benar/total if total else 0
    return f'<div class="donut-wrap"><svg width="170" height="170" viewBox="0 0 170 170"><circle cx="85" cy="85" r="{R}" fill="none" stroke="#ef4444" stroke-width="20"/><circle cx="85" cy="85" r="{R}" fill="none" stroke="#22c55e" stroke-width="20" stroke-dasharray="{dash:.1f} {circ:.1f}" stroke-dashoffset="{circ/4:.1f}" stroke-linecap="round"/><text x="85" y="79" text-anchor="middle" font-size="22" font-weight="700" fill="currentColor">{pct:.0f}%</text><text x="85" y="99" text-anchor="middle" font-size="11" fill="currentColor" opacity=".6">Skor Akhir</text><text x="85" y="114" text-anchor="middle" font-size="11" fill="currentColor" opacity=".6">{benar}/{total} benar</text></svg></div>'

def konfetti_js():
    return '<canvas id="kc" style="position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:9999"></canvas><script>(function(){var c=document.getElementById("kc");if(!c)return;c.width=innerWidth;c.height=innerHeight;var ctx=c.getContext("2d");var ps=Array.from({length:130},()=>({x:Math.random()*c.width,y:-120-Math.random()*200,r:Math.random()*7+3,col:["#f59e0b","#10b981","#3b82f6","#ec4899","#8b5cf6"][Math.floor(Math.random()*5)],vx:(Math.random()-.5)*2.5,vy:Math.random()*3.5+1.5,rot:Math.random()*360,vr:(Math.random()-.5)*5}));var fr=0;function draw(){ctx.clearRect(0,0,c.width,c.height);ps.forEach(p=>{ctx.save();ctx.translate(p.x,p.y);ctx.rotate(p.rot*Math.PI/180);ctx.fillStyle=p.col;ctx.fillRect(-p.r/2,-p.r/2,p.r,p.r);ctx.restore();p.x+=p.vx;p.y+=p.vy;p.rot+=p.vr;});fr++;if(fr<220)requestAnimationFrame(draw);else ctx.clearRect(0,0,c.width,c.height);}draw();})();</script>'

def toggle_bm(qid):
    if qid in st.session_state.bookmarks: st.session_state.bookmarks.discard(qid)
    else: st.session_state.bookmarks.add(qid)
    save_bookmarks(user["uid"],st.session_state.bookmarks)

def render_opsi_checked(q,saved):
    kunci=q["kunci_jawaban"]
    for k,v in q["opsi"].items():
        if k==kunci and k==saved: cls,icon="opsi-item opsi-benar","✅ "
        elif k==kunci: cls,icon="opsi-item opsi-benar","✅ "
        elif k==saved: cls,icon="opsi-item opsi-salah","❌ "
        else: cls,icon="opsi-item",""
        st.markdown(f'<div class="{cls}">{icon}{k}. {v}</div>',unsafe_allow_html=True)
    if saved==kunci: st.success("**Benar!**")
    else: st.error(f"**Salah.** Kunci: **{kunci}. {q['opsi'][kunci]}**")

def render_opsi_review(q,jaw,kunci):
    for key,teks in q["opsi"].items():
        if key==kunci and key==jaw: st.markdown(f'<div class="opsi-item opsi-benar">✅ {key}. {teks} ← Jawaban Anda (Benar)</div>',unsafe_allow_html=True)
        elif key==kunci: st.markdown(f'<div class="opsi-item opsi-benar">✅ {key}. {teks} ← Kunci Jawaban</div>',unsafe_allow_html=True)
        elif key==jaw: st.markdown(f'<div class="opsi-item opsi-salah">❌ {key}. {teks} ← Jawaban Anda</div>',unsafe_allow_html=True)
        else: st.markdown(f'<div class="opsi-item">{key}. {teks}</div>',unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    ph=(f'<img src="{user["photo"]}" style="width:36px;height:36px;border-radius:50%;object-fit:cover">'
        if user.get("photo") else
        f'<div style="width:36px;height:36px;border-radius:50%;background:#3b82f6;display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:1rem">{user["name"][:1].upper()}</div>')
    st.markdown(f"""
<div style="text-align:center;padding:.5rem 0 .75rem">
  <div style="font-size:1.8rem;margin-bottom:.3rem">🎓</div>
  <div style="font-weight:700;font-size:1.1rem">CAT MHI</div>
  <div style="font-size:.78rem;opacity:.55;margin-top:.1rem;line-height:1.5">Mediator Hubungan Industrial<br>Ahli Madya</div>
</div>
<div style="display:flex;align-items:center;justify-content:center;gap:8px;padding:.5rem;border-radius:10px;border:1px solid rgba(128,128,128,.2);margin:.3rem .2rem .6rem">
  {ph}
  <div style="text-align:left;min-width:0">
    <div style="font-weight:600;font-size:.9rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:110px">{user["name"]}</div>
    <div style="font-size:.72rem;opacity:.5;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:110px">{user["email"]}</div>
  </div>
</div>""",unsafe_allow_html=True)
    st.divider()
    st.markdown(metrics_html((len(soal_pg),"Soal PG"),(len(soal_essay),"Essay"),(st.session_state.simulasi_jumlah,"Simulasi")),unsafe_allow_html=True)
    bmc=len(st.session_state.bookmarks)
    if bmc: st.markdown(f'<div style="text-align:center;font-size:.82rem;opacity:.6;margin-top:.4rem">🔖 {bmc} bookmark</div>',unsafe_allow_html=True)
    if st.session_state.simulasi_histori:
        st.divider()
        st.markdown('<div style="text-align:center;font-size:.8rem;font-weight:600;opacity:.6">Histori Terakhir</div>',unsafe_allow_html=True)
        for h in st.session_state.simulasi_histori[-3:]:
            lulus=h["skor"]>=h.get("passing",70);w="#16a34a" if lulus else "#dc2626"
            st.markdown(f'<div class="skor-item"><span>{"✅" if lulus else "❌"}</span><span style="flex:1;opacity:.6;font-size:.78rem">{h.get("label","")}</span><span class="skor-badge" style="color:{w}">{h["skor"]:.0f}%</span></div>',unsafe_allow_html=True)
    st.divider()
    if st.button("Keluar",use_container_width=True,key="logout"):
        st.session_state.user=None;st.session_state.bookmarks=set();st.rerun()

# ── TABS ─────────────────────────────────────────────────────────
t1,t2,t3,t4,t5=st.tabs(["🏠  Beranda","📝  Latihan PG","✏️  Essay","🚀  Simulasi","🔖  Bookmark"])

# ── BERANDA ──────────────────────────────────────────────────────
with t1:
    st.markdown("## Simulasi Ujikom MHI")
    st.write("Latihan soal **Pilihan Ganda** dan **Essay** untuk persiapan Uji Kompetensi.")
    st.markdown(metrics_html((len(soal_pg),"Soal PG"),(len(soal_essay),"Soal Essay"),(st.session_state.simulasi_jumlah,"Soal Simulasi")),unsafe_allow_html=True)
    st.divider()
    st.markdown("#### 📊 Distribusi per Kategori")
    kc=Counter(q.get("kategori","Umum") for q in soal_pg)
    for kat,cnt in sorted(kc.items(),key=lambda x:-x[1]):
        st.markdown(prog_html(cnt/len(soal_pg),f"{kat} ({cnt} soal)"),unsafe_allow_html=True)
    st.divider()
    st.markdown(f"**Panduan:**\n- **Latihan PG** — soal per soal, filter kategori, ⭐ bookmark, cek jawaban\n- **Latihan Essay** — tulis jawaban lalu tampilkan referensi\n- **Simulasi** — pilih jumlah soal, durasi & ambang lulus, timer otomatis\n- Bookmark tersimpan ke akun Google — tidak hilang meski tutup browser")

# ── LATIHAN PG ───────────────────────────────────────────────────
with t2:
    st.markdown("## 📝 Latihan Pilihan Ganda")
    ck,cr=st.columns([3,1])
    with ck:
        kat_pg=st.selectbox("Kategori",["Semua Kategori"]+SEMUA_KATEGORI,key="pg_kat",label_visibility="collapsed")
    with cr:
        if st.button("🔀 Acak",use_container_width=True,key="pg_reset"):
            pool=filter_pg(kat_pg)
            st.session_state.latihan_pg_questions=random.sample(pool,len(pool))
            st.session_state.latihan_pg_answers={};st.session_state.latihan_pg_checked={}
            st.session_state.current_q=0;st.session_state.latihan_pg_salah_mode=False;st.rerun()
    if not st.session_state.latihan_pg_questions:
        pool=filter_pg(kat_pg);st.session_state.latihan_pg_questions=random.sample(pool,len(pool))
    if st.session_state.latihan_pg_salah_mode and st.session_state.latihan_pg_salah_list:
        questions=st.session_state.latihan_pg_salah_list
        st.info(f"🔁 Mode Soal Salah — {len(questions)} soal")
        if st.button("← Kembali ke Semua Soal",key="pg_back"):
            st.session_state.latihan_pg_salah_mode=False;st.session_state.current_q=0;st.rerun()
    else:
        questions=st.session_state.latihan_pg_questions
    total_q=len(questions);idx=min(st.session_state.current_q,total_q-1);q=questions[idx]
    aqr=st.session_state.latihan_pg_questions
    n_ch=len(st.session_state.latihan_pg_checked)
    n_bn=sum(1 for i in st.session_state.latihan_pg_checked if i<len(aqr) and st.session_state.latihan_pg_answers.get(i)==aqr[i]["kunci_jawaban"])
    if n_ch:
        st.markdown(metrics_html((n_ch,"Dicek"),(n_bn,"Benar"),(n_ch-n_bn,"Salah"),(f"{n_bn/n_ch*100:.0f}%","Akurasi")),unsafe_allow_html=True)
    st.markdown(prog_html((idx+1)/total_q,f"Soal {idx+1} dari {total_q}"),unsafe_allow_html=True)
    bm_id=q["id"];is_bm=bm_id in st.session_state.bookmarks
    cq,cbm=st.columns([11,1])
    with cbm:
        if st.button("⭐" if is_bm else "☆",key=f"bm_{idx}_{bm_id}",help="Bookmark"):
            toggle_bm(bm_id);st.rerun()
    st.markdown(f'<span class="tag">{q.get("kategori","Umum")}</span>',unsafe_allow_html=True)
    st.markdown(f'<div class="q-card">{q["pertanyaan"]}</div>',unsafe_allow_html=True)
    saved=st.session_state.latihan_pg_answers.get(idx)
    opsi_keys=list(q["opsi"].keys())
    def_idx=opsi_keys.index(saved) if saved in opsi_keys else 0
    sudah_dicek=st.session_state.latihan_pg_checked.get(idx,False)
    if sudah_dicek:
        render_opsi_checked(q,saved)
    else:
        pilihan=st.radio("",opsi_keys,format_func=lambda x:f"{x}. {q['opsi'][x]}",key=f"pg_r_{idx}_{q['id']}",index=def_idx,label_visibility="collapsed")
        st.session_state.latihan_pg_answers[idx]=pilihan
        if st.button("✅  Cek Jawaban",type="primary",key=f"pg_cek_{idx}"):
            st.session_state.latihan_pg_checked[idx]=True;st.rerun()
    st.divider()
    c1,c2=st.columns(2)
    with c1:
        if idx>0 and st.button("◀  Sebelumnya",use_container_width=True,key="pg_prev"):
            st.session_state.current_q-=1;st.rerun()
    with c2:
        if idx<total_q-1 and st.button("Selanjutnya  ▶",use_container_width=True,key="pg_next"):
            st.session_state.current_q+=1;st.rerun()
    n_sal=n_ch-n_bn
    if n_sal>0 and not st.session_state.latihan_pg_salah_mode:
        st.divider()
        if st.button(f"🔁  Latihan Ulang {n_sal} Soal Salah",use_container_width=True,key="pg_salah"):
            sl=[aqr[i] for i in st.session_state.latihan_pg_checked if i<len(aqr) and st.session_state.latihan_pg_answers.get(i)!=aqr[i]["kunci_jawaban"]]
            st.session_state.latihan_pg_salah_list=random.sample(sl,len(sl))
            st.session_state.latihan_pg_salah_mode=True;st.session_state.latihan_pg_answers={}
            st.session_state.latihan_pg_checked={};st.session_state.current_q=0;st.rerun()

# ── ESSAY ────────────────────────────────────────────────────────
with t3:
    st.markdown("## ✏️ Latihan Essay")
    ce,re=st.columns([3,1])
    with re:
        if st.button("🔀 Acak",use_container_width=True,key="es_reset"):
            st.session_state.latihan_essay_questions=random.sample(soal_essay,len(soal_essay))
            st.session_state.latihan_essay_shown={};st.session_state.current_q=0;st.rerun()
    if not st.session_state.latihan_essay_questions:
        st.session_state.latihan_essay_questions=random.sample(soal_essay,len(soal_essay))
    qse=st.session_state.latihan_essay_questions;tote=len(qse)
    idxe=min(st.session_state.current_q,tote-1);qe=qse[idxe]
    with ce: st.caption(f"Referensi ditampilkan: {len(st.session_state.latihan_essay_shown)}/{tote}")
    st.markdown(prog_html((idxe+1)/tote,f"Soal {idxe+1} dari {tote}"),unsafe_allow_html=True)
    st.markdown(f'<div class="q-card">{qe["pertanyaan"]}</div>',unsafe_allow_html=True)
    st.text_area("Jawaban:",height=130,key=f"es_in_{idxe}",label_visibility="collapsed",placeholder="Tulis jawaban Anda di sini...")
    if st.button("📖  Tampilkan Referensi",type="primary",key=f"es_ref_{idxe}"):
        st.session_state.latihan_essay_shown[idxe]=True
    if st.session_state.latihan_essay_shown.get(idxe):
        st.info("**Referensi Jawaban:**\n\n"+qe["referensi_jawaban"])
    st.divider()
    e1,e2=st.columns(2)
    with e1:
        if idxe>0 and st.button("◀  Sebelumnya",use_container_width=True,key="es_prev"):
            st.session_state.current_q-=1;st.rerun()
    with e2:
        if idxe<tote-1 and st.button("Selanjutnya  ▶",use_container_width=True,key="es_next"):
            st.session_state.current_q+=1;st.rerun()

# ── SIMULASI ─────────────────────────────────────────────────────
with t4:
    sim_q=st.session_state.simulasi_questions
    if not st.session_state.simulasi_started:
        st.markdown("## 🚀 Simulasi Ujian")
        sj,sd=st.columns(2)
        with sj:
            jml=st.selectbox("Jumlah",JUMLAH_OPSI_SIM,index=JUMLAH_OPSI_SIM.index(st.session_state.simulasi_jumlah),key="sim_jml")
            st.session_state.simulasi_jumlah=jml
        with sd:
            dlbl=st.selectbox("Durasi",list(DURASI_OPSI.keys()),index=list(DURASI_OPSI.keys()).index(st.session_state.simulasi_durasi_label),key="sim_dur")
            st.session_state.simulasi_durasi_label=dlbl
        sk,sp=st.columns(2)
        with sk:
            ks=st.selectbox("Kategori",["Semua Kategori"]+SEMUA_KATEGORI,key="sim_kat")
            st.session_state.simulasi_kategori=ks
        with sp:
            ps=st.selectbox("Ambang Lulus",PASSING_OPSI,index=PASSING_OPSI.index(st.session_state.simulasi_passing),format_func=lambda x:f"{x}%",key="sim_pass")
            st.session_state.simulasi_passing=ps
        pool=filter_pg(ks);nsim=min(jml,len(pool))
        st.markdown(metrics_html((len(pool),"Tersedia"),(nsim,"Diambil"),(dlbl.replace(" menit","m"),"Durasi"),(f"{ps}%","Min. Lulus")),unsafe_allow_html=True)
        st.warning("⚠️ Timer langsung berjalan setelah klik Mulai.")
        if st.button("▶️  Mulai Simulasi",type="primary",use_container_width=True,key="sim_mulai"):
            st.session_state.simulasi_started=True;st.session_state.simulasi_answers={}
            st.session_state.simulasi_submitted=False;st.session_state.simulasi_start_time=time.time()
            st.session_state.simulasi_questions=random.sample(pool,nsim);st.session_state.current_q=0
            st.session_state.simulasi_show_review=False;st.session_state.simulasi_review_idx=0
            st.session_state._hist_saved=False;st.session_state.sim_confirm_kumpul=False;st.rerun()
        if st.session_state.simulasi_histori:
            st.divider();st.markdown("#### 📈 Histori Skor")
            for h in reversed(st.session_state.simulasi_histori):
                lulus=h["skor"]>=h.get("passing",70);w="#16a34a" if lulus else "#dc2626"
                mnt=h["waktu"]//60;dtk=h["waktu"]%60
                st.markdown(f'<div class="skor-item"><span>{"✅" if lulus else "❌"}</span><span style="flex:1">{h.get("label","")}</span><span style="opacity:.6;font-size:.8rem">{h["benar"]}/{h["total"]} {mnt}m{dtk}s</span><span class="skor-badge" style="color:{w}">{h["skor"]:.1f}%</span></div>',unsafe_allow_html=True)
    elif st.session_state.simulasi_submitted:
        tq=len(sim_q);passing=st.session_state.simulasi_passing
        if not st.session_state.simulasi_show_review:
            st.markdown("## 🎉 Hasil Simulasi")
            benar=sum(1 for q in sim_q if st.session_state.simulasi_answers.get(str(q["id"]))==q["kunci_jawaban"])
            salah=tq-benar;sko=benar/tq*100 if tq else 0;lulus=sko>=passing
            wkt=int(time.time()-st.session_state.simulasi_start_time);mnt=wkt//60;dtk=wkt%60
            if not st.session_state._hist_saved:
                st.session_state.simulasi_histori.append({"skor":sko,"benar":benar,"total":tq,"waktu":wkt,"passing":passing,"label":f"Sim #{len(st.session_state.simulasi_histori)+1} · {st.session_state.simulasi_kategori[:18]}"})
                st.session_state._hist_saved=True
            if lulus: st.success("### ✅ LULUS"); components.html(konfetti_js(),height=0)
            else: st.error(f"### ❌ BELUM LULUS (min. {passing}%)")
            st.markdown(donut_html(benar,tq),unsafe_allow_html=True)
            st.markdown(metrics_html((f"{sko:.1f}%","Skor"),(benar,"Benar"),(salah,"Salah"),(f"{mnt}m {dtk}s","Waktu")),unsafe_allow_html=True)
            st.divider()
            ra,rb=st.columns(2)
            with ra:
                if st.button("🔍  Review Jawaban",use_container_width=True,type="primary"):
                    st.session_state.simulasi_show_review=True;st.session_state.simulasi_review_idx=0;st.rerun()
            with rb:
                if st.button("🔄  Simulasi Baru",use_container_width=True):
                    st.session_state.simulasi_started=False;st.session_state.simulasi_submitted=False
                    st.session_state.simulasi_show_review=False;st.session_state._hist_saved=False;st.rerun()
            if salah>0:
                st.divider()
                if st.button(f"🔁  Latihan {salah} Soal Salah di Tab PG",use_container_width=True):
                    sl=[q for q in sim_q if st.session_state.simulasi_answers.get(str(q["id"]))!=q["kunci_jawaban"]]
                    st.session_state.latihan_pg_salah_list=random.sample(sl,len(sl))
                    st.session_state.latihan_pg_salah_mode=True;st.session_state.latihan_pg_answers={}
                    st.session_state.latihan_pg_checked={};st.session_state.current_q=0;st.rerun()
        else:
            st.markdown("## 🔍 Review Jawaban");ridx=st.session_state.simulasi_review_idx;q=sim_q[ridx]
            tq=len(sim_q)
            nbt=sum(1 for qq in sim_q if st.session_state.simulasi_answers.get(str(qq["id"]))==qq["kunci_jawaban"])
            st.caption(f"Soal {ridx+1}/{tq}  |  Benar: {nbt}/{tq}")
            st.markdown(prog_html((ridx+1)/tq),unsafe_allow_html=True)
            jaw=st.session_state.simulasi_answers.get(str(q["id"]));kunci=q["kunci_jawaban"]
            if jaw==kunci: st.success(f"Soal {ridx+1} — **Benar ✅**")
            else: st.error(f"Soal {ridx+1} — **Salah ❌**")
            st.markdown(f'<span class="tag">{q.get("kategori","Umum")}</span>',unsafe_allow_html=True)
            st.markdown(f'<div class="q-card">{q["pertanyaan"]}</div>',unsafe_allow_html=True)
            render_opsi_review(q,jaw,kunci)
            st.divider()
            rv1,rv2,rv3=st.columns([1,2,1])
            with rv1:
                if ridx>0 and st.button("◀",use_container_width=True,key="rv_p"):
                    st.session_state.simulasi_review_idx-=1;st.rerun()
            with rv2:
                if st.button("◀  Kembali ke Hasil",use_container_width=True,key="rv_b"):
                    st.session_state.simulasi_show_review=False;st.rerun()
            with rv3:
                if ridx<tq-1 and st.button("▶",use_container_width=True,key="rv_n"):
                    st.session_state.simulasi_review_idx+=1;st.rerun()
    else:
        tq=len(sim_q);dur=DURASI_OPSI.get(st.session_state.simulasi_durasi_label,7200)
        idx=min(st.session_state.current_q,tq-1);q=sim_q[idx]
        ela=int(time.time()-st.session_state.simulasi_start_time);sisa=max(0,dur-ela)
        if sisa==0: st.session_state.simulasi_submitted=True;st.rerun()
        st.markdown(f"## Soal {idx+1} / {tq}")
        st.markdown(prog_html((idx+1)/tq),unsafe_allow_html=True)
        components.html(f'<div style="background:rgba(239,68,68,.08);border-left:4px solid #ef4444;padding:9px 15px;border-radius:9px;margin-bottom:6px;font-family:sans-serif"><span style="font-size:.92rem;font-weight:600">⏱️ Sisa: </span><span id="clk" style="font-size:1.05rem;font-weight:700;color:#ef4444">--:--</span></div><script>var tL={sisa},el=document.getElementById("clk");var tm=setInterval(function(){{if(tL<=0){{clearInterval(tm);el.innerHTML="⚠️ HABIS!";return;}}var m=Math.floor(tL/60),s=tL%60;el.innerHTML=(m<10?"0":"")+m+":"+(s<10?"0":"")+s;tL--;}},1000);</script>',height=52)
        st.markdown(f'<span class="tag">{q.get("kategori","Umum")}</span>',unsafe_allow_html=True)
        st.markdown(f'<div class="q-card">{q["pertanyaan"]}</div>',unsafe_allow_html=True)
        opk=list(q["opsi"].keys());sa=st.session_state.simulasi_answers.get(str(q["id"]))
        di=opk.index(sa) if sa in opk else None
        pil=st.radio("",opk,format_func=lambda x:f"{x}. {q['opsi'][x]}",key=f"sim_r_{idx}_{q['id']}",index=di,label_visibility="collapsed")
        if pil: st.session_state.simulasi_answers[str(q["id"])]=pil
        ndj=len(st.session_state.simulasi_answers);nbl=tq-ndj
        st.caption(f"Dijawab: {ndj}/{tq}");st.divider()
        s1,s2,s3=st.columns([1,2,1])
        with s1:
            if idx>0 and st.button("◀",use_container_width=True,key="sim_p"):
                st.session_state.current_q-=1;st.rerun()
        with s2:
            if st.button(f"📥  Kumpulkan ({ndj}/{tq})",use_container_width=True,type="primary",key="sim_k"):
                if nbl>0: st.session_state.sim_confirm_kumpul=True
                else: st.session_state.simulasi_submitted=True;st.rerun()
        with s3:
            if idx<tq-1 and st.button("▶",use_container_width=True,key="sim_n"):
                st.session_state.current_q+=1;st.rerun()
        if st.session_state.sim_confirm_kumpul:
            st.warning(f"⚠️ **{nbl} soal** belum dijawab. Yakin ingin mengumpulkan?")
            ck1,ck2=st.columns(2)
            with ck1:
                if st.button("✅  Ya, Kumpulkan",type="primary",use_container_width=True,key="sim_ya"):
                    st.session_state.simulasi_submitted=True;st.session_state.sim_confirm_kumpul=False;st.rerun()
            with ck2:
                if st.button("← Kembali",use_container_width=True,key="sim_batal"):
                    st.session_state.sim_confirm_kumpul=False;st.rerun()
        with st.expander("🗺️  Peta Soal",expanded=False):
            cpp=10;rows=[sim_q[i:i+cpp] for i in range(0,tq,cpp)]
            for rs,row in enumerate(rows):
                cols=st.columns(cpp)
                for cp,soal in enumerate(row):
                    si=rs*cpp+cp;dj=str(soal["id"]) in st.session_state.simulasi_answers
                    with cols[cp]:
                        if st.button(f"{'✓' if dj else '○'}{si+1}",key=f"pt_{si}",use_container_width=True):
                            st.session_state.current_q=si;st.rerun()

# ── BOOKMARK ─────────────────────────────────────────────────────
with t5:
    st.markdown("## 🔖 Soal Bookmark")
    bmids=st.session_state.bookmarks
    if not bmids:
        st.info("Belum ada soal yang di-bookmark.\nKlik ☆ pada soal di Tab Latihan PG.")
    else:
        bms=[q for q in soal_pg if q["id"] in bmids]
        st.caption(f"{len(bms)} soal di-bookmark · tersimpan ke akun Google")
        if st.button("🗑️  Hapus Semua Bookmark",key="bm_all"):
            st.session_state.bookmarks=set();save_bookmarks(user["uid"],set());st.rerun()
        for q in bms:
            with st.expander(f'[{q.get("kategori","Umum")}]  {q["pertanyaan"][:75]}...'):
                for k,v in q["opsi"].items():
                    if k==q["kunci_jawaban"]: st.markdown(f'<div class="opsi-item opsi-benar">✅ {k}. {v}</div>',unsafe_allow_html=True)
                    else: st.markdown(f'<div class="opsi-item">{k}. {v}</div>',unsafe_allow_html=True)
                st.caption(f'Kunci: **{q["kunci_jawaban"]}**')
                if st.button("🗑️  Hapus",key=f"bm_del_{q['id']}"):
                    toggle_bm(q["id"]);st.rerun()
