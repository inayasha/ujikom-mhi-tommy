import streamlit as st
import streamlit.components.v1 as components
import json
import time
import random
from collections import Counter

# ══════════════════════════════════════════════════════════════════
# 1. KONFIGURASI
# ══════════════════════════════════════════════════════════════════
st.set_page_config(page_title="CAT MHI", page_icon="🎓", layout="centered")

# ══════════════════════════════════════════════════════════════════
# 2. LOAD DATA
# ══════════════════════════════════════════════════════════════════
@st.cache_data
def load_data():
    with open("soal_pg.json", "r", encoding="utf-8") as f:
        soal_pg = json.load(f)
    with open("soal_essay.json", "r", encoding="utf-8") as f:
        soal_essay = json.load(f)
    return soal_pg, soal_essay

try:
    soal_pg, soal_essay = load_data()
except FileNotFoundError:
    st.error("Gagal memuat database soal. Pastikan soal_pg.json dan soal_essay.json tersedia.")
    st.stop()

# Mapping nilai "paket" di JSON ke label yang enak dibaca
PAKET_LABEL = {
    "integritas":  "Integritas",
    "manajerial":  "Manajerial",
    "teknis_1":    "Teknis / Hubungan Industrial",
    "teknis_2":    "Teknis / Hubungan Industrial",
}

def kategori_soal(q):
    """Ambil label kategori dari field 'paket' (fallback ke 'kategori' lama, lalu 'Umum')."""
    p = q.get('paket') or q.get('kategori')
    if not p:
        return "Umum"
    return PAKET_LABEL.get(p, p.replace('_', ' ').title())

SEMUA_KATEGORI  = sorted(set(kategori_soal(q) for q in soal_pg))
JUMLAH_OPSI_SIM = [50, 75, 100]
DURASI_OPSI     = {"60 menit": 3600, "90 menit": 5400, "120 menit": 7200}
PASSING_SCORE   = 70.0          # default; bisa diubah user di tab Simulasi
AMBANG_OPSI     = [70, 75, 80, 85]

# ══════════════════════════════════════════════════════════════════
# 3. CSS  — ikut tema Streamlit (light/dark diatur dari Settings)
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Body text default (markdown, write, prose) ── */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    font-size: clamp(1rem, 2.5vw, 1.12rem) !important;
    line-height: 1.7;
}
/* ── Textarea input (jawaban) lebih besar ── */
.stTextArea textarea {
    font-size: clamp(1rem, 2.5vw, 1.12rem) !important;
}
/* ── Baris kontrol bookmark+acak tetap sejajar di HP ── */
/* Blok kolom setelah elemen yang memuat penanda .ctrl-row: jangan turun */
[data-testid="stElementContainer"]:has(.ctrl-row)
    + [data-testid="stHorizontalBlock"] {
    flex-wrap: nowrap !important;
    gap: 0.5rem !important;
}
[data-testid="stElementContainer"]:has(.ctrl-row)
    + [data-testid="stHorizontalBlock"] > [data-testid="column"] {
    min-width: 0 !important;
    flex: 1 1 0 !important;
}
/* ── Sidebar rata tengah ── */
[data-testid="stSidebar"] > div:first-child {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding-top: 1.2rem;
}
[data-testid="stSidebar"] .stMetric,
[data-testid="stSidebar"] .stMetric label,
[data-testid="stSidebar"] .stMetric > div {
    text-align: center !important;
    justify-content: center !important;
}

/* ── Font responsive (mobile) ── */
h1 { font-size: clamp(1.5rem, 4.5vw, 2.3rem) !important; }
h2 { font-size: clamp(1.3rem, 4vw, 1.9rem) !important; }
/* ── Tab labels — lebih besar & proporsional ── */
[data-testid="stTabs"] button p {
    font-size: clamp(1.02rem, 2.8vw, 1.2rem) !important;
    font-weight: 600 !important;
    white-space: nowrap;
}
[data-testid="stTabs"] button {
    padding: 0.55rem 0.9rem !important;
}

/* ── Semua tombol Streamlit — perbesar font ── */
.stButton > button {
    font-size: clamp(1.02rem, 2.7vw, 1.2rem) !important;
    font-weight: 600 !important;
    padding: 0.5rem 1rem !important;
    border-radius: 10px !important;
}
.stButton > button[kind="primary"] {
    font-size: clamp(1.08rem, 2.8vw, 1.25rem) !important;
}

/* ── Selectbox, radio, textarea label ── */
.stSelectbox label, .stSelectbox > div,
.stRadio label, .stTextArea label {
    font-size: clamp(1rem, 2.6vw, 1.15rem) !important;
}
.stRadio > div > label > div > p {
    font-size: clamp(1rem, 2.6vw, 1.15rem) !important;
}

/* ── Radio pilihan ganda: align atas + hanging indent + jarak lega ── */
.stRadio > div {
    gap: 0.55rem !important;             /* jarak antar opsi */
}
.stRadio > div > label {
    align-items: flex-start !important;   /* bulatan sejajar baris pertama teks */
    padding: 0.15rem 0 !important;
}
/* Bulatan radio tidak ikut mengecil & tetap di atas */
.stRadio > div > label > div:first-child {
    margin-top: 0.15rem !important;
    flex-shrink: 0 !important;
}
/* Teks opsi: baris ke-2 dst menjorok sejajar huruf pertama (hanging indent) */
.stRadio > div > label > div:last-child p {
    line-height: 1.5 !important;
    padding-left: 1.4em !important;
    text-indent: -1.4em !important;
}
.stRadio > div > label > div:last-child {
    padding-left: 0.15rem !important;
}

