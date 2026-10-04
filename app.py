import streamlit as st
import pandas as pd
import datetime

# ----------------------------------------------------
# 1. KONFIGURASI HALAMAN APLIKASI
# ----------------------------------------------------
st.set_page_config(
    page_title="Gym Progress Tracker", 
    layout="wide", 
    page_icon="🏋️‍♂️"
)

st.title("🏋️‍♂️ Gym Upper/Lower Progress Tracker")

# ----------------------------------------------------
# 2. SAFE LOAD MODULE (GSHEETS / LOCAL FALLBACK)
# ----------------------------------------------------
GSHEETS_AVAILABLE = False
try:
    from streamlit_gsheets import GSheetsConnection
    GSHEETS_AVAILABLE = True
except ModuleNotFoundError:
    st.warning("⚠️ Modul 'st-gsheets-connection' belum ter-install. Memakai mode penyimpanan lokal.")

# ----------------------------------------------------
# 3. KONEKSI GOOGLE SHEETS & HELPER FUNCTIONS
# ----------------------------------------------------
COLS_WORKOUT = ["Tanggal", "Hari", "Sesi", "Exercise", "Set", "Reps", "Beban (kg)", "RIR", "RPE", "Catatan"]
COLS_HABITS = ["Tanggal", "Latihan", "Protein", "Buah/Sayur", "Minum Cukup", "Tidur Cukup", "Energi", "Recovery", "Catatan"]
COLS_WEEKLY = ["Minggu", "Latihan Upper", "Latihan Lower", "Total Sesi", "Tidur Rata-rata", "Energi", "Recovery", "Catatan"]

# Init Session State
for key, cols in [("df_workout", COLS_WORKOUT), ("df_habits", COLS_HABITS), ("df_weekly", COLS_WEEKLY)]:
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame(columns=cols)

if GSHEETS_AVAILABLE:
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        def load_data(sheet_name, default_cols):
            try:
                df = conn.read(worksheet=sheet_name, ttl="0")
                return df if df is not None and not df.empty else pd.DataFrame(columns=default_cols)
            except Exception:
                return pd.DataFrame(columns=default_cols)
        
        df_workout = load_data("Workout_Logs", COLS_WORKOUT)
        df_habits = load_data("Habits_Logs", COLS_HABITS)
        df_weekly = load_data("Weekly_Logs", COLS_WEEKLY)
    except Exception as e:
        df_workout = st.session_state["df_workout"]
        df_habits = st.session_state["df_habits"]
        df_weekly = st.session_state["df_weekly"]
else:
    df_workout = st.session_state["df_workout"]
    df_habits = st.session_state["df_habits"]
    df_weekly = st.session_state["df_weekly"]

def save_data(df, worksheet_name, state_key):
    st.session_state[state_key] = df
    if GSHEETS_AVAILABLE:
        try:
            conn.update(worksheet=worksheet_name, data=df)
            st.success("✅ Data tersimpan ke Google Sheets!")
        except Exception as e:
            st.warning(f"Tersimpan lokal (Gagal update Google Sheets: {e})")

