import streamlit as st
import streamlit.components.v1 as components
import json
import time
import random

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(page_title="CAT MHI - Inayasha", page_icon="🎓", layout="centered")

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
        'mode': 'Beranda',
        'current_q': 0,

        # Simulasi
        'simulasi_answers': {},
        'simulasi_submitted': False,
        'simulasi_start_time': None,
        'simulasi_questions': [],
        'simulasi_review_idx': 0,
        'simulasi_show_review': False,

        # Latihan PG
        'latihan_pg_questions': [],
        'latihan_pg_answers': {},   # simpan jawaban per soal {idx: pilihan}
        'latihan_pg_checked': {},   # soal yang sudah dicek {idx: True}

        # Latihan Essay
        'latihan_essay_questions': [],
        'latihan_essay_shown': {},  # soal yang sudah tampil referensi
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ==========================================
# 5. SIDEBAR (NAVIGASI)
# ==========================================
with st.sidebar:
    st.title("🎓 CAT MHI")
    st.caption("Inayasha — Uji Kompetensi")
    st.divider()

    if st.button("🏠 Beranda", use_container_width=True):
        st.session_state.mode = 'Beranda'

    if st.button("📝 Latihan Pilihan Ganda", use_container_width=True):
        st.session_state.mode = 'PG'
        st.session_state.current_q = 0
        st.session_state.latihan_pg_questions = random.sample(soal_pg, len(soal_pg))
        st.session_state.latihan_pg_answers = {}
        st.session_state.latihan_pg_checked = {}

    if st.button("✏️ Latihan Essay", use_container_width=True):
        st.session_state.mode = 'Essay'
        st.session_state.current_q = 0
        st.session_state.latihan_essay_questions = random.sample(soal_essay, len(soal_essay))
        st.session_state.latihan_essay_shown = {}

    st.divider()

    n_sim = min(JUMLAH_SOAL_SIMULASI, len(soal_pg))
    if st.button(f"🚀 Simulasi Ujian ({n_sim} Soal)", use_container_width=True, type="primary"):
        st.session_state.mode = 'Simulasi'
        st.session_state.simulasi_answers = {}
        st.session_state.simulasi_submitted = False
        st.session_state.simulasi_start_time = time.time()
        st.session_state.simulasi_questions = random.sample(soal_pg, n_sim)
        st.session_state.current_q = 0
        st.session_state.simulasi_show_review = False
        st.session_state.simulasi_review_idx = 0

    st.divider()
    st.caption(f"📚 {len(soal_pg)} soal PG tersedia")
    st.caption(f"📖 {len(soal_essay)} soal Essay tersedia")


# ==========================================
# 6. HALAMAN BERANDA
# ==========================================
if st.session_state.mode == 'Beranda':
    st.title("Simulasi Ujikom MHI")
    st.write("Aplikasi latihan soal **Pilihan Ganda** dan **Essay** untuk persiapan Uji Kompetensi.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Soal PG", f"{len(soal_pg)}")
    with col2:
        st.metric("Soal Essay", f"{len(soal_essay)}")
    with col3:
        st.metric("Soal Simulasi", f"{min(JUMLAH_SOAL_SIMULASI, len(soal_pg))}")

    st.divider()
    st.markdown("""
    **Panduan Penggunaan:**
    - **Latihan PG** — Kerjakan soal satu per satu, cek jawaban langsung, navigasi bebas.
    - **Latihan Essay** — Baca soal, tulis jawaban sendiri, lalu tampilkan referensi untuk evaluasi diri.
    - **Simulasi Ujian** — {n} soal acak dengan timer 2 jam. Jawaban dikunci setelah dikumpulkan. Ambang batas lulus: **{p}%**.
    """.format(n=min(JUMLAH_SOAL_SIMULASI, len(soal_pg)), p=int(PASSING_SCORE)))

    st.info("💡 Setiap kali memilih mode, urutan soal diacak ulang secara otomatis.")


