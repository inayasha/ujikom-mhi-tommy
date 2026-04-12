import streamlit as st
import streamlit.components.v1 as components
import json
import time

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
    st.error("Gagal memuat database soal.")
    st.stop()

# ==========================================
# 3. STATE MANAGEMENT
# ==========================================
if 'mode' not in st.session_state:
    st.session_state.mode = 'Beranda'
if 'current_q' not in st.session_state:
    st.session_state.current_q = 0

if 'simulasi_answers' not in st.session_state:
    st.session_state.simulasi_answers = {}
if 'simulasi_submitted' not in st.session_state:
    st.session_state.simulasi_submitted = False
if 'simulasi_start_time' not in st.session_state:
    st.session_state.simulasi_start_time = None

# ==========================================
# 4. SIDEBAR (NAVIGASI)
# ==========================================
with st.sidebar:
    st.title("Navigasi")
    if st.button("🏠 Beranda", use_container_width=True):
        st.session_state.mode = 'Beranda'
    if st.button("📝 Latihan Pilihan Ganda", use_container_width=True):
        st.session_state.mode = 'PG'
        st.session_state.current_q = 0
    if st.button("✍️ Latihan Essay", use_container_width=True):
        st.session_state.mode = 'Essay'
        st.session_state.current_q = 0
    
    st.divider()
    
    if st.button("⏱️ Simulasi Ujian (PG)", use_container_width=True, type="primary"):
        st.session_state.mode = 'Simulasi'
        st.session_state.simulasi_answers = {}
        st.session_state.simulasi_submitted = False
        st.session_state.simulasi_start_time = time.time() # Mencatat waktu mulai

# ==========================================
# 5. HALAMAN BERANDA
# ==========================================
if st.session_state.mode == 'Beranda':
    st.title("Simulasi Ujikom MHI")
    st.write("Aplikasi latihan soal Pilihan Ganda dan Essay untuk persiapan Uji Kompetensi.")
    st.info("Pilih mode latihan di panel sebelah kiri.")

# ==========================================
# 6. HALAMAN LATIHAN PILIHAN GANDA
# ==========================================
elif st.session_state.mode == 'PG':
    st.title("Latihan Pilihan Ganda")
    
    total_q = len(soal_pg)
    idx = st.session_state.current_q
    
    st.progress((idx + 1) / total_q)
    st.write(f"**Soal {idx + 1} dari {total_q}**")
    
    q = soal_pg[idx]
    st.write("### " + q['pertanyaan'])
    
    pilihan = st.radio("Pilih jawaban:", list(q['opsi'].keys()), format_func=lambda x: q['opsi'][x], key=f"radio_{idx}")
    
    if st.button("Cek Jawaban", type="primary"):
        if pilihan == q['kunci_jawaban']:
            st.success(f"Benar! Kunci Jawaban: **{q['kunci_jawaban']}**")
        else:
            st.error(f"Salah. Kunci Jawaban yang tepat adalah **{q['kunci_jawaban']}**")
            
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if idx > 0:
            if st.button("⬅️ Sebelumnya", use_container_width=True):
                st.session_state.current_q -= 1
                st.rerun()
    with col2:
        if idx < total_q - 1:
            if st.button("Selanjutnya ➡️", use_container_width=True):
                st.session_state.current_q += 1
                st.rerun()

# ==========================================
# 7. HALAMAN LATIHAN ESSAY
# ==========================================
elif st.session_state.mode == 'Essay':
    st.title("Latihan Essay")
    
    total_q = len(soal_essay)
    idx = st.session_state.current_q
    
    st.progress((idx + 1) / total_q)
    st.write(f"**Soal {idx + 1} dari {total_q}**")
    
    q = soal_essay[idx]
    st.write("### " + q['pertanyaan'])
    
    st.text_area("Ketik jawaban Anda:", height=150)
    
    if st.button("Tampilkan Referensi Jawaban", type="primary"):
        st.info("**Referensi Jawaban Resmi:**\n\n" + q['referensi_jawaban'])
        
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if idx > 0:
            if st.button("⬅️ Sebelumnya", use_container_width=True):
                st.session_state.current_q -= 1
                st.rerun()
    with col2:
        if idx < total_q - 1:
            if st.button("Selanjutnya ➡️", use_container_width=True):
                st.session_state.current_q += 1
                st.rerun()