# ----------------------------------------------------
# 4. DATABASE PROGRAM LATIHAN
# ----------------------------------------------------
PROGRAM_DATA = {
    "Upper A": [
        {"Exercise": "Bench Press", "Set Target": 3, "Reps Target": "6-8", "RIR Target": "1-2"},
        {"Exercise": "Incline Press", "Set Target": 2, "Reps Target": "8-12", "RIR Target": "1-2"},
        {"Exercise": "Pull Up", "Set Target": 3, "Reps Target": "8-12", "RIR Target": "1-2"},
        {"Exercise": "Cable Row", "Set Target": 3, "Reps Target": "8-12", "RIR Target": "1-2"},
        {"Exercise": "Lat Pulldown", "Set Target": 3, "Reps Target": "8-12", "RIR Target": "1-2"},
        {"Exercise": "Shoulder Press", "Set Target": 2, "Reps Target": "6-10", "RIR Target": "1-2"},
        {"Exercise": "Lateral Raise", "Set Target": 3, "Reps Target": "12-20", "RIR Target": "1-2"},
        {"Exercise": "Rear Delt Fly", "Set Target": 2, "Reps Target": "12-20", "RIR Target": "1-2"},
        {"Exercise": "Triceps Pushdown", "Set Target": 3, "Reps Target": "10-15", "RIR Target": "1-2"},
        {"Exercise": "Supinating DB Curl", "Set Target": 3, "Reps Target": "8-12", "RIR Target": "1-2"}
    ],
    "Lower A": [
        {"Exercise": "Squat", "Set Target": 3, "Reps Target": "6-8", "RIR Target": "1-2"},
        {"Exercise": "Romanian Deadlift", "Set Target": 3, "Reps Target": "6-10", "RIR Target": "1-2"},
        {"Exercise": "Leg Curl", "Set Target": 2, "Reps Target": "10-15", "RIR Target": "1-2"},
        {"Exercise": "Leg Extension", "Set Target": 2, "Reps Target": "10-15", "RIR Target": "1-2"},
        {"Exercise": "Calf Raise", "Set Target": 3, "Reps Target": "8-15", "RIR Target": "1-2"},
        {"Exercise": "Cable Crunch", "Set Target": 2, "Reps Target": "10-15", "RIR Target": "1-2"},
        {"Exercise": "Hip Thrust", "Set Target": 2, "Reps Target": "10-15", "RIR Target": "1-2"}
    ],
    "Upper B": [
        {"Exercise": "Incline Press", "Set Target": 3, "Reps Target": "6-10", "RIR Target": "1-2"},
        {"Exercise": "Bench Press", "Set Target": 2, "Reps Target": "8-12", "RIR Target": "1-2"},
        {"Exercise": "Cable Row", "Set Target": 3, "Reps Target": "8-12", "RIR Target": "1-2"},
        {"Exercise": "Pull Up", "Set Target": 3, "Reps Target": "8-12", "RIR Target": "1-2"},
        {"Exercise": "Lat Pulldown", "Set Target": 3, "Reps Target": "8-12", "RIR Target": "1-2"},
        {"Exercise": "Shoulder Press", "Set Target": 2, "Reps Target": "8-12", "RIR Target": "1-2"},
        {"Exercise": "Cable Lateral Raise", "Set Target": 3, "Reps Target": "12-20", "RIR Target": "1-2"},
        {"Exercise": "Rear Delt Fly", "Set Target": 2, "Reps Target": "12-20", "RIR Target": "1-2"},
        {"Exercise": "Overhead Triceps Extension", "Set Target": 3, "Reps Target": "10-15", "RIR Target": "1-2"},
        {"Exercise": "Preacher Curl", "Set Target": 3, "Reps Target": "8-12", "RIR Target": "1-2"}
    ],
    "Lower B": [
        {"Exercise": "Squat", "Set Target": 3, "Reps Target": "6-10", "RIR Target": "1-2"},
        {"Exercise": "Hip Thrust", "Set Target": 3, "Reps Target": "8-12", "RIR Target": "1-2"},
        {"Exercise": "Leg Curl", "Set Target": 3, "Reps Target": "8-15", "RIR Target": "1-2"},
        {"Exercise": "Leg Extension", "Set Target": 2, "Reps Target": "10-15", "RIR Target": "1-2"},
        {"Exercise": "Calf Raise", "Set Target": 3, "Reps Target": "10-15", "RIR Target": "1-2"},
        {"Exercise": "Cable Crunch", "Set Target": 2, "Reps Target": "8-15 / 30-60s", "RIR Target": "1-2"}
    ]
}

# ----------------------------------------------------
# 5. NAVIGASI SIDEBAR
# ----------------------------------------------------
menu = st.sidebar.radio(
    "📍 Navigasi Menu", 
    ["📋 Program Latihan", "🏋️‍♂️ Input Workout Log", "🥗 Daily Habits", "📈 Progress Mingguan", "📊 Dashboard Stats"]
)