# ==========================================
# 7. HALAMAN LATIHAN PILIHAN GANDA
# ==========================================
elif st.session_state.mode == 'PG':
    st.title("📝 Latihan Pilihan Ganda")

    if not st.session_state.latihan_pg_questions:
        st.session_state.latihan_pg_questions = random.sample(soal_pg, len(soal_pg))

    questions = st.session_state.latihan_pg_questions
    total_q   = len(questions)
    idx       = st.session_state.current_q
    q         = questions[idx]

    # Progress
    st.progress((idx + 1) / total_q)
    st.write(f"**Soal {idx + 1} dari {total_q}**")

    st.write("### " + q['pertanyaan'])

    # Jawaban sebelumnya (jika ada)
    saved = st.session_state.latihan_pg_answers.get(idx)
    opsi_keys = list(q['opsi'].keys())
    default_idx = opsi_keys.index(saved) if saved in opsi_keys else 0

    pilihan = st.radio(
        "Pilih jawaban:",
        opsi_keys,
        format_func=lambda x: f"{x}. {q['opsi'][x]}",
        key=f"pg_radio_{idx}",
        index=default_idx,
    )

    # Simpan pilihan ke state
    st.session_state.latihan_pg_answers[idx] = pilihan

    # Tombol cek jawaban
    sudah_dicek = st.session_state.latihan_pg_checked.get(idx, False)

    col_btn1, col_btn2 = st.columns([1, 2])
    with col_btn1:
        if st.button("✅ Cek Jawaban", type="primary"):
            st.session_state.latihan_pg_checked[idx] = True
            sudah_dicek = True

    # Tampilkan hasil jika sudah dicek
    if sudah_dicek:
        kunci = q['kunci_jawaban']
        if pilihan == kunci:
            st.success(f"**Benar!** Jawaban: **{kunci}. {q['opsi'][kunci]}**")
        else:
            st.error(f"**Salah.** Jawaban Anda: {pilihan}. {q['opsi'].get(pilihan, '')}")
            st.info(f"Kunci Jawaban: **{kunci}. {q['opsi'][kunci]}**")

    st.divider()

    # Navigasi
    col1, col_mid, col2 = st.columns([1, 2, 1])
    with col1:
        if idx > 0:
            if st.button("◀ Sebelumnya", use_container_width=True):
                st.session_state.current_q -= 1
                st.rerun()
    with col_mid:
        # Ringkasan jawaban
        n_checked = len(st.session_state.latihan_pg_checked)
        n_benar   = sum(
            1 for i, c in st.session_state.latihan_pg_checked.items()
            if c and st.session_state.latihan_pg_answers.get(i) == questions[i]['kunci_jawaban']
        )
        if n_checked:
            st.caption(f"Sudah dicek: {n_checked} soal | Benar: {n_benar}")
    with col2:
        if idx < total_q - 1:
            if st.button("Selanjutnya ▶", use_container_width=True):
                st.session_state.current_q += 1
                st.rerun()


# ==========================================
# 8. HALAMAN LATIHAN ESSAY
# ==========================================
elif st.session_state.mode == 'Essay':
    st.title("✏️ Latihan Essay")

    if not st.session_state.latihan_essay_questions:
        st.session_state.latihan_essay_questions = random.sample(soal_essay, len(soal_essay))

    questions = st.session_state.latihan_essay_questions
    total_q   = len(questions)
    idx       = st.session_state.current_q
    q         = questions[idx]

    st.progress((idx + 1) / total_q)
    st.write(f"**Soal {idx + 1} dari {total_q}**")

    st.write("### " + q['pertanyaan'])
    st.text_area("Ketik jawaban Anda:", height=150, key=f"essay_input_{idx}")

    if st.button("📖 Tampilkan Referensi Jawaban", type="primary"):
        st.session_state.latihan_essay_shown[idx] = True

    if st.session_state.latihan_essay_shown.get(idx):
        st.info("**Referensi Jawaban Resmi:**\n\n" + q['referensi_jawaban'])

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if idx > 0:
            if st.button("◀ Sebelumnya", use_container_width=True):
                st.session_state.current_q -= 1
                st.rerun()
    with col2:
        if idx < total_q - 1:
            if st.button("Selanjutnya ▶", use_container_width=True):
                st.session_state.current_q += 1
                st.rerun()


