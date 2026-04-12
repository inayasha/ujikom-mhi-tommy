import streamlit as st
import json

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