# ==========================================
# 8. HALAMAN SIMULASI UJIAN (DENGAN TIMER)
# ==========================================
elif st.session_state.mode == 'Simulasi':
    st.title("Mode Simulasi Ujian")
    
    # Logika Timer (90 Menit)
    WAKTU_UJIAN_DETIK = 5400 
    
    if not st.session_state.simulasi_submitted:
        elapsed_time = int(time.time() - st.session_state.simulasi_start_time)
        sisa_waktu = max(0, WAKTU_UJIAN_DETIK - elapsed_time)
        
        # Injeksi HTML/JS untuk Countdown yang responsif tanpa merefresh server
        timer_html = f"""
        <div style="background-color: #f8f9fa; border-left: 5px solid #ff4b4b; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <h3 style="margin: 0; color: #333;">⏱️ Sisa Waktu: <span id="clock" style="color: #ff4b4b;">Memuat...</span></h3>
        </div>
        <script>
            var timeLeft = {sisa_waktu};
            var elem = document.getElementById('clock');
            var timerId = setInterval(countdown, 1000);
            
            function countdown() {{
                if (timeLeft <= 0) {{
                    clearTimeout(timerId);
                    elem.innerHTML = "WAKTU HABIS!";
                    elem.style.color = "red";
                }} else {{
                    var m = Math.floor(timeLeft / 60);
                    var s = timeLeft % 60;
                    elem.innerHTML = (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
                    timeLeft--;
                }}
            }}
        </script>
        """
        components.html(timer_html, height=80)
        st.warning("Kerjakan seluruh soal di bawah ini. Nilai akhir akan muncul setelah Anda mengklik 'Kumpulkan'.")
    
    total_q = len(soal_pg)
    
    for i, q in enumerate(soal_pg):
        st.write(f"**{i + 1}. {q['pertanyaan']}**")
        opsi_keys = list(q['opsi'].keys())
        
        saved_answer = st.session_state.simulasi_answers.get(str(q['id']))
        default_index = opsi_keys.index(saved_answer) if saved_answer in opsi_keys else None
        
        pilihan = st.radio(
            label=f"Opsi Soal {q['id']}", 
            options=opsi_keys, 
            format_func=lambda x: q['opsi'][x], 
            key=f"sim_radio_{q['id']}",
            index=default_index,
            label_visibility="collapsed",
            disabled=st.session_state.simulasi_submitted
        )
        
        if pilihan:
            st.session_state.simulasi_answers[str(q['id'])] = pilihan
            
        st.write("")
    
    st.divider()
    
    if not st.session_state.simulasi_submitted:
        if st.button("Kumpulkan & Lihat Hasil", type="primary", use_container_width=True):
            st.session_state.simulasi_submitted = True
            st.rerun()
    else:
        benar = 0
        for q in soal_pg:
            jawaban_user = st.session_state.simulasi_answers.get(str(q['id']))
            if jawaban_user == q['kunci_jawaban']:
                benar += 1
                
        skor_akhir = (benar / total_q) * 100
        waktu_selesai = int(time.time() - st.session_state.simulasi_start_time)
        menit_selesai = waktu_selesai // 60
        detik_selesai = waktu_selesai % 60
        
        st.success(f"### 🎉 Simulasi Selesai! Skor Akhir Anda: {skor_akhir:.2f}")
        st.write(f"**Anda menjawab benar {benar} dari {total_q} soal.**")
        st.info(f"⏱️ Waktu yang Anda habiskan: **{menit_selesai} menit {detik_selesai} detik**.")
        
        if st.button("Ulangi Simulasi", use_container_width=True):
            st.session_state.simulasi_answers = {}
            st.session_state.simulasi_submitted = False
            st.session_state.simulasi_start_time = time.time()
            st.rerun()