/* ── Caption — lebih besar sedikit ── */
.stCaption, [data-testid="stCaptionContainer"] {
    font-size: clamp(0.92rem, 2.3vw, 1.05rem) !important;
}

/* ── Sidebar: perbesar semua teks ── */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div {
    font-size: clamp(0.98rem, 2.4vw, 1.12rem);
}

/* ── Progress bar animasi ── */
.prog-wrap {
    background: rgba(128,128,128,0.2);
    border-radius: 99px;
    height: 7px;
    margin: 0.3rem 0 0.6rem;
    overflow: hidden;
}
.prog-bar {
    height: 7px;
    border-radius: 99px;
    background: linear-gradient(90deg, #3b82f6, #7c3aed);
    transition: width 0.45s cubic-bezier(.4,0,.2,1);
}

/* ── Card soal ── */
.q-card {
    border: 1px solid rgba(128,128,128,0.25);
    border-radius: 14px;
    padding: 1.2rem 1.45rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    font-size: clamp(1.1rem, 2.9vw, 1.25rem);
    line-height: 1.7;
}

/* ── Metric row (center + responsive) ── */
.metric-row {
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
    justify-content: center;
    margin: 0.75rem 0;
}
/* ── Metric vertikal (untuk sidebar) — berjejer ke bawah ── */
.metric-col {
    flex-direction: column;
    flex-wrap: nowrap;
    gap: 0.65rem;
}
.metric-col .metric-box {
    width: 100%;
    flex: none;
    padding: 0.85rem 1rem;
}
.metric-box {
    border: 1px solid rgba(128,128,128,0.25);
    border-radius: 12px;
    padding: 0.7rem 1rem;
    text-align: center;
    flex: 1 1 80px;
    min-width: 75px;
    box-shadow: 0 1px 5px rgba(0,0,0,0.05);
}
.metric-box .mval {
    font-size: clamp(1.4rem, 4.5vw, 1.75rem);
    font-weight: 700;
    color: #3b82f6;
    line-height: 1.1;
}
.metric-box .mlbl {
    font-size: 0.9rem;
    opacity: 0.65;
    margin-top: 0.15rem;
}

/* ── Tag kategori ── */
.tag {
    display: inline-block;
    background: rgba(59,130,246,0.12);
    color: #3b82f6;
    border-radius: 99px;
    font-size: 0.9rem;
    font-weight: 600;
    padding: 0.12rem 0.6rem;
    margin-bottom: 0.5rem;
}

/* ── Opsi jawaban ── */
.opsi-item {
    display: block;
    padding: 0.65rem 0.95rem;
    border-radius: 9px;
    margin-bottom: 0.35rem;
    border: 1.5px solid rgba(128,128,128,0.25);
    font-size: clamp(1.02rem, 2.7vw, 1.18rem);
}
.opsi-benar {
    border-color: #16a34a !important;
    background: rgba(22,163,74,0.1) !important;
    color: #15803d !important;
    font-weight: 600;
}
.opsi-salah {
    border-color: #dc2626 !important;
    background: rgba(220,38,38,0.08) !important;
    color: #b91c1c !important;
    font-weight: 600;
}

/* ── Donut chart ── */
.donut-wrap { display: flex; justify-content: center; margin: 0.8rem 0; }

/* ── Histori skor ── */
.skor-item {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.38rem 0.6rem;
    border-radius: 8px;
    border: 1px solid rgba(128,128,128,0.2);
    margin-bottom: 0.35rem;
    font-size: 1.02rem;
}
.skor-badge { font-weight: 700; font-size: 1.15rem; min-width: 52px; text-align: right; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 4. STATE
# ══════════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        'current_q': 0,
        # Simulasi
        'simulasi_started': False,
        'simulasi_answers': {},
        'simulasi_submitted': False,
        'simulasi_start_time': None,
        'simulasi_questions': [],
        'simulasi_review_idx': 0,
        'simulasi_show_review': False,
        'simulasi_jumlah': 100,
        'simulasi_durasi_label': "120 menit",
        'simulasi_kategori': "Semua Kategori",
        'simulasi_histori': [],
        'sim_confirm_kumpul': False,
        '_hist_saved': False,
        'passing_score': PASSING_SCORE,
        # Latihan PG
        'latihan_pg_questions': [],
        'latihan_pg_answers': {},
        'latihan_pg_checked': {},
        'latihan_pg_salah_mode': False,
        'latihan_pg_salah_list': [],
        # Latihan Essay
        'latihan_essay_questions': [],
        'latihan_essay_shown': {},
        # Bookmark
        'bookmarks': set(),
        'bookmarks_essay': set(),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
def filter_pg(kat):
    if kat == "Semua Kategori":
        return soal_pg
    return [q for q in soal_pg if kategori_soal(q) == kat]

def prog_html(pct, label=""):
    lbl = f'<div style="font-size:.85rem;opacity:.6;margin-bottom:2px">{label}</div>' if label else ""
    return f'{lbl}<div class="prog-wrap"><div class="prog-bar" style="width:{pct*100:.1f}%"></div></div>'

def metrics_html(*items, vertical=False):
    boxes = "".join(
        f'<div class="metric-box"><div class="mval">{v}</div><div class="mlbl">{l}</div></div>'
        for v, l in items)
    cls = "metric-row metric-col" if vertical else "metric-row"
    return f'<div class="{cls}">{boxes}</div>'

def donut_html(benar, total):
    pct  = benar / total * 100 if total else 0
    R    = 66
    circ = 2 * 3.14159 * R
    dash = circ * benar / total if total else 0
    return f"""
    <div class="donut-wrap">
      <svg width="165" height="165" viewBox="0 0 165 165">
        <circle cx="82.5" cy="82.5" r="{R}" fill="none" stroke="#ef4444" stroke-width="19"/>
        <circle cx="82.5" cy="82.5" r="{R}" fill="none" stroke="#22c55e" stroke-width="19"
                stroke-dasharray="{dash:.1f} {circ:.1f}"
                stroke-dashoffset="{circ/4:.1f}" stroke-linecap="round"/>
        <text x="82.5" y="77" text-anchor="middle" font-size="20"
              font-weight="700" fill="currentColor">{pct:.0f}%</text>
        <text x="82.5" y="96" text-anchor="middle" font-size="10"
              fill="currentColor" opacity=".6">Skor Akhir</text>
        <text x="82.5" y="110" text-anchor="middle" font-size="10"
              fill="currentColor" opacity=".6">{benar}/{total} benar</text>
      </svg>
    </div>"""

def konfetti_js():
    return """<canvas id="kc" style="position:fixed;top:0;left:0;width:100%;height:100%;
    pointer-events:none;z-index:9999"></canvas>
    <script>(function(){var c=document.getElementById('kc');if(!c)return;
    c.width=innerWidth;c.height=innerHeight;var ctx=c.getContext('2d');
    var ps=Array.from({length:110},()=>({x:Math.random()*c.width,y:-100-Math.random()*200,
    r:Math.random()*7+3,col:['#f59e0b','#10b981','#3b82f6','#ec4899','#8b5cf6']
    [Math.floor(Math.random()*5)],vx:(Math.random()-.5)*2.5,vy:Math.random()*3.5+1.5,
    rot:Math.random()*360,vr:(Math.random()-.5)*5}));var fr=0;
    function draw(){ctx.clearRect(0,0,c.width,c.height);
    ps.forEach(p=>{ctx.save();ctx.translate(p.x,p.y);ctx.rotate(p.rot*Math.PI/180);
    ctx.fillStyle=p.col;ctx.fillRect(-p.r/2,-p.r/2,p.r,p.r);ctx.restore();
    p.x+=p.vx;p.y+=p.vy;p.rot+=p.vr;});fr++;
    if(fr<200)requestAnimationFrame(draw);else ctx.clearRect(0,0,c.width,c.height);}
    draw();})();</script>"""

# ══════════════════════════════════════════════════════════════════
def format_jawaban(teks: str) -> str:
    """Ubah teks jawaban menjadi markdown rapi dengan list yang terbaca."""
    import re as _re
    t = teks
    # Ejaan
    t = _re.sub(r'\bsocial\b',     'sosial',     t, flags=_re.IGNORECASE)
    t = _re.sub(r'\bpublic\b',     'publik',     t, flags=_re.IGNORECASE)
    t = _re.sub(r'\bdepensasi\b',  'dispensasi', t, flags=_re.IGNORECASE)
    t = _re.sub(r'\bbipatride?\b', 'bipartit',   t, flags=_re.IGNORECASE)
    # Sisipkan newline sebelum nomor list (1. 2. dst) di tengah paragraf
    t = _re.sub(r' ([1-9][0-9]?\. [A-Z])', r'\n\1', t)
    # Sisipkan newline sebelum sub-poin huruf (a. b. c.)
    t = _re.sub(r' ([a-e]\. [A-Z\"\(])', r'\n\1', t)
    # Sisipkan newline sebelum bullet "- " di tengah kalimat
    t = _re.sub(r' (- [A-Z])', r'\n\1', t)
    # Ganti bullet "o " menjadi "• "
    t = _re.sub(r'(?m)^o ', '• ', t)
    t = _re.sub(r' o ([A-Z])', r'\n• \1', t)
    # Hapus newline berlebih
    t = _re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()


# 5. SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:0.3rem 0 0.5rem">
      <div style="font-size:2.4rem">🎓</div>
      <div style="font-weight:700;font-size:1.25rem;margin-top:0.25rem">CAT MHI</div>
      <div style="font-size:0.85rem;opacity:.6;margin-top:0.1rem;line-height:1.5">
        Mediator Hubungan Industrial<br>Ahli Madya
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown(metrics_html(
        (len(soal_pg),   "Soal PG"),
        (len(soal_essay),"Essay"),
        (st.session_state.simulasi_jumlah, "Simulasi"),
        vertical=True,
    ), unsafe_allow_html=True)

    bm_count = len(st.session_state.bookmarks) + len(st.session_state.bookmarks_essay)
    if bm_count:
        st.markdown(f'<div style="text-align:center;font-size:0.88rem;opacity:.6;'
                    f'margin-top:0.5rem">🔖 {bm_count} soal bookmark</div>',
                    unsafe_allow_html=True)

    if st.session_state.simulasi_histori:
        st.divider()
        st.markdown('<div style="text-align:center;font-size:0.86rem;font-weight:600;opacity:.6">Histori Terakhir</div>',
                    unsafe_allow_html=True)
        for h in st.session_state.simulasi_histori[-3:]:
            lulus = h["skor"] >= st.session_state.passing_score
            warna = "#16a34a" if lulus else "#dc2626"
            icon  = "✔️" if lulus else "❌"
            st.markdown(f"""
            <div class="skor-item">
              <span>{icon}</span>
              <span style="flex:1;opacity:.6;font-size:.72rem">{h.get('label','')}</span>
              <span class="skor-badge" style="color:{warna}">{h['skor']:.0f}%</span>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 6. TABS
# ══════════════════════════════════════════════════════════════════
tab_beranda, tab_pg, tab_essay, tab_simulasi, tab_bm = st.tabs([
    "🏠 Beranda", "📝 Latihan PG", "✏️ Essay", "🚀 Simulasi", "🔖 Bookmark",
])

# ══════════════════════════════════════════════════════════════════
# TAB 1 — BERANDA
# ══════════════════════════════════════════════════════════════════
with tab_beranda:
    st.markdown("## Simulasi Ujikom MHI")
    st.write("Latihan soal **Pilihan Ganda** dan **Essay** untuk persiapan Uji Kompetensi.")

    st.markdown(metrics_html(
        (len(soal_pg),   "Soal PG"),
        (len(soal_essay),"Soal Essay"),
        (st.session_state.simulasi_jumlah, "Soal Simulasi"),
    ), unsafe_allow_html=True)

    st.divider()
    st.markdown("#### 📊 Distribusi per Kategori")
    kat_counts = Counter(kategori_soal(q) for q in soal_pg)
    for kat, cnt in sorted(kat_counts.items(), key=lambda x: -x[1]):
        pct = cnt / len(soal_pg)
        st.markdown(prog_html(pct, f"{kat} ({cnt} soal)"), unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
**Panduan:**
- **Latihan PG** — soal per soal, filter kategori, ⭐ bookmark, cek jawaban
- **Latihan Essay** — tulis jawaban, ☆ bookmark, lalu tampilkan referensi
- **Simulasi** — pilih jumlah soal & durasi, timer otomatis, konfirmasi sebelum kumpul
- Ambang batas lulus: **{int(st.session_state.passing_score)}%**
    """)

# ══════════════════════════════════════════════════════════════════
# TAB 2 — LATIHAN PILIHAN GANDA
# ══════════════════════════════════════════════════════════════════
with tab_pg:
    st.markdown("## 📝 Latihan Pilihan Ganda")

    kat_pg = st.selectbox("Kategori", ["Semua Kategori"] + SEMUA_KATEGORI,
                          key="pg_sel_kat", label_visibility="collapsed")

    if not st.session_state.latihan_pg_questions:
        pool = filter_pg(kat_pg)
        st.session_state.latihan_pg_questions = random.sample(pool, len(pool))

    # Mode soal salah
    if st.session_state.latihan_pg_salah_mode and st.session_state.latihan_pg_salah_list:
        questions = st.session_state.latihan_pg_salah_list
        st.info(f"🚨 Mode Soal Salah — {len(questions)} soal")
        if st.button("← Kembali ke Semua Soal", key="pg_back"):
            st.session_state.latihan_pg_salah_mode = False
            st.session_state.current_q = 0
            st.rerun()
    else:
        questions = st.session_state.latihan_pg_questions

    total_q = len(questions)
    idx     = min(st.session_state.current_q, total_q - 1)
    q       = questions[idx]

    # Statistik mini
    all_q_ref = st.session_state.latihan_pg_questions
    n_checked = len(st.session_state.latihan_pg_checked)
    n_benar   = sum(
        1 for i in st.session_state.latihan_pg_checked
        if i < len(all_q_ref) and
        st.session_state.latihan_pg_answers.get(i) == all_q_ref[i]['kunci_jawaban']
    )
    if n_checked:
        akurasi = f"{n_benar/n_checked*100:.0f}%"
        st.markdown(metrics_html(
            (n_checked, "Dicek"), (n_benar, "Benar"),
            (n_checked - n_benar, "Salah"), (akurasi, "Akurasi"),
        ), unsafe_allow_html=True)

    # Baris kontrol: bookmark ⭐ + Acak berdampingan
    bm_id = q['id']
    is_bm = bm_id in st.session_state.bookmarks
    st.markdown('<div class="ctrl-row"></div>', unsafe_allow_html=True)
    c_bm, c_rst = st.columns([1, 4])
    with c_bm:
        if st.button("⭐" if is_bm else "☆", key=f"bm_pg_{idx}_{bm_id}",
                     help="Bookmark soal ini", use_container_width=True):
            if is_bm:
                st.session_state.bookmarks.discard(bm_id)
            else:
                st.session_state.bookmarks.add(bm_id)
            st.rerun()
    with c_rst:
        if st.button("♻️ Acak", use_container_width=True, key="pg_reset"):
            pool = filter_pg(kat_pg)
            st.session_state.latihan_pg_questions  = random.sample(pool, len(pool))
            st.session_state.latihan_pg_answers    = {}
            st.session_state.latihan_pg_checked    = {}
            st.session_state.current_q             = 0
            st.session_state.latihan_pg_salah_mode = False
            st.rerun()

    # Progress
    st.markdown(prog_html((idx+1)/total_q, f"Soal {idx+1} dari {total_q}"),
                unsafe_allow_html=True)

    kat_label = kategori_soal(q)
    st.markdown(f'<span class="tag">{kat_label}</span>', unsafe_allow_html=True)
    st.markdown(f'<div class="q-card"><strong>{q["pertanyaan"]}</strong></div>',
                unsafe_allow_html=True)

    # Opsi
    saved       = st.session_state.latihan_pg_answers.get(idx)
    opsi_keys   = list(q['opsi'].keys())
    default_idx = opsi_keys.index(saved) if saved in opsi_keys else 0
    sudah_dicek = st.session_state.latihan_pg_checked.get(idx, False)

    if sudah_dicek:
        kunci = q['kunci_jawaban']
        for k, v in q['opsi'].items():
            if k == kunci and k == saved:
                cls, icon = "opsi-item opsi-benar", "✔️ "
            elif k == kunci:
                cls, icon = "opsi-item opsi-benar", "✔️ "
            elif k == saved:
                cls, icon = "opsi-item opsi-salah", "❌ "
            else:
                cls, icon = "opsi-item", ""
            st.markdown(f'<div class="{cls}">{icon}{k}. {v}</div>', unsafe_allow_html=True)
        if saved == kunci:
            st.success("**Benar!**")
        else:
            st.error(f"**Salah.** Kunci: **{kunci}. {q['opsi'][kunci]}**")
    else:
        pilihan = st.radio("Jawaban:", opsi_keys,
                           format_func=lambda x: f"{x}. {q['opsi'][x]}",
                           key=f"pg_r_{idx}_{q['id']}", index=default_idx,
                           label_visibility="collapsed")
        st.session_state.latihan_pg_answers[idx] = pilihan
        if st.button("✔️ Cek Jawaban", type="primary", key=f"pg_cek_{idx}"):
            st.session_state.latihan_pg_checked[idx] = True
            st.rerun()

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if idx > 0:
            if st.button("◀ Sebelumnya", use_container_width=True, key="pg_prev"):
                st.session_state.current_q -= 1
                st.rerun()
    with c2:
        if idx < total_q - 1:
            if st.button("Selanjutnya ▶", use_container_width=True, key="pg_next"):
                st.session_state.current_q += 1
                st.rerun()

    # Tombol latihan soal salah
    n_salah = n_checked - n_benar
    if n_salah > 0 and not st.session_state.latihan_pg_salah_mode:
        st.divider()
        if st.button(f"🚨 Latihan Ulang {n_salah} Soal Salah",
                     use_container_width=True, key="pg_salah_btn"):
            salah_q = [
                all_q_ref[i] for i in st.session_state.latihan_pg_checked
                if i < len(all_q_ref) and
                st.session_state.latihan_pg_answers.get(i) != all_q_ref[i]['kunci_jawaban']
            ]
            st.session_state.latihan_pg_salah_list  = random.sample(salah_q, len(salah_q))
            st.session_state.latihan_pg_salah_mode  = True
            st.session_state.latihan_pg_answers     = {}
            st.session_state.latihan_pg_checked     = {}
            st.session_state.current_q              = 0
            st.rerun()

# ══════════════════════════════════════════════════════════════════
# TAB 3 — LATIHAN ESSAY
# ══════════════════════════════════════════════════════════════════
with tab_essay:
    st.markdown("## ✏️ Latihan Essay")

    if not st.session_state.latihan_essay_questions:
        st.session_state.latihan_essay_questions = random.sample(soal_essay, len(soal_essay))

    qs_e  = st.session_state.latihan_essay_questions
    tot_e = len(qs_e)
    idx_e = min(st.session_state.current_q, tot_e - 1)
    qe    = qs_e[idx_e]

    st.caption(f"Referensi ditampilkan: {len(st.session_state.latihan_essay_shown)}/{tot_e}")

    # Baris kontrol: bookmark ⭐ + Acak berdampingan
    bm_id_e = qe['id']
    is_bm_e = bm_id_e in st.session_state.bookmarks_essay
    st.markdown('<div class="ctrl-row"></div>', unsafe_allow_html=True)
    c_bme, c_re = st.columns([1, 4])
    with c_bme:
        if st.button("⭐" if is_bm_e else "☆", key=f"bm_essay_{idx_e}_{bm_id_e}",
                     help="Bookmark soal ini", use_container_width=True):
            if is_bm_e:
                st.session_state.bookmarks_essay.discard(bm_id_e)
            else:
                st.session_state.bookmarks_essay.add(bm_id_e)
            st.rerun()
    with c_re:
        if st.button("♻️ Acak", use_container_width=True, key="essay_reset"):
            st.session_state.latihan_essay_questions = random.sample(soal_essay, len(soal_essay))
            st.session_state.latihan_essay_shown     = {}
            st.session_state.current_q               = 0
            st.rerun()

    st.markdown(prog_html((idx_e+1)/tot_e, f"Soal {idx_e+1} dari {tot_e}"),
                unsafe_allow_html=True)

    st.markdown(f'<div class="q-card"><strong>{qe["pertanyaan"]}</strong></div>',
                unsafe_allow_html=True)

    st.text_area("Jawaban Anda:", height=130, key=f"essay_in_{idx_e}",
                 label_visibility="collapsed",
                 placeholder="Tulis jawaban Anda di sini...")

    if st.button("📖 Tampilkan Referensi", type="primary", key=f"essay_ref_{idx_e}"):
        st.session_state.latihan_essay_shown[idx_e] = True

    if st.session_state.latihan_essay_shown.get(idx_e):
        jawaban_md = format_jawaban(qe['referensi_jawaban'])
        st.markdown(
            f'''<div style="background:rgba(59,130,246,0.07);border-left:4px solid #3b82f6;
            border-radius:0 10px 10px 0;padding:1.15rem 1.35rem;margin-top:0.5rem">
            <div style="font-weight:600;color:#3b82f6;margin-bottom:0.55rem;font-size:1.1rem">
            📖 Referensi Jawaban:</div>
            <div style="line-height:1.75;white-space:pre-line;font-size:1.08rem">{jawaban_md}</div>
            </div>''',
            unsafe_allow_html=True
        )

    st.divider()
    c1e, c2e = st.columns(2)
    with c1e:
        if idx_e > 0:
            if st.button("◀ Sebelumnya", use_container_width=True, key="essay_prev"):
                st.session_state.current_q -= 1
                st.rerun()
    with c2e:
        if idx_e < tot_e - 1:
            if st.button("Selanjutnya ▶", use_container_width=True, key="essay_next"):
                st.session_state.current_q += 1
                st.rerun()

# ══════════════════════════════════════════════════════════════════
# TAB 4 — SIMULASI
# ══════════════════════════════════════════════════════════════════
with tab_simulasi:
    sim_q = st.session_state.simulasi_questions

    # ── Belum mulai ───────────────────────────────────────────────
    if not st.session_state.simulasi_started:
        st.markdown("## 🚀 Simulasi Ujian")

        c_jml, c_dur = st.columns(2)
        with c_jml:
            jml = st.selectbox("Jumlah Soal", JUMLAH_OPSI_SIM,
                               index=JUMLAH_OPSI_SIM.index(st.session_state.simulasi_jumlah),
                               key="sim_jml")
            st.session_state.simulasi_jumlah = jml
        with c_dur:
            dur_lbl = st.selectbox("Durasi", list(DURASI_OPSI.keys()),
                                   index=list(DURASI_OPSI.keys()).index(
                                       st.session_state.simulasi_durasi_label),
                                   key="sim_dur")
            st.session_state.simulasi_durasi_label = dur_lbl

        c_kat_sim, c_ambang = st.columns(2)
        with c_kat_sim:
            kat_sim = st.selectbox("Kategori Soal", ["Semua Kategori"] + SEMUA_KATEGORI,
                                   key="sim_kat")
            st.session_state.simulasi_kategori = kat_sim
        with c_ambang:
            ambang = st.selectbox(
                "🎯 Ambang Batas Lulus",
                AMBANG_OPSI,
                index=AMBANG_OPSI.index(int(st.session_state.passing_score))
                      if int(st.session_state.passing_score) in AMBANG_OPSI else 0,
                format_func=lambda x: f"{x}%",
                key="sim_ambang",
            )
            st.session_state.passing_score = float(ambang)

        pool_sim = filter_pg(kat_sim)
        n_sim    = min(jml, len(pool_sim))

        st.markdown(metrics_html(
            (len(pool_sim), "Tersedia"),
            (n_sim,         "Diambil"),
            (dur_lbl.replace(" menit", "m"), "Durasi"),
            (f"{int(st.session_state.passing_score)}%", "Min. Lulus"),
        ), unsafe_allow_html=True)

        st.warning("⚠️ Timer langsung berjalan setelah klik Mulai.")

        if st.button("▶️ Mulai Simulasi", type="primary",
                     use_container_width=True, key="sim_mulai"):
            st.session_state.simulasi_started     = True
            st.session_state.simulasi_answers     = {}
            st.session_state.simulasi_submitted   = False
            st.session_state.simulasi_start_time  = time.time()
            st.session_state.simulasi_questions   = random.sample(pool_sim, n_sim)
            st.session_state.current_q            = 0
            st.session_state.simulasi_show_review = False
            st.session_state.simulasi_review_idx  = 0
            st.session_state._hist_saved          = False
            st.session_state.sim_confirm_kumpul   = False
            st.rerun()

        # Histori lengkap
        if st.session_state.simulasi_histori:
            st.divider()
            st.markdown("#### 🔎 Histori Skor")
            for h in reversed(st.session_state.simulasi_histori):
                lulus = h["skor"] >= st.session_state.passing_score
                icon  = "✔️" if lulus else "❌"
                warna = "#16a34a" if lulus else "#dc2626"
                mnt   = h['waktu'] // 60; dtk = h['waktu'] % 60
                st.markdown(f"""
                <div class="skor-item">
                  <span>{icon}</span>
                  <span style="flex:1">{h.get('label','')}</span>
                  <span style="opacity:.6;font-size:.75rem">{h['benar']}/{h['total']} &nbsp;{mnt}m{dtk}s</span>
                  <span class="skor-badge" style="color:{warna}">{h['skor']:.1f}%</span>
                </div>""", unsafe_allow_html=True)

    # ── Hasil ─────────────────────────────────────────────────────
    elif st.session_state.simulasi_submitted:
        total_q = len(sim_q)

        if not st.session_state.simulasi_show_review:
            st.markdown("## 🎉 Hasil Simulasi")

            benar      = sum(1 for q in sim_q
                             if st.session_state.simulasi_answers.get(str(q['id'])) == q['kunci_jawaban'])
            salah      = total_q - benar
            skor_akhir = benar / total_q * 100 if total_q else 0
            lulus      = skor_akhir >= st.session_state.passing_score
            wkt        = int(time.time() - st.session_state.simulasi_start_time)
            mnt        = wkt // 60; dtk = wkt % 60

            # Simpan histori sekali saja
            if not st.session_state._hist_saved:
                st.session_state.simulasi_histori.append({
                    'skor': skor_akhir, 'benar': benar, 'total': total_q, 'waktu': wkt,
                    'label': (f"Sim #{len(st.session_state.simulasi_histori)+1} · "
                              f"{st.session_state.simulasi_kategori[:18]}"),
                })
                st.session_state._hist_saved = True

            if lulus:
                st.success("### ✔️ LULUS")
                components.html(konfetti_js(), height=0)
            else:
                st.error(f"### ❌ BELUM LULUS (min. {int(st.session_state.passing_score)}%)")

            st.markdown(donut_html(benar, total_q), unsafe_allow_html=True)
            st.markdown(metrics_html(
                (f"{skor_akhir:.1f}%", "Skor"),
                (benar, "Benar"),
                (salah, "Salah"),
                (f"{mnt}m {dtk}s", "Waktu"),
            ), unsafe_allow_html=True)

            st.divider()
            ca, cb = st.columns(2)
            with ca:
                if st.button("🔍 Review Jawaban", use_container_width=True, type="primary"):
                    st.session_state.simulasi_show_review = True
                    st.session_state.simulasi_review_idx  = 0
                    st.rerun()
            with cb:
                if st.button("♻️ Simulasi Baru", use_container_width=True):
                    st.session_state.simulasi_started     = False
                    st.session_state.simulasi_submitted   = False
                    st.session_state.simulasi_show_review = False
                    st.session_state._hist_saved          = False
                    st.rerun()

            if salah > 0:
                st.divider()
                if st.button(f"🚨 Latihan {salah} Soal Salah di Tab PG",
                             use_container_width=True):
                    salah_q = [q for q in sim_q
                               if st.session_state.simulasi_answers.get(str(q['id'])) != q['kunci_jawaban']]
                    st.session_state.latihan_pg_salah_list  = random.sample(salah_q, len(salah_q))
                    st.session_state.latihan_pg_salah_mode  = True
                    st.session_state.latihan_pg_answers     = {}
                    st.session_state.latihan_pg_checked     = {}
                    st.session_state.current_q              = 0
                    st.rerun()

        else:
            # Review per soal
            st.markdown("## 🔍 Review Jawaban")
            ridx  = st.session_state.simulasi_review_idx
            q     = sim_q[ridx]
            n_bt  = sum(1 for qq in sim_q
                        if st.session_state.simulasi_answers.get(str(qq['id'])) == qq['kunci_jawaban'])

            st.caption(f"Soal {ridx+1}/{total_q}  |  Benar: {n_bt}/{total_q}")
            st.markdown(prog_html((ridx+1)/total_q), unsafe_allow_html=True)

            jaw   = st.session_state.simulasi_answers.get(str(q['id']))
            kunci = q['kunci_jawaban']

            if jaw == kunci:
                st.success(f"Soal {ridx+1} — **Benar ✔️**")
            else:
                st.error(f"Soal {ridx+1} — **Salah ❌**")

            kat_label = kategori_soal(q)
            st.markdown(f'<span class="tag">{kat_label}</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="q-card"><strong>{q["pertanyaan"]}</strong></div>',
                        unsafe_allow_html=True)

            for key, teks in q['opsi'].items():
                if key == kunci and key == jaw:
                    st.markdown(f'<div class="opsi-item opsi-benar">✔️ {key}. {teks} ← Jawaban Anda (Benar)</div>',
                                unsafe_allow_html=True)
                elif key == kunci:
                    st.markdown(f'<div class="opsi-item opsi-benar">✔️ {key}. {teks} ← Kunci Jawaban</div>',
                                unsafe_allow_html=True)
                elif key == jaw:
                    st.markdown(f'<div class="opsi-item opsi-salah">❌ {key}. {teks} ← Jawaban Anda</div>',
                                unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="opsi-item">{key}. {teks}</div>',
                                unsafe_allow_html=True)

            st.divider()
            r1, r2, r3 = st.columns([1, 2, 1])
            with r1:
                if ridx > 0:
                    if st.button("◀", use_container_width=True, key="rv_p"):
                        st.session_state.simulasi_review_idx -= 1
                        st.rerun()
            with r2:
                if st.button("◀ Kembali ke Hasil", use_container_width=True, key="rv_b"):
                    st.session_state.simulasi_show_review = False
                    st.rerun()
            with r3:
                if ridx < total_q - 1:
                    if st.button("▶", use_container_width=True, key="rv_n"):
                        st.session_state.simulasi_review_idx += 1
                        st.rerun()

    # ── Ujian berlangsung ─────────────────────────────────────────
    else:
        total_q  = len(sim_q)
        dur_dtk  = DURASI_OPSI.get(st.session_state.simulasi_durasi_label, 7200)
        idx      = min(st.session_state.current_q, total_q - 1)
        q        = sim_q[idx]

        elapsed    = int(time.time() - st.session_state.simulasi_start_time)
        sisa_waktu = max(0, dur_dtk - elapsed)

        if sisa_waktu == 0:
            st.session_state.simulasi_submitted = True
            st.rerun()

        st.markdown(f"## Soal {idx+1} / {total_q}")
        st.markdown(prog_html((idx+1)/total_q), unsafe_allow_html=True)

        timer_html = f"""
        <div style="background:rgba(239,68,68,0.08);border-left:4px solid #ef4444;
                    padding:8px 14px;border-radius:8px;margin-bottom:8px;">
          <span style="font-size:.85rem;font-weight:600;">⏱️ Sisa: </span>
          <span id="clk" style="font-size:1rem;font-weight:700;color:#ef4444">--:--</span>
        </div>
        <script>
        var tL={sisa_waktu},el=document.getElementById('clk');
        var tm=setInterval(function(){{
          if(tL<=0){{clearInterval(tm);el.innerHTML='⚠️ HABIS!';return;}}
          var m=Math.floor(tL/60),s=tL%60;
          el.innerHTML=(m<10?'0':'')+m+':'+(s<10?'0':'')+s;
          tL--;
        }},1000);
        </script>"""
        components.html(timer_html, height=50)

        kat_label = kategori_soal(q)
        st.markdown(f'<span class="tag">{kat_label}</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="q-card"><strong>{q["pertanyaan"]}</strong></div>',
                    unsafe_allow_html=True)

        opsi_keys = list(q['opsi'].keys())
        saved_ans = st.session_state.simulasi_answers.get(str(q['id']))
        def_idx   = opsi_keys.index(saved_ans) if saved_ans in opsi_keys else None

        pilihan = st.radio("", opsi_keys,
                           format_func=lambda x: f"{x}. {q['opsi'][x]}",
                           key=f"sim_r_{idx}_{q['id']}", index=def_idx,
                           label_visibility="collapsed")
        if pilihan:
            st.session_state.simulasi_answers[str(q['id'])] = pilihan

        n_dijawab = len(st.session_state.simulasi_answers)
        n_belum   = total_q - n_dijawab
        st.caption(f"Dijawab: {n_dijawab}/{total_q}")
        st.divider()

        s1, s2, s3 = st.columns([1, 2, 1])
        with s1:
            if idx > 0:
                if st.button("◀", use_container_width=True, key="sim_p"):
                    st.session_state.current_q -= 1
                    st.rerun()
        with s2:
            if st.button(f"📥 Kumpulkan ({n_dijawab}/{total_q})",
                         use_container_width=True, type="primary", key="sim_k"):
                if n_belum > 0:
                    st.session_state.sim_confirm_kumpul = True
                else:
                    st.session_state.simulasi_submitted = True
                    st.rerun()
        with s3:
            if idx < total_q - 1:
                if st.button("▶", use_container_width=True, key="sim_n"):
                    st.session_state.current_q += 1
                    st.rerun()

        # Konfirmasi kumpul
        if st.session_state.sim_confirm_kumpul:
            st.warning(f"⚠️ **{n_belum} soal** belum dijawab. Yakin ingin mengumpulkan?")
            ck1, ck2 = st.columns(2)
            with ck1:
                if st.button("✔️ Ya, Kumpulkan", type="primary",
                             use_container_width=True, key="sim_ya"):
                    st.session_state.simulasi_submitted   = True
                    st.session_state.sim_confirm_kumpul   = False
                    st.rerun()
            with ck2:
                if st.button("← Kembali", use_container_width=True, key="sim_batal"):
                    st.session_state.sim_confirm_kumpul = False
                    st.rerun()

        # Peta soal
        with st.expander("🗺️ Peta Soal", expanded=False):
            cpp  = 10
            rows = [sim_q[i:i+cpp] for i in range(0, total_q, cpp)]
            for rs, row in enumerate(rows):
                cols = st.columns(cpp)
                for cp, soal in enumerate(row):
                    si   = rs * cpp + cp
                    djwb = str(soal['id']) in st.session_state.simulasi_answers
                    lbl  = f"{'✓' if djwb else '○'}{si+1}"
                    with cols[cp]:
                        if st.button(lbl, key=f"pt_{si}", use_container_width=True):
                            st.session_state.current_q = si
                            st.rerun()

# ══════════════════════════════════════════════════════════════════
# TAB 5 — BOOKMARK
# ══════════════════════════════════════════════════════════════════
with tab_bm:
    st.markdown("## 🔖 Soal Bookmark")

    bm_ids   = st.session_state.bookmarks
    bm_ids_e = st.session_state.bookmarks_essay

    if not bm_ids and not bm_ids_e:
        st.info("Belum ada soal yang di-bookmark.\n\n"
                "Klik ☆ pada soal di Tab **Latihan PG** atau Tab **Essay**.")
    else:
        total_bm = len(bm_ids) + len(bm_ids_e)
        c_info, c_clear = st.columns([3, 1])
        with c_info:
            st.caption(f"{total_bm} soal di-bookmark "
                       f"({len(bm_ids)} PG, {len(bm_ids_e)} Essay)")
        with c_clear:
            if st.button("🗑️ Hapus Semua", key="bm_clear_all", use_container_width=True):
                st.session_state.bookmarks       = set()
                st.session_state.bookmarks_essay = set()
                st.rerun()

        # ── Bagian PG ──────────────────────────────────────────────
        if bm_ids:
            st.markdown("### 📝 Pilihan Ganda")
            bm_soal = [q for q in soal_pg if q['id'] in bm_ids]
            for q in bm_soal:
                kat_label = kategori_soal(q)
                with st.expander(f"[{kat_label}] {q['pertanyaan'][:75]}..."):
                    for k, v in q['opsi'].items():
                        if k == q['kunci_jawaban']:
                            st.markdown(f'<div class="opsi-item opsi-benar">✔️ {k}. {v}</div>',
                                        unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="opsi-item">{k}. {v}</div>',
                                        unsafe_allow_html=True)
                    st.caption(f"Kunci: **{q['kunci_jawaban']}**")
                    if st.button("🗑️ Hapus Bookmark", key=f"bm_del_{q['id']}"):
                        st.session_state.bookmarks.discard(q['id'])
                        st.rerun()

        # ── Bagian Essay ───────────────────────────────────────────
        if bm_ids_e:
            st.markdown("### ✏️ Essay")
            bm_essay = [q for q in soal_essay if q['id'] in bm_ids_e]
            for q in bm_essay:
                kat_label = q.get('paket', 'Umum')
                with st.expander(f"[{kat_label}] {q['pertanyaan'][:75]}..."):
                    jawaban_md = format_jawaban(q['referensi_jawaban'])
                    st.markdown(
                        f'''<div style="background:rgba(59,130,246,0.07);border-left:4px solid #3b82f6;
                        border-radius:0 10px 10px 0;padding:1.15rem 1.35rem;margin:0.3rem 0 0.6rem">
                        <div style="font-weight:600;color:#3b82f6;margin-bottom:0.55rem;font-size:1.1rem">
                        📖 Referensi Jawaban:</div>
                        <div style="line-height:1.75;white-space:pre-line;font-size:1.08rem">{jawaban_md}</div>
                        </div>''',
                        unsafe_allow_html=True
                    )
                    if st.button("🗑️ Hapus Bookmark", key=f"bm_del_essay_{q['id']}"):
                        st.session_state.bookmarks_essay.discard(q['id'])
                        st.rerun()