# ==========================================
# 9. HALAMAN SIMULASI UJIAN
# ==========================================
elif st.session_state.mode == 'Simulasi':

    questions = st.session_state.simulasi_questions
    total_q   = len(questions)

    # ── Tampilan setelah submit: HASIL + REVIEW ──────────────────────────────
    if st.session_state.simulasi_submitted:

        if not st.session_state.simulasi_show_review:
            # ── Kartu Hasil ─────────────────────────────────────────────────
            st.title("🎉 Hasil Simulasi")

            benar = sum(
                1 for q in questions
                if st.session_state.simulasi_answers.get(str(q['id'])) == q['kunci_jawaban']
            )
            salah       = total_q - benar
            skor_akhir  = (benar / total_q) * 100
            lulus       = skor_akhir >= PASSING_SCORE

            waktu_total  = int(time.time() - st.session_state.simulasi_start_time)
            menit_habis  = waktu_total // 60
            detik_habis  = waktu_total % 60

            if lulus:
                st.success(f"### ✅ LULUS — Skor: {skor_akhir:.1f}%")
            else:
                st.error(f"### ❌ BELUM LULUS — Skor: {skor_akhir:.1f}% (minimum {PASSING_SCORE:.0f}%)")

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Skor",  f"{skor_akhir:.1f}%")
            col2.metric("Benar", benar)
            col3.metric("Salah", salah)
            col4.metric("Waktu", f"{menit_habis}m {detik_habis}s")

            st.divider()
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔍 Review Jawaban", use_container_width=True, type="primary"):
                    st.session_state.simulasi_show_review = True
                    st.session_state.simulasi_review_idx = 0
                    st.rerun()
            with col_b:
                if st.button("🔄 Ulangi Simulasi (Soal Baru)", use_container_width=True):
                    n_sim = min(JUMLAH_SOAL_SIMULASI, len(soal_pg))
                    st.session_state.simulasi_answers   = {}
                    st.session_state.simulasi_submitted = False
                    st.session_state.simulasi_start_time = time.time()
                    st.session_state.simulasi_questions = random.sample(soal_pg, n_sim)
                    st.session_state.current_q = 0
                    st.session_state.simulasi_show_review = False
                    st.rerun()

        else:
            # ── Mode Review: satu soal per halaman ──────────────────────────
            st.title("🔍 Review Jawaban")
            ridx = st.session_state.simulasi_review_idx
            q    = questions[ridx]

            # Status seluruh soal (strip ringkasan di atas)
            n_benar_total = sum(
                1 for qq in questions
                if st.session_state.simulasi_answers.get(str(qq['id'])) == qq['kunci_jawaban']
            )
            st.caption(f"Soal {ridx + 1} dari {total_q}  |  Total benar: {n_benar_total}/{total_q}")
            st.progress((ridx + 1) / total_q)

            jawaban_user = st.session_state.simulasi_answers.get(str(q['id']))
            kunci        = q['kunci_jawaban']
            benar_soal   = jawaban_user == kunci

            if benar_soal:
                st.success(f"**Soal {ridx + 1} — Benar ✅**")
            else:
                st.error(f"**Soal {ridx + 1} — Salah ❌**")

            st.write("### " + q['pertanyaan'])
            st.divider()

            for key, teks in q['opsi'].items():
                if key == kunci and key == jawaban_user:
                    st.markdown(f"✅ **{key}. {teks}** ← Jawaban Anda (Benar)")
                elif key == kunci:
                    st.markdown(f"✅ **{key}. {teks}** ← Kunci Jawaban")
                elif key == jawaban_user:
                    st.markdown(f"❌ ~~{key}. {teks}~~ ← Jawaban Anda")
                else:
                    st.markdown(f"　 {key}. {teks}")

            st.divider()
            col1, col_mid, col2 = st.columns([1, 2, 1])
            with col1:
                if ridx > 0:
                    if st.button("◀ Sebelumnya", use_container_width=True):
                        st.session_state.simulasi_review_idx -= 1
                        st.rerun()
            with col_mid:
                if st.button("◀ Kembali ke Hasil", use_container_width=True):
                    st.session_state.simulasi_show_review = False
                    st.rerun()
            with col2:
                if ridx < total_q - 1:
                    if st.button("Selanjutnya ▶", use_container_width=True):
                        st.session_state.simulasi_review_idx += 1
                        st.rerun()

    # ── Tampilan saat ujian berlangsung ──────────────────────────────────────
    else:
        idx = st.session_state.current_q
        q   = questions[idx]

        # Header & Timer
        elapsed_time = int(time.time() - st.session_state.simulasi_start_time)
        sisa_waktu   = max(0, WAKTU_UJIAN_DETIK - elapsed_time)

        # Auto-submit jika waktu habis
        if sisa_waktu == 0:
            st.session_state.simulasi_submitted = True
            st.rerun()

        st.title(f"🚀 Simulasi Ujian — Soal {idx + 1}/{total_q}")
        st.progress((idx + 1) / total_q)

        # Timer HTML
        timer_html = f"""
        <div style="background:#fff3cd;border-left:5px solid #ff4b4b;padding:12px 18px;
                    border-radius:6px;margin-bottom:10px;">
            <span style="font-size:1rem;font-weight:600;color:#333;">⏱️ Sisa Waktu: </span>
            <span id="clock" style="font-size:1.2rem;font-weight:700;color:#ff4b4b;">Memuat...</span>
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
        components.html(timer_html, height=65)

        # Soal
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

        # Indikator berapa soal sudah dijawab
        n_dijawab = len(st.session_state.simulasi_answers)
        st.caption(f"Sudah dijawab: {n_dijawab}/{total_q} soal")

        st.divider()

        # Navigasi soal
        col1, col_kumpul, col2 = st.columns([1, 2, 1])
        with col1:
            if idx > 0:
                if st.button("◀ Sebelumnya", use_container_width=True):
                    st.session_state.current_q -= 1
                    st.rerun()
        with col_kumpul:
            label_kumpul = f"📥 Kumpulkan ({n_dijawab}/{total_q} dijawab)"
            if st.button(label_kumpul, use_container_width=True, type="primary"):
                st.session_state.simulasi_submitted = True
                st.rerun()
        with col2:
            if idx < total_q - 1:
                if st.button("Selanjutnya ▶", use_container_width=True):
                    st.session_state.current_q += 1
                    st.rerun()

        # Peta soal (grid kecil navigasi cepat)
        with st.expander("🗺️ Peta Soal — Navigasi Cepat", expanded=False):
            cols_per_row = 10
            all_keys     = [str(q['id']) for q in questions]
            rows         = [questions[i:i+cols_per_row] for i in range(0, total_q, cols_per_row)]

            for row_start, row in enumerate(rows):
                cols = st.columns(cols_per_row)
                for col_pos, soal in enumerate(row):
                    soal_idx   = row_start * cols_per_row + col_pos
                    dijawab    = str(soal['id']) in st.session_state.simulasi_answers
                    label_peta = f"{'✓' if dijawab else '○'}{soal_idx+1}"
                    with cols[col_pos]:
                        if st.button(label_peta, key=f"peta_{soal_idx}", use_container_width=True):
                            st.session_state.current_q = soal_idx
                            st.rerun()
