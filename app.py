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

SEMUA_KATEGORI  = sorted(set(q.get('kategori', 'Umum') for q in soal_pg))
JUMLAH_OPSI_SIM = [50, 75, 100]
DURASI_OPSI     = {"60 menit": 3600, "90 menit": 5400, "120 menit": 7200}
PASSING_SCORE   = 70.0

# ══════════════════════════════════════════════════════════════════
# 3. STATE
# ══════════════════════════════════════════════════════════════════
def init_state():
    defaults = {
        'dark_mode': False,
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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ══════════════════════════════════════════════════════════════════
# 4. CSS
# ══════════════════════════════════════════════════════════════════
dark = st.session_state.dark_mode

BG        = "#0e1117"       if dark else "#f5f7fa"
CARD_BG   = "#1e2130"       if dark else "#ffffff"
TEXT      = "#e0e0e0"       if dark else "#1a1a2e"
SUB_TEXT  = "#9aa0b0"       if dark else "#6b7280"
BORDER    = "#2e3250"       if dark else "#e5e7eb"
ACCENT    = "#4f8ef7"       if dark else "#3b82f6"
SUCCESS   = "#2e7d32"       if dark else "#16a34a"
ERROR_C   = "#b71c1c"       if dark else "#dc2626"
TAG_BG    = "#2e3250"       if dark else "#eff6ff"
SUC_BG    = "#1b3a1f"       if dark else "#e8f5e9"
ERR_BG    = "#3a1a1a"       if dark else "#ffebee"

st.markdown(f"""
<style>
html, body, [data-testid="stAppViewContainer"] {{
    background-color: {BG} !important;
    color: {TEXT};
}}
[data-testid="stSidebar"] {{
    background-color: {CARD_BG} !important;
    border-right: 1px solid {BORDER};
}}
/* ─ Sidebar rata tengah ─ */
[data-testid="stSidebar"] > div:first-child {{
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding-top: 1.2rem;
}}
[data-testid="stSidebar"] .stMetric,
[data-testid="stSidebar"] .stMetric label,
[data-testid="stSidebar"] .stMetric > div {{
    text-align: center !important;
    justify-content: center !important;
}}
/* ─ Font responsive ─ */
h1 {{ font-size: clamp(1.25rem, 4vw, 1.9rem) !important; }}
h2 {{ font-size: clamp(1.1rem, 3.5vw, 1.55rem) !important; }}
h3 {{ font-size: clamp(0.95rem, 3vw, 1.25rem) !important; }}
[data-testid="stTabs"] button p {{
    font-size: clamp(0.65rem, 2vw, 0.88rem) !important;
    white-space: nowrap;
}}
/* ─ Card ─ */
.q-card {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.9rem;
    box-shadow: 0 2px 14px rgba(0,0,0,{0.18 if dark else 0.07});
    font-size: clamp(0.88rem, 2.5vw, 1rem);
    line-height: 1.55;
}}
/* ─ Progress ─ */
.prog-wrap {{
    background: {BORDER};
    border-radius: 99px;
    height: 7px;
    margin: 0.35rem 0 0.65rem;
    overflow: hidden;
}}
.prog-bar {{
    height: 7px;
    border-radius: 99px;
    background: linear-gradient(90deg, {ACCENT}, #7c3aed);
    transition: width 0.45s cubic-bezier(.4,0,.2,1);
}}
/* ─ Metric row ─ */
.metric-row {{
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
    justify-content: center;
    margin: 0.8rem 0;
}}
.metric-box {{
    background: {CARD_BG};
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 0.75rem 1rem;
    text-align: center;
    flex: 1 1 80px;
    min-width: 75px;
    box-shadow: 0 1px 6px rgba(0,0,0,{0.12 if dark else 0.05});
}}
.metric-box .mval {{
    font-size: clamp(1.2rem, 4vw, 1.55rem);
    font-weight: 700;
    color: {ACCENT};
    line-height: 1.1;
}}
.metric-box .mlbl {{
    font-size: 0.68rem;
    color: {SUB_TEXT};
    margin-top: 0.15rem;
}}
/* ─ Tag ─ */
.tag {{
    display: inline-block;
    background: {TAG_BG};
    color: {ACCENT};
    border-radius: 99px;
    font-size: 0.68rem;
    font-weight: 600;
    padding: 0.12rem 0.55rem;
    margin-bottom: 0.45rem;
}}
/* ─ Opsi ─ */
.opsi-item {{
    display: block;
    padding: 0.55rem 0.85rem;
    border-radius: 9px;
    margin-bottom: 0.3rem;
    border: 1.5px solid {BORDER};
    background: {CARD_BG};
    font-size: clamp(0.82rem, 2.3vw, 0.95rem);
    transition: all 0.15s;
}}
.opsi-benar {{
    border-color: {SUCCESS} !important;
    background: {SUC_BG} !important;
    color: {SUCCESS} !important;
    font-weight: 600;
}}
.opsi-salah {{
    border-color: {ERROR_C} !important;
    background: {ERR_BG} !important;
    color: {ERROR_C} !important;
    font-weight: 600;
}}
/* ─ Histori ─ */
.skor-item {{
    display: flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.38rem 0.6rem;
    border-radius: 8px;
    background: {CARD_BG};
    border: 1px solid {BORDER};
    margin-bottom: 0.35rem;
    font-size: 0.82rem;
}}
.skor-badge {{ font-weight: 700; font-size: 0.9rem; min-width: 48px; text-align: right; }}
.c-ok  {{ color: {SUCCESS}; }}
.c-err {{ color: {ERROR_C}; }}
/* ─ Donut ─ */
.donut-wrap {{ display:flex; justify-content:center; margin: 0.8rem 0; }}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
def filter_pg(kat):
    if kat == "Semua Kategori":
        return soal_pg
    return [q for q in soal_pg if q.get('kategori', 'Umum') == kat]

def prog_html(pct, label=""):
    return (f'<div style="font-size:.7rem;color:{SUB_TEXT};margin-bottom:2px">{label}</div>'
            f'<div class="prog-wrap"><div class="prog-bar" style="width:{pct*100:.1f}%"></div></div>')

def metrics_html(*items):
    boxes = "".join(
        f'<div class="metric-box"><div class="mval">{v}</div><div class="mlbl">{l}</div></div>'
        for v, l in items)
    return f'<div class="metric-row">{boxes}</div>'

def donut_html(benar, total):
    salah = total - benar
    pct   = benar / total * 100 if total else 0
    R     = 68
    circ  = 2 * 3.14159 * R
    dash  = circ * benar / total if total else 0
    green = "#22c55e"; red = "#ef4444"
    return f"""
    <div class="donut-wrap">
      <svg width="170" height="170" viewBox="0 0 170 170">
        <circle cx="85" cy="85" r="{R}" fill="none" stroke="{red}" stroke-width="20"/>
        <circle cx="85" cy="85" r="{R}" fill="none" stroke="{green}" stroke-width="20"
                stroke-dasharray="{dash:.1f} {circ:.1f}"
                stroke-dashoffset="{circ/4:.1f}" stroke-linecap="round"/>
        <text x="85" y="80" text-anchor="middle" font-size="21"
              font-weight="700" fill="{TEXT}">{pct:.0f}%</text>
        <text x="85" y="100" text-anchor="middle" font-size="10" fill="{SUB_TEXT}">Skor Akhir</text>
        <text x="85" y="115" text-anchor="middle" font-size="10" fill="{SUB_TEXT}">{benar}/{total} benar</text>
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
# 5. SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center;padding:0.3rem 0 0.5rem">
      <div style="font-size:1.9rem">🎓</div>
      <div style="font-weight:700;font-size:1.05rem;margin-top:0.25rem;color:{TEXT}">CAT MHI</div>
      <div style="font-size:0.7rem;color:{SUB_TEXT};margin-top:0.1rem;line-height:1.4">
        Mediator Hubungan Industrial<br>Ahli Madya
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown(metrics_html(
        (len(soal_pg),   "Soal PG"),
        (len(soal_essay),"Essay"),
        (st.session_state.simulasi_jumlah, "Simulasi"),
    ), unsafe_allow_html=True)

    st.divider()

    dm_lbl = "☀️ Mode Terang" if dark else "🌙 Mode Gelap"
    if st.button(dm_lbl, use_container_width=True, key="dm_toggle"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    bm_count = len(st.session_state.bookmarks)
    if bm_count:
        st.markdown(f'<div style="text-align:center;font-size:0.75rem;color:{SUB_TEXT};'
                    f'margin-top:0.4rem">🔖 {bm_count} soal bookmark</div>',
                    unsafe_allow_html=True)

    if st.session_state.simulasi_histori:
        st.divider()
        st.markdown(f'<div style="text-align:center;font-size:0.73rem;font-weight:600;'
                    f'color:{SUB_TEXT}">Histori Terakhir</div>', unsafe_allow_html=True)
        for h in st.session_state.simulasi_histori[-3:]:
            lulus = h['skor'] >= PASSING_SCORE
            warna = SUCCESS if lulus else ERROR_C
            icon  = "✅" if lulus else "❌"
            st.markdown(f"""
            <div class="skor-item">
              <span>{icon}</span>
              <span style="flex:1;color:{SUB_TEXT};font-size:.72rem">{h.get('label','')}</span>
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
    kat_counts = Counter(q.get('kategori', 'Umum') for q in soal_pg)
    for kat, cnt in sorted(kat_counts.items(), key=lambda x: -x[1]):
        pct = cnt / len(soal_pg)
        st.markdown(prog_html(pct, f"{kat} ({cnt})"), unsafe_allow_html=True)

    st.divider()
    st.markdown(f"""
**Panduan:**
- **Latihan PG** — soal per soal, filter kategori, ⭐ bookmark, cek jawaban
- **Latihan Essay** — tulis jawaban lalu tampilkan referensi
- **Simulasi** — pilih jumlah soal & durasi, timer otomatis, konfirmasi sebelum kumpul
- Ambang batas lulus: **{int(PASSING_SCORE)}%**
    """)

# ══════════════════════════════════════════════════════════════════
# TAB 2 — LATIHAN PILIHAN GANDA
# ══════════════════════════════════════════════════════════════════
with tab_pg:
    st.markdown("## 📝 Latihan Pilihan Ganda")

    c_kat, c_rst = st.columns([3, 1])
    with c_kat:
        kat_pg = st.selectbox("Kategori", ["Semua Kategori"] + SEMUA_KATEGORI,
                              key="pg_sel_kat", label_visibility="collapsed")
    with c_rst:
        if st.button("🔀 Acak", use_container_width=True, key="pg_reset"):
            pool = filter_pg(kat_pg)
            st.session_state.latihan_pg_questions = random.sample(pool, len(pool))
            st.session_state.latihan_pg_answers   = {}
            st.session_state.latihan_pg_checked   = {}
            st.session_state.current_q            = 0
            st.session_state.latihan_pg_salah_mode = False
            st.rerun()

    if not st.session_state.latihan_pg_questions:
        pool = filter_pg(kat_pg)
        st.session_state.latihan_pg_questions = random.sample(pool, len(pool))

    # Mode soal salah
    if st.session_state.latihan_pg_salah_mode and st.session_state.latihan_pg_salah_list:
        questions = st.session_state.latihan_pg_salah_list
        st.info(f"🔁 Mode Soal Salah — {len(questions)} soal")
        if st.button("← Kembali ke Semua Soal", key="pg_back"):
            st.session_state.latihan_pg_salah_mode = False
            st.session_state.current_q = 0
            st.rerun()
    else:
        questions = st.session_state.latihan_pg_questions

    total_q = len(questions)
    idx     = min(st.session_state.current_q, total_q - 1)
    q       = questions[idx]

    # Statistik
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

    st.markdown(prog_html((idx+1)/total_q, f"Soal {idx+1} dari {total_q}"), unsafe_allow_html=True)

    # Header soal + bookmark
    bm_id  = q['id']
    is_bm  = bm_id in st.session_state.bookmarks
    c_q, c_bm = st.columns([11, 1])
    with c_bm:
        bm_icon = "⭐" if is_bm else "☆"
        if st.button(bm_icon, key=f"bm_pg_{idx}_{bm_id}", help="Bookmark"):
            if is_bm:
                st.session_state.bookmarks.discard(bm_id)
            else:
                st.session_state.bookmarks.add(bm_id)
            st.rerun()

    kat_label = q.get('kategori', 'Umum')
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
                cls = "opsi-item opsi-benar"; icon = "✅ "
            elif k == kunci:
                cls = "opsi-item opsi-benar"; icon = "✅ "
            elif k == saved:
                cls = "opsi-item opsi-salah"; icon = "❌ "
            else:
                cls = "opsi-item"; icon = ""
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
        if st.button("✅ Cek Jawaban", type="primary", key=f"pg_cek_{idx}"):
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
        if st.button(f"🔁 Latihan Ulang {n_salah} Soal Salah",
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

    c_ie, c_re = st.columns([3, 1])
    with c_re:
        if st.button("🔀 Acak", use_container_width=True, key="essay_reset"):
            st.session_state.latihan_essay_questions = random.sample(soal_essay, len(soal_essay))
            st.session_state.latihan_essay_shown     = {}
            st.session_state.current_q               = 0
            st.rerun()

    if not st.session_state.latihan_essay_questions:
        st.session_state.latihan_essay_questions = random.sample(soal_essay, len(soal_essay))

    qs_e  = st.session_state.latihan_essay_questions
    tot_e = len(qs_e)
    idx_e = min(st.session_state.current_q, tot_e - 1)
    qe    = qs_e[idx_e]

    with c_ie:
        st.caption(f"Referensi ditampilkan: {len(st.session_state.latihan_essay_shown)}/{tot_e}")

    st.markdown(prog_html((idx_e+1)/tot_e, f"Soal {idx_e+1} dari {tot_e}"), unsafe_allow_html=True)
    st.markdown(f'<div class="q-card"><strong>{qe["pertanyaan"]}</strong></div>',
                unsafe_allow_html=True)

    st.text_area("Jawaban Anda:", height=130, key=f"essay_in_{idx_e}",
                 label_visibility="collapsed", placeholder="Tulis jawaban Anda di sini...")

    if st.button("📖 Tampilkan Referensi", type="primary", key=f"essay_ref_{idx_e}"):
        st.session_state.latihan_essay_shown[idx_e] = True

    if st.session_state.latihan_essay_shown.get(idx_e):
        st.info("**Referensi Jawaban:**\n\n" + qe['referensi_jawaban'])

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
        st.markdown(f'<div class="q-card">', unsafe_allow_html=True)

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

        kat_sim = st.selectbox("Kategori", ["Semua Kategori"] + SEMUA_KATEGORI, key="sim_kat")
        st.session_state.simulasi_kategori = kat_sim
        st.markdown('</div>', unsafe_allow_html=True)

        pool_sim = filter_pg(kat_sim)
        n_sim    = min(jml, len(pool_sim))
        st.markdown(metrics_html(
            (len(pool_sim), f"Tersedia"),
            (n_sim,         "Diambil"),
            (dur_lbl.replace(" menit", "m"), "Durasi"),
            (f"{int(PASSING_SCORE)}%", "Min. Lulus"),
        ), unsafe_allow_html=True)

        st.warning("⚠️ Timer langsung berjalan setelah klik Mulai.")

        if st.button("▶️ Mulai Simulasi", type="primary", use_container_width=True, key="sim_mulai"):
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

        # Histori
        if st.session_state.simulasi_histori:
            st.divider()
            st.markdown("#### 📈 Histori Skor")
            for h in reversed(st.session_state.simulasi_histori):
                lulus = h['skor'] >= PASSING_SCORE
                icon  = "✅" if lulus else "❌"
                warna = SUCCESS if lulus else ERROR_C
                mnt   = h['waktu'] // 60; dtk = h['waktu'] % 60
                st.markdown(f"""
                <div class="skor-item">
                  <span>{icon}</span>
                  <span style="flex:1">{h.get('label','')}</span>
                  <span style="color:{SUB_TEXT};font-size:.75rem">{h['benar']}/{h['total']} &nbsp; {mnt}m{dtk}s</span>
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
            lulus      = skor_akhir >= PASSING_SCORE
            wkt        = int(time.time() - st.session_state.simulasi_start_time)
            mnt        = wkt // 60; dtk = wkt % 60

            # Simpan histori (sekali saja)
            if not st.session_state._hist_saved:
                st.session_state.simulasi_histori.append({
                    'skor': skor_akhir, 'benar': benar, 'total': total_q, 'waktu': wkt,
                    'label': (f"Sim #{len(st.session_state.simulasi_histori)+1} · "
                              f"{st.session_state.simulasi_kategori[:18]}"),
                })
                st.session_state._hist_saved = True

            if lulus:
                st.success("### ✅ LULUS")
                components.html(konfetti_js(), height=0)
            else:
                st.error(f"### ❌ BELUM LULUS (min. {int(PASSING_SCORE)}%)")

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
                if st.button("🔄 Simulasi Baru", use_container_width=True):
                    st.session_state.simulasi_started     = False
                    st.session_state.simulasi_submitted   = False
                    st.session_state.simulasi_show_review = False
                    st.session_state._hist_saved          = False
                    st.rerun()

            if salah > 0:
                st.divider()
                if st.button(f"🔁 Latihan {salah} Soal Salah di Tab PG",
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
            ridx     = st.session_state.simulasi_review_idx
            q        = sim_q[ridx]
            n_bt     = sum(1 for qq in sim_q
                           if st.session_state.simulasi_answers.get(str(qq['id'])) == qq['kunci_jawaban'])

            st.caption(f"Soal {ridx+1}/{total_q}  |  Benar: {n_bt}/{total_q}")
            st.markdown(prog_html((ridx+1)/total_q), unsafe_allow_html=True)

            jaw  = st.session_state.simulasi_answers.get(str(q['id']))
            kunci = q['kunci_jawaban']

            if jaw == kunci:
                st.success(f"Soal {ridx+1} — **Benar ✅**")
            else:
                st.error(f"Soal {ridx+1} — **Salah ❌**")

            kat_label = q.get('kategori', 'Umum')
            st.markdown(f'<span class="tag">{kat_label}</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="q-card"><strong>{q["pertanyaan"]}</strong></div>',
                        unsafe_allow_html=True)

            for key, teks in q['opsi'].items():
                if key == kunci and key == jaw:
                    st.markdown(f'<div class="opsi-item opsi-benar">✅ {key}. {teks} ← Jawaban Anda (Benar)</div>',
                                unsafe_allow_html=True)
                elif key == kunci:
                    st.markdown(f'<div class="opsi-item opsi-benar">✅ {key}. {teks} ← Kunci Jawaban</div>',
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
        <div style="background:#fff3cd;border-left:5px solid #ef4444;padding:8px 14px;
                    border-radius:8px;margin-bottom:8px;">
          <span style="font-size:.85rem;font-weight:600;color:#555">⏱️ Sisa: </span>
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

        kat_label = q.get('kategori', 'Umum')
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
                if st.button("✅ Ya, Kumpulkan", type="primary",
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
                    si    = rs * cpp + cp
                    djwb  = str(soal['id']) in st.session_state.simulasi_answers
                    lbl   = f"{'✓' if djwb else '○'}{si+1}"
                    with cols[cp]:
                        if st.button(lbl, key=f"pt_{si}", use_container_width=True):
                            st.session_state.current_q = si
                            st.rerun()

# ══════════════════════════════════════════════════════════════════
# TAB 5 — BOOKMARK
# ══════════════════════════════════════════════════════════════════
with tab_bm:
    st.markdown("## 🔖 Soal Bookmark")

    bm_ids = st.session_state.bookmarks
    if not bm_ids:
        st.info("Belum ada soal yang di-bookmark.\nKlik ☆ pada soal di Tab Latihan PG.")
    else:
        bm_soal = [q for q in soal_pg if q['id'] in bm_ids]
        st.caption(f"{len(bm_soal)} soal di-bookmark")

        if st.button("🗑️ Hapus Semua", key="bm_clear_all"):
            st.session_state.bookmarks = set()
            st.rerun()

        for q in bm_soal:
            kat_label = q.get('kategori', 'Umum')
            with st.expander(f"[{kat_label}] {q['pertanyaan'][:75]}..."):
                for k, v in q['opsi'].items():
                    if k == q['kunci_jawaban']:
                        st.markdown(f'<div class="opsi-item opsi-benar">✅ {k}. {v}</div>',
                                    unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="opsi-item">{k}. {v}</div>',
                                    unsafe_allow_html=True)
                st.caption(f"Kunci: **{q['kunci_jawaban']}**")
                if st.button("🗑️ Hapus Bookmark", key=f"bm_del_{q['id']}"):
                    st.session_state.bookmarks.discard(q['id'])
                    st.rerun()