# ----------------------------------------------------
# MENU 1: PROGRAM LATIHAN
# ----------------------------------------------------
if "Program Latihan" in menu:
    st.subheader("📋 Detail Program Upper / Lower Split")
    st.info("💡 **Aturan Overload:** Catat beban & reps setiap sesi. Jika semua set sudah mencapai batas atas reps dengan teknik bagus, naikkan beban sedikit pada sesi berikutnya.")
    
    col1, col2 = st.columns(2)
    for idx, (sesi_name, ex_list) in enumerate(PROGRAM_DATA.items()):
        with (col1 if idx % 2 == 0 else col2):
            st.markdown(f"### 🎯 Sesi {sesi_name}")
            st.dataframe(pd.DataFrame(ex_list), use_container_width=True, hide_index=True)

# ----------------------------------------------------
# MENU 2: INPUT WORKOUT LOG
# ----------------------------------------------------
elif "Input Workout Log" in menu:
    st.subheader("🏋️‍♂️ Catat Sesi Latihan Harian")
    
    # --- DITARUH DI LUAR FORM AGAR DYNAMIC REAL-TIME ---
    c1, c2, c3 = st.columns(3)
    tanggal = c1.date_input("Tanggal", datetime.date.today())
    hari = c2.selectbox("Hari", ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"])
    sesi = c3.selectbox("Sesi Latihan", ["Upper A", "Lower A", "Upper B", "Lower B", "Custom"])

    # Otomatis update daftar gerakan berdasarkan Sesi yang dipilih
    program_exercises = [e["Exercise"] for e in PROGRAM_DATA.get(sesi, [])]

    with st.form("form_workout", clear_on_submit=False):
        exercise_choice = st.selectbox("Pilih Gerakan dari Program", ["(Ketik Manual)"] + program_exercises)
        exercise_custom = st.text_input("Nama Gerakan (jika ketik manual)", value="" if exercise_choice != "(Ketik Manual)" else "")
        
        exercise_final = exercise_choice if exercise_choice != "(Ketik Manual)" else exercise_custom

        c4, c5, c6, c7, c8 = st.columns(5)
        set_num = c4.number_input("Set Ke-", min_value=1, value=1)
        reps = c5.number_input("Reps (Ulang)", min_value=1, value=10)
        beban = c6.number_input("Beban (kg)", min_value=0.0, value=20.0, step=0.5)
        rir = c7.number_input("RIR (0-5)", min_value=0, max_value=5, value=2)
        rpe = c8.number_input("RPE (1-10)", min_value=1, max_value=10, value=10-rir)

        catatan = st.text_input("Catatan Set / Form / Sensasi Otot")
        submitted = st.form_submit_button("➕ Simpan Set Latihan")

        if submitted and exercise_final:
            new_entry = {
                "Tanggal": tanggal.strftime("%Y-%m-%d"), 
                "Hari": hari, 
                "Sesi": sesi,
                "Exercise": exercise_final, 
                "Set": set_num, 
                "Reps": reps,
                "Beban (kg)": beban, 
                "RIR": rir, 
                "RPE": rpe, 
                "Catatan": catatan
            }
            df_updated = pd.concat([df_workout, pd.DataFrame([new_entry])], ignore_index=True)
            save_data(df_updated, "Workout_Logs", "df_workout")
            st.rerun()

    st.markdown("---")
    st.subheader("📜 Riwayat Workout Log & Hapus Data")
    
    if not df_workout.empty:
        st.dataframe(df_workout, use_container_width=True)
        
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            if st.button("↩️ Hapus Set Terakhir (Undo)"):
                df_updated = df_workout.iloc[:-1]
                save_data(df_updated, "Workout_Logs", "df_workout")
                st.rerun()
                
        with col_del2:
            row_to_delete = st.number_input("Hapus Baris Indeks Ke-:", min_value=0, max_value=max(0, len(df_workout)-1), step=1)
            if st.button("🗑️ Hapus Baris Ini"):
                df_updated = df_workout.drop(index=row_to_delete).reset_index(drop=True)
                save_data(df_updated, "Workout_Logs", "df_workout")
                st.rerun()
    else:
        st.info("Belum ada data latihan terdaftar.")

# ----------------------------------------------------
# MENU 3: DAILY HABITS
# ----------------------------------------------------
elif "Daily Habits" in menu:
    st.subheader("🥗 Daily Habits Tracker (Kebiasaan Harian)")
    
    with st.form("form_habits"):
        tgl = st.date_input("Tanggal", datetime.date.today())
        
        c1, c2, c3 = st.columns(3)
        latihan = c1.checkbox("Latihan Selesai")
        protein = c2.checkbox("Protein Tiap Makan Utama")
        buah = c3.checkbox("Buah / Sayur Terpenuhi")
        
        c4, c5 = st.columns(2)
        minum = c4.checkbox("Minum Cukup Air")
        tidur = c5.checkbox("Tidur Cukup & Berkualitas")

        e1, e2 = st.columns(2)
        energi = e1.slider("Level Energi Harian (1-5)", 1, 5, 4)
        recovery = e2.slider("Level Recovery / Pemulihan (1-5)", 1, 5, 4)
        cat = st.text_input("Catatan Tambahan Harian")

        sub_h = st.form_submit_button("💾 Simpan Kebiasaan Harian")
        if sub_h:
            h_entry = {
                "Tanggal": tgl.strftime("%Y-%m-%d"), 
                "Latihan": latihan, 
                "Protein": protein,
                "Buah/Sayur": buah, 
                "Minum Cukup": minum, 
                "Tidur Cukup": tidur,
                "Energi": energi, 
                "Recovery": recovery, 
                "Catatan": cat
            }
            df_updated = pd.concat([df_habits, pd.DataFrame([h_entry])], ignore_index=True)
            save_data(df_updated, "Habits_Logs", "df_habits")
            st.rerun()

    st.markdown("---")
    st.subheader("📜 Riwayat Kebiasaan Harian")
    st.dataframe(df_habits, use_container_width=True)

# ----------------------------------------------------
# MENU 4: PROGRESS MINGGUAN
# ----------------------------------------------------
elif "Progress Mingguan" in menu:
    st.subheader("📈 Rekap Evaluasi Mingguan")
    
    with st.form("form_weekly"):
        minggu = st.text_input("Minggu Ke- / Periode", "Minggu 1")
        c1, c2, c3 = st.columns(3)
        up = c1.number_input("Total Sesi Upper Selesai", min_value=0, value=2)
        low = c2.number_input("Total Sesi Lower Selesai", min_value=0, value=2)
        tidur_avg = c3.number_input("Tidur Rata-rata (Jam)", value=7.5)

        e1, e2 = st.columns(2)
        en_avg = e1.slider("Rata-rata Energi Mingguan (1-5)", 1.0, 5.0, 4.0)
        rec_avg = e2.slider("Rata-rata Recovery Mingguan (1-5)", 1.0, 5.0, 4.0)
        cat_w = st.text_input("Catatan Progres / Rencana Naik Beban")

        sub_w = st.form_submit_button("📌 Simpan Rekap Mingguan")
        if sub_w:
            w_entry = {
                "Minggu": minggu, 
                "Latihan Upper": up, 
                "Latihan Lower": low,
                "Total Sesi": up + low, 
                "Tidur Rata-rata": tidur_avg,
                "Energi": en_avg, 
                "Recovery": rec_avg, 
                "Catatan": cat_w
            }
            df_updated = pd.concat([df_weekly, pd.DataFrame([w_entry])], ignore_index=True)
            save_data(df_updated, "Weekly_Logs", "df_weekly")
            st.rerun()

    st.markdown("---")
    st.subheader("📜 Riwayat Evaluasi Mingguan")
    st.dataframe(df_weekly, use_container_width=True)

# ----------------------------------------------------
# MENU 5: DASHBOARD STATS
# ----------------------------------------------------
elif "Dashboard Stats" in menu:
    st.subheader("📊 Dashboard & Grafik Progressive Overload")
    
    if not df_workout.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Set Dicatat", len(df_workout))
        
        vol = (df_workout["Beban (kg)"].astype(float) * df_workout["Reps"].astype(float)).sum()
        col2.metric("Total Volume Angkatan", f"{vol:,.0f} kg")
        col3.metric("Jumlah Variasi Gerakan", df_workout["Exercise"].nunique())

        st.markdown("---")
        st.subheader("📈 Grafik Kenaikan Beban (Progressive Overload)")
        st.line_chart(df_workout, x="Tanggal", y="Beban (kg)", color="Exercise")
    else:
        st.warning("⚠️ Belum ada data latihan yang dicatat.")
