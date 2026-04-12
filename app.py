import streamlit as st
import streamlit.components.v1 as components
import json
import time
import random

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="CAT MHI", page_icon="🎓", layout="centered")

# ==========================================
# 2. LOAD DATA
# ==========================================
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
    st.error("Gagal memuat database soal. Pastikan file soal_pg.json dan soal_essay.json tersedia.")
    st.stop()

# ==========================================
# 3. KONSTANTA
# ==========================================
JUMLAH_SOAL_SIMULASI = 100
WAKTU_UJIAN_DETIK    = 7200   # 2 jam
PASSING_SCORE        = 70.0   # ambang batas lulus (%)

# ==========================================
# 4. STATE MANAGEMENT
# ==========================================
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

        # Latihan PG
        'latihan_pg_questions': [],
        'latihan_pg_answers': {},
        'latihan_pg_checked': {},

        # Latihan Essay
        'latihan_essay_questions': [],
        'latihan_essay_shown': {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ==========================================
# 5. SIDEBAR — info saja, tanpa navigasi
# ==========================================
with st.sidebar:
    st.title("🎓 CAT MHI")
    st.caption("Simulasi Uji Kompetensi")
    st.divider()
    st.metric("Soal PG",       len(soal_pg))
    st.metric("Soal Essay",    len(soal_essay))
    st.metric("Soal Simulasi", min(JUMLAH_SOAL_SIMULASI, len(soal_pg)))
    st.divider()
    st.caption("Mediator Hubungan Industrial Ahli Madya.")

# ==========================================
# 6. NAVIGASI TABS — di area utama
# ==========================================
tab_beranda, tab_pg, tab_essay, tab_simulasi = st.tabs([
    "🏠 Beranda",
    "📝 Latihan PG",
    "✏️ Latihan Essay",
    "🚀 Simulasi Ujian",
])


# ══════════════════════════════════════════
# TAB 1 — BERANDA
# ══════════════════════════════════════════
with tab_beranda:
    st.title("Simulasi Ujikom MHI")
    st.write("Aplikasi latihan soal **Pilihan Ganda** dan **Essay** untuk persiapan Uji Kompetensi.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Soal PG",       len(soal_pg))
    col2.metric("Soal Essay",    len(soal_essay))
    col3.metric("Soal Simulasi", min(JUMLAH_SOAL_SIMULASI, len(soal_pg)))

    st.divider()
    st.markdown(f"""
    **Panduan Penggunaan:**
    - **Latihan PG** — Kerjakan soal satu per satu, cek jawaban langsung, navigasi bebas.
    - **Latihan Essay** — Baca soal, tulis jawaban sendiri, lalu tampilkan referensi untuk evaluasi diri.
    - **Simulasi Ujian** — {min(JUMLAH_SOAL_SIMULASI, len(soal_pg))} soal acak dengan timer 2 jam. \
Jawaban dikunci setelah dikumpulkan. Ambang batas lulus: **{int(PASSING_SCORE)}%**.
    """)
    st.info("💡 Pilih tab di atas untuk mulai. Urutan soal diacak setiap kali sesi dimulai.")


# ══════════════════════════════════════════
# TAB 2 — LATIHAN PILIHAN GANDA
# ══════════════════════════════════════════
with tab_pg:
    st.title("📝 Latihan Pilihan Ganda")

    col_info, col_reset = st.columns([3, 1])
    with col_reset:
        if st.button("⚡ Acak Ulang", use_container_width=True, key="pg_reset"):
            st.session_state.latihan_pg_questions = random.sample(soal_pg, len(soal_pg))
            st.session_state.latihan_pg_answers   = {}
            st.session_state.latihan_pg_checked   = {}
            st.session_state.current_q            = 0
            st.rerun()

    if not st.session_state.latihan_pg_questions:
        st.session_state.latihan_pg_questions = random.sample(soal_pg, len(soal_pg))

    questions = st.session_state.latihan_pg_questions
    total_q   = len(questions)
    idx       = st.session_state.current_q

    if idx >= total_q:
        idx = 0
        st.session_state.current_q = 0

    q = questions[idx]

    with col_info:
        n_checked = len(st.session_state.latihan_pg_checked)
        n_benar   = sum(
            1 for i in st.session_state.latihan_pg_checked
            if st.session_state.latihan_pg_answers.get(i) == questions[i]['kunci_jawaban']
        )
        st.caption(f"Sudah dicek: {n_checked} soal  |  Benar: {n_benar}")

    st.progress((idx + 1) / total_q)
    st.write(f"**Soal {idx + 1} dari {total_q}**")
    st.write("### " + q['pertanyaan'])

    saved       = st.session_state.latihan_pg_answers.get(idx)
    opsi_keys   = list(q['opsi'].keys())
    default_idx = opsi_keys.index(saved) if saved in opsi_keys else 0

    pilihan = st.radio(
        "Pilih jawaban:",
        opsi_keys,
        format_func=lambda x: f"{x}. {q['opsi'][x]}",
        key=f"pg_radio_{idx}",
        index=default_idx,
    )
    st.session_state.latihan_pg_answers[idx] = pilihan

    sudah_dicek = st.session_state.latihan_pg_checked.get(idx, False)
    if st.button("🎯 Cek Jawaban", type="primary", key=f"pg_cek_{idx}"):
        st.session_state.latihan_pg_checked[idx] = True
        sudah_dicek = True

    if sudah_dicek:
        kunci = q['kunci_jawaban']
        if pilihan == kunci:
            st.success(f"**Benar!** Kunci: **{kunci}. {q['opsi'][kunci]}**")
        else:
            st.error(f"**Salah.** Jawaban Anda: {pilihan}. {q['opsi'].get(pilihan, '')}")
            st.info(f"Kunci Jawaban: **{kunci}. {q['opsi'][kunci]}**")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if idx > 0:
            if st.button("◀ Sebelumnya", use_container_width=True, key="pg_prev"):
                st.session_state.current_q -= 1
                st.rerun()
    with col2:
        if idx < total_q - 1:
            if st.button("Selanjutnya ▶", use_container_width=True, key="pg_next"):
                st.session_state.current_q += 1
                st.rerun()


# ══════════════════════════════════════════
# TAB 3 — LATIHAN ESSAY
# ══════════════════════════════════════════
with tab_essay:
    st.title("✏️ Latihan Essay")

    col_info_e, col_reset_e = st.columns([3, 1])
    with col_reset_e:
        if st.button("⚡ Acak Ulang", use_container_width=True, key="essay_reset"):
            st.session_state.latihan_essay_questions = random.sample(soal_essay, len(soal_essay))
            st.session_state.latihan_essay_shown     = {}
            st.session_state.current_q               = 0
            st.rerun()

    if not st.session_state.latihan_essay_questions:
        st.session_state.latihan_essay_questions = random.sample(soal_essay, len(soal_essay))

    questions_e = st.session_state.latihan_essay_questions
    total_e     = len(questions_e)
    idx_e       = st.session_state.current_q

    if idx_e >= total_e:
        idx_e = 0
        st.session_state.current_q = 0

    qe = questions_e[idx_e]

    with col_info_e:
        n_shown = len(st.session_state.latihan_essay_shown)
        st.caption(f"Referensi sudah ditampilkan: {n_shown} soal")

    st.progress((idx_e + 1) / total_e)
    st.write(f"**Soal {idx_e + 1} dari {total_e}**")
    st.write("### " + qe['pertanyaan'])

    st.text_area("Ketik jawaban Anda:", height=150, key=f"essay_input_{idx_e}")

    if st.button("📖 Tampilkan Referensi Jawaban", type="primary", key=f"essay_ref_{idx_e}"):
        st.session_state.latihan_essay_shown[idx_e] = True

    if st.session_state.latihan_essay_shown.get(idx_e):
        st.info("**Referensi Jawaban Resmi:**\n\n" + qe['referensi_jawaban'])

    st.divider()

    col1_e, col2_e = st.columns(2)
    with col1_e:
        if idx_e > 0:
            if st.button("◀ Sebelumnya", use_container_width=True, key="essay_prev"):
                st.session_state.current_q -= 1
                st.rerun()
    with col2_e:
        if idx_e < total_e - 1:
            if st.button("Selanjutnya ▶", use_container_width=True, key="essay_next"):
                st.session_state.current_q += 1
                st.rerun()


# ══════════════════════════════════════════
# TAB 4 — SIMULASI UJIAN
# ══════════════════════════════════════════
with tab_simulasi:

    n_sim     = min(JUMLAH_SOAL_SIMULASI, len(soal_pg))
    questions = st.session_state.simulasi_questions

    # ── Belum mulai ───────────────────────────────────────────────────────────
    if not st.session_state.simulasi_started:
        st.title("🚀 Simulasi Ujian")
        st.markdown(f"""
        **Ketentuan Simulasi:**
        - Jumlah soal : **{n_sim} soal** (dipilih acak)
        - Waktu ujian : **120 menit**
        - Ambang lulus: **{int(PASSING_SCORE)}%**
        - Soal **tidak bisa diubah** setelah dikumpulkan
        """)
        st.warning("Pastikan Anda siap sebelum memulai. Timer akan langsung berjalan.")
        if st.button("🚀 Mulai Simulasi", type="primary", use_container_width=True):
            st.session_state.simulasi_started     = True
            st.session_state.simulasi_answers     = {}
            st.session_state.simulasi_submitted   = False
            st.session_state.simulasi_start_time  = time.time()
            st.session_state.simulasi_questions   = random.sample(soal_pg, n_sim)
            st.session_state.current_q            = 0
            st.session_state.simulasi_show_review = False
            st.session_state.simulasi_review_idx  = 0
            st.rerun()

    # ── Hasil & Review ────────────────────────────────────────────────────────
    elif st.session_state.simulasi_submitted:
        total_q = len(questions)

        if not st.session_state.simulasi_show_review:
            st.title("🎉 Hasil Simulasi")

            benar      = sum(1 for q in questions
                             if st.session_state.simulasi_answers.get(str(q['id'])) == q['kunci_jawaban'])
            salah      = total_q - benar
            skor_akhir = (benar / total_q) * 100
            lulus      = skor_akhir >= PASSING_SCORE

            waktu_total = int(time.time() - st.session_state.simulasi_start_time)
            mnt = waktu_total // 60
            dtk = waktu_total % 60

            if lulus:
                st.success(f"### 🎯 LULUS — Skor: {skor_akhir:.1f}%")
            else:
                st.error(f"### ❌ BELUM LULUS — Skor: {skor_akhir:.1f}% (minimum {int(PASSING_SCORE)}%)")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Skor",  f"{skor_akhir:.1f}%")
            c2.metric("Benar", benar)
            c3.metric("Salah", salah)
            c4.metric("Waktu", f"{mnt}m {dtk}s")

            st.divider()
            ca, cb = st.columns(2)
            with ca:
                if st.button("🔍 Review Jawaban", use_container_width=True, type="primary"):
                    st.session_state.simulasi_show_review = True
                    st.session_state.simulasi_review_idx  = 0
                    st.rerun()
            with cb:
                if st.button("⚡ Simulasi Baru", use_container_width=True):
                    st.session_state.simulasi_started     = False
                    st.session_state.simulasi_submitted   = False
                    st.session_state.simulasi_show_review = False
                    st.rerun()

        else:
            # Review per soal
            st.title("🔍 Review Jawaban")
            ridx = st.session_state.simulasi_review_idx
            q    = questions[ridx]

            n_benar_total = sum(1 for qq in questions
                                if st.session_state.simulasi_answers.get(str(qq['id'])) == qq['kunci_jawaban'])
            st.caption(f"Soal {ridx + 1} dari {total_q}  |  Total benar: {n_benar_total}/{total_q}")
            st.progress((ridx + 1) / total_q)

            jawaban_user = st.session_state.simulasi_answers.get(str(q['id']))
            kunci        = q['kunci_jawaban']

            if jawaban_user == kunci:
                st.success(f"**Soal {ridx + 1} — Benar 🎯**")
            else:
                st.error(f"**Soal {ridx + 1} — Salah ❌**")

            st.write("### " + q['pertanyaan'])
            st.divider()

            for key, teks in q['opsi'].items():
                if key == kunci and key == jawaban_user:
                    st.markdown(f"🎯 **{key}. {teks}** ← Jawaban Anda (Benar)")
                elif key == kunci:
                    st.markdown(f"🎯 **{key}. {teks}** ← Kunci Jawaban")
                elif key == jawaban_user:
                    st.markdown(f"❌ ~~{key}. {teks}~~ ← Jawaban Anda")
                else:
                    st.markdown(f"　 {key}. {teks}")

            st.divider()
            r1, r2, r3 = st.columns([1, 2, 1])
            with r1:
                if ridx > 0:
                    if st.button("◀ Sebelumnya", use_container_width=True, key="rev_prev"):
                        st.session_state.simulasi_review_idx -= 1
                        st.rerun()
            with r2:
                if st.button("◀ Kembali ke Hasil", use_container_width=True, key="rev_back"):
                    st.session_state.simulasi_show_review = False
                    st.rerun()
            with r3:
                if ridx < total_q - 1:
                    if st.button("Selanjutnya ▶", use_container_width=True, key="rev_next"):
                        st.session_state.simulasi_review_idx += 1
                        st.rerun()

    # ── Ujian berlangsung ─────────────────────────────────────────────────────
    else:
        total_q = len(questions)
        idx     = st.session_state.current_q
        if idx >= total_q:
            idx = 0
            st.session_state.current_q = 0
        q = questions[idx]

        elapsed_time = int(time.time() - st.session_state.simulasi_start_time)
        sisa_waktu   = max(0, WAKTU_UJIAN_DETIK - elapsed_time)

        if sisa_waktu == 0:
            st.session_state.simulasi_submitted = True
            st.rerun()

        st.title(f"🚀 Simulasi — Soal {idx + 1}/{total_q}")
        st.progress((idx + 1) / total_q)

        timer_html = f"""
        <div style="background:#fff3cd;border-left:5px solid #ff4b4b;padding:10px 16px;
                    border-radius:6px;margin-bottom:8px;">
            <span style="font-size:.95rem;font-weight:600;color:#333;">⏱️ Sisa Waktu: </span>
            <span id="clock" style="font-size:1.1rem;font-weight:700;color:#ff4b4b;">Memuat...</span>
        </div>
        <script>
            var timeLeft = {sisa_waktu};
            var elem = document.getElementById('clock');
            var timerId = setInterval(countdown, 1000);
            function countdown() {{
                if (timeLeft <= 0) {{
                    clearInterval(timerId);
                    elem.innerHTML = "⚠️ WAKTU HABIS!";
                }} else {{
                    var m = Math.floor(timeLeft / 60);
                    var s = timeLeft % 60;
                    elem.innerHTML = (m<10?"0":"") + m + ":" + (s<10?"0":"") + s;
                    timeLeft--;
                }}
            }}
        </script>
        """
        components.html(timer_html, height=60)

        st.write("### " + q['pertanyaan'])

        opsi_keys    = list(q['opsi'].keys())
        saved_answer = st.session_state.simulasi_answers.get(str(q['id']))
        default_idx  = opsi_keys.index(saved_answer) if saved_answer in opsi_keys else None

        pilihan = st.radio(
            label="Pilih jawaban:",
            options=opsi_keys,
            format_func=lambda x: f"{x}. {q['opsi'][x]}",
            key=f"sim_radio_{idx}_{q['id']}",
            index=default_idx,
        )
        if pilihan:
            st.session_state.simulasi_answers[str(q['id'])] = pilihan

        n_dijawab = len(st.session_state.simulasi_answers)
        st.caption(f"Sudah dijawab: {n_dijawab}/{total_q} soal")
        st.divider()

        s1, s2, s3 = st.columns([1, 2, 1])
        with s1:
            if idx > 0:
                if st.button("◀ Sebelumnya", use_container_width=True, key="sim_prev"):
                    st.session_state.current_q -= 1
                    st.rerun()
        with s2:
            if st.button(f"📥 Kumpulkan ({n_dijawab}/{total_q})", use_container_width=True,
                         type="primary", key="sim_kumpul"):
                st.session_state.simulasi_submitted = True
                st.rerun()
        with s3:
            if idx < total_q - 1:
                if st.button("Selanjutnya ▶", use_container_width=True, key="sim_next"):
                    st.session_state.current_q += 1
                    st.rerun()

        # Peta soal
        with st.expander("🗺️ Peta Soal — Navigasi Cepat", expanded=False):
            cols_per_row = 10
            rows = [questions[i:i+cols_per_row] for i in range(0, total_q, cols_per_row)]
            for row_start, row in enumerate(rows):
                cols = st.columns(cols_per_row)
                for col_pos, soal in enumerate(row):
                    soal_idx   = row_start * cols_per_row + col_pos
                    dijawab    = str(soal['id']) in st.session_state.simulasi_answers
                    label_peta = f"{'✓' if dijawab else '○'}{soal_idx + 1}"
                    with cols[col_pos]:
                        if st.button(label_peta, key=f"peta_{soal_idx}", use_container_width=True):
                            st.session_state.current_q = soal_idx
                            st.rerun()
