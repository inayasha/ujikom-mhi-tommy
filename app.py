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
# 3. STATE MANAGEMENT (DIPERBARUI)
# ==========================================
if 'mode' not in st.session_state:
    st.session_state.mode = 'Beranda'
if 'current_q' not in st.session_state:
    st.session_state.current_q = 0
# Variabel baru untuk mode simulasi
if 'simulasi_answers' not in st.session_state:
    st.session_state.simulasi_answers = {}
if 'simulasi_submitted' not in st.session_state:
    st.session_state.simulasi_submitted = False

# ==========================================
# 4. SIDEBAR (NAVIGASI DIPERBARUI)
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
    
    # Tombol baru untuk mode simulasi
    if st.button("⏱️ Simulasi Ujian (PG)", use_container_width=True, type="primary"):
        st.session_state.mode = 'Simulasi'
        # Reset ulang jawaban jika menekan tombol ini lagi
        st.session_state.simulasi_answers = {}
        st.session_state.simulasi_submitted = False

# ==========================================
# 5. HALAMAN BERANDA
# ==========================================
if st.session_state.mode == 'Beranda':
    st.title("Simulasi Ujikom MHI")
    st.write("Aplikasi latihan soal Pilihan Ganda dan Essay untuk persiapan Uji Kompetensi.")
    st.info("Pilih mode latihan di panel sebelah kiri.")

# ==========================================
# 6. HALAMAN LATIHAN PILIHAN GANDA (DRILL)
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
# 8. HALAMAN SIMULASI UJIAN (FITUR BARU)
# ==========================================
elif st.session_state.mode == 'Simulasi':
    st.title("Mode Simulasi Ujian")
    st.warning("Kerjakan seluruh soal di bawah ini. Nilai akhir akan muncul setelah Anda mengklik 'Kumpulkan'.")
    
    total_q = len(soal_pg)
    
    # Render semua soal ke bawah
    for i, q in enumerate(soal_pg):
        st.write(f"**{i + 1}. {q['pertanyaan']}**")
        
        opsi_keys = list(q['opsi'].keys())
        
        # Ambil state jawaban sebelumnya (berguna jika user tidak sengaja klik menu lain lalu kembali)
        saved_answer = st.session_state.simulasi_answers.get(str(q['id']))
        default_index = opsi_keys.index(saved_answer) if saved_answer in opsi_keys else None
        
        # Radio button untuk memilih opsi
        pilihan = st.radio(
            label=f"Opsi Soal {q['id']}", 
            options=opsi_keys, 
            format_func=lambda x: q['opsi'][x], 
            key=f"sim_radio_{q['id']}",
            index=default_index,
            label_visibility="collapsed",
            disabled=st.session_state.simulasi_submitted # Kunci radio button jika sudah disubmit
        )
        
        # Simpan ke state setiap kali user memilih
        if pilihan:
            st.session_state.simulasi_answers[str(q['id'])] = pilihan
            
        st.write("") # Spacing antar soal
    
    st.divider()
    
    # Logika Penilaian
    if not st.session_state.simulasi_submitted:
        if st.button("Kumpulkan & Lihat Hasil", type="primary", use_container_width=True):
            st.session_state.simulasi_submitted = True
            st.rerun()
    else:
        # Menghitung skor
        benar = 0
        for q in soal_pg:
            jawaban_user = st.session_state.simulasi_answers.get(str(q['id']))
            if jawaban_user == q['kunci_jawaban']:
                benar += 1
                
        skor_akhir = (benar / total_q) * 100
        
        st.success(f"### 🎉 Simulasi Selesai! Skor Akhir Anda: {skor_akhir:.2f}")
        st.write(f"**Anda menjawab benar {benar} dari {total_q} soal.**")
        
        # Tombol Ulangi
        if st.button("Ulangi Simulasi", use_container_width=True):
            st.session_state.simulasi_answers = {}
            st.session_state.simulasi_submitted = False
            st.rerun()
