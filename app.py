import streamlit as st
import pandas as pd
import datetime
import base64
import io
import time
from PIL import Image

# ----------------------------------------------------
# KONFIGURASI HALAMAN
# ----------------------------------------------------
st.set_page_config(
    page_title="Gym & Running Progress Tracker", 
    layout="wide", 
    page_icon="🏋️‍♂️"
)

# ----------------------------------------------------
# SEMBUNYIKAN HEADER, TOOLBAR, DAN FOOTER STREAMLIT
# ----------------------------------------------------
hide_streamlit_style = """
    <style>
    /* Sembunyikan seluruh header bar atas (Share, GitHub, Edit, dll) */
    header {visibility: hidden;}
    
    /* Sembunyikan footer "Made with Streamlit" di bawah */
    footer {visibility: hidden;}
    
    /* Sembunyikan menu titik tiga secara spesifik */
    #MainMenu {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ----------------------------------------------------
# 2. HELPER FUNGSI
# ----------------------------------------------------
def process_and_compress_image(uploaded_file):
    """Mengecilkan foto & mengubah ke string Base64 agar hemat ruang di Google Sheets"""
    try:
        img = Image.open(uploaded_file)
        img = img.convert("RGB")
        img.thumbnail((200, 200))
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=80)
        b64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        st.error(f"Gagal memproses gambar: {e}")
        return ""

def calculate_1rm(beban, reps):
    """Menghitung Estimasi 1RM menggunakan Rumus Epley"""
    try:
        b = float(beban)
        r = float(reps)
        if r <= 0 or b <= 0:
            return 0.0
        if r == 1:
            return round(b, 1)
        return round(b * (1.0 + (r / 30.0)), 1)
    except (ValueError, TypeError):
        return 0.0

def run_rest_timer(seconds):
    """Timer hitung mundur istirahat antar set"""
    ph = st.empty()
    for t in range(seconds, -1, -1):
        mins, secs = divmod(t, 60)
        ph.metric("⏱️ Waktu Istirahat Tersisa", f"{mins:02d}:{secs:02d}")
        time.sleep(1)
    ph.success("🔔 Waktu Istirahat Selesai! Saatnya Set Berikutnya! 🔥")

# ----------------------------------------------------
# 3. CEK & KONEKSI GOOGLE SHEETS
# ----------------------------------------------------
GSHEETS_AVAILABLE = False
try:
    from streamlit_gsheets import GSheetsConnection
    GSHEETS_AVAILABLE = True
except ModuleNotFoundError:
    st.error("⚠️ Modul 'st-gsheets-connection' belum ter-install di requirements.txt!")

COLS_USERS = ["Username", "Password", "Nama", "Foto"]
COLS_WORKOUT = ["User", "Tanggal", "Hari", "Sesi", "Exercise", "Set", "Reps", "Beban (kg)", "RIR", "RPE", "Est. 1RM", "Catatan"]
COLS_HABITS = ["User", "Tanggal", "Latihan", "Protein", "Buah/Sayur", "Minum Cukup", "Tidur Cukup", "Energi", "Recovery", "Catatan"]
COLS_WEEKLY = ["User", "Minggu", "Latihan Upper", "Latihan Lower", "Total Sesi", "Tidur Rata-rata", "Energi", "Recovery", "Catatan"]

def load_worksheet(worksheet_name, default_cols):
    if GSHEETS_AVAILABLE:
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            df = conn.read(worksheet=worksheet_name, ttl=0)
            if df is not None:
                for col in default_cols:
                    if col not in df.columns:
                        df[col] = ""
                return df[default_cols]
        except Exception as e:
            st.sidebar.warning(f"⚠️ Gagal membaca tab '{worksheet_name}': {e}")
    return pd.DataFrame(columns=default_cols)

def save_worksheet(df, worksheet_name, state_key):
    st.session_state[state_key] = df
    if GSHEETS_AVAILABLE:
        try:
            conn = st.connection("gsheets", type=GSheetsConnection)
            conn.update(worksheet=worksheet_name, data=df)
            st.toast(f"✅ Berhasil disimpan ke Google Sheets ({worksheet_name})!")
            return True
        except Exception as e:
            st.error(f"❌ GAGAL SIMPAN KE GOOGLE SHEETS: {e}")
            return False
    return False

# Init Data ke Session State
if "df_users" not in st.session_state:
    st.session_state["df_users"] = load_worksheet("Users", COLS_USERS)

if "df_workout" not in st.session_state:
    st.session_state["df_workout"] = load_worksheet("Workout_Logs", COLS_WORKOUT)

if "df_habits" not in st.session_state:
    st.session_state["df_habits"] = load_worksheet("Habits_Logs", COLS_HABITS)

if "df_weekly" not in st.session_state:
    st.session_state["df_weekly"] = load_worksheet("Weekly_Logs", COLS_WEEKLY)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "user_fullname" not in st.session_state:
    st.session_state["user_fullname"] = ""
if "user_photo" not in st.session_state:
    st.session_state["user_photo"] = ""

# ----------------------------------------------------
# 4. HALAMAN LOGIN & REGISTER
# ----------------------------------------------------
if not st.session_state["logged_in"]:
    st.title("🏋️‍♂️ Gym & Running Progress Tracker")
    st.subheader("Silakan Login atau Buat Akun Baru")

    tab_login, tab_register = st.tabs(["🔑 Login", "📝 Buat Akun Baru"])

    with tab_login:
        login_user = st.text_input("Username", key="login_u").strip().lower()
        login_pass = st.text_input("Password", type="password", key="login_p")
        if st.button("Masuk / Login", type="primary"):
            df_u = st.session_state["df_users"]
            matched_user = df_u[(df_u["Username"].astype(str).str.lower() == login_user) & (df_u["Password"].astype(str) == login_pass)]
            if not matched_user.empty:
                st.session_state["logged_in"] = True
                st.session_state["username"] = login_user
                st.session_state["user_fullname"] = matched_user.iloc[0]["Nama"]
                st.session_state["user_photo"] = str(matched_user.iloc[0].get("Foto", ""))
                st.success(f"Selamat datang kembali, {st.session_state['user_fullname']}!")
                st.rerun()
            else:
                st.error("❌ Username atau Password salah!")

    with tab_register:
        reg_name = st.text_input("Nama Lengkap", key="reg_n")
        reg_user = st.text_input("Username Baru (Tanpa Spasi)", key="reg_u").strip().lower()
        reg_pass = st.text_input("Password Baru", type="password", key="reg_p")
        
        if st.button("Daftar Akun Baru"):
            df_u = st.session_state["df_users"]
            if not reg_user or not reg_pass or not reg_name:
                st.error("⚠️ Semua kolom wajib diisi!")
            elif reg_user in df_u["Username"].astype(str).str.lower().values:
                st.error("⚠️ Username sudah terpakai, silakan pakai username lain!")
            else:
                new_user = {"Username": reg_user, "Password": reg_pass, "Nama": reg_name, "Foto": ""}
                df_updated = pd.concat([df_u, pd.DataFrame([new_user])], ignore_index=True)
                save_worksheet(df_updated, "Users", "df_users")
                st.success("🎉 Akun berhasil dibuat! Silakan pindah ke tab Login untuk masuk.")

    st.stop()

# ----------------------------------------------------
# 5. APLIKASI UTAMA (SETELAH USER LOGIN)
# ----------------------------------------------------
current_user = st.session_state["username"]
user_fullname = st.session_state["user_fullname"]
user_photo = st.session_state["user_photo"]

# TAMPILAN SIDEBAR
if user_photo and str(user_photo).strip() != "":
    st.sidebar.image(user_photo, width=120)
else:
    st.sidebar.title("👤")

st.sidebar.markdown(f"### {user_fullname}")
st.sidebar.caption(f"Logged as: @{current_user}")

if st.sidebar.button("🚪 Logout / Keluar"):
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["user_fullname"] = ""
    st.session_state["user_photo"] = ""
    st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Sync Data Google Sheets"):
    st.session_state["df_users"] = load_worksheet("Users", COLS_USERS)
    st.session_state["df_workout"] = load_worksheet("Workout_Logs", COLS_WORKOUT)
    st.session_state["df_habits"] = load_worksheet("Habits_Logs", COLS_HABITS)
    st.session_state["df_weekly"] = load_worksheet("Weekly_Logs", COLS_WEEKLY)
    st.rerun()

st.title("🏋️️‍♂️ Gym & 🏃‍♂️ Running Progress Tracker")

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

menu = st.sidebar.radio(
    "Pilih Halaman:", 
    ["📋 Program Latihan", "🏋️‍♂️ Input Workout Log", "🥗 Daily Habits", "📈 Progress Mingguan", "📊 Dashboard Stats", "⚙️ Pengaturan"]
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
    st.subheader("🏋️‍♂️ / 🏃‍♂️️ Catat Sesi Latihan & Running Harian")
    
    c1, c2, c3 = st.columns(3)
    tanggal = c1.date_input("Tanggal", datetime.date.today())
    hari = c2.selectbox("Hari", ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"])
    sesi = c3.selectbox("Sesi Latihan", ["Upper A", "Lower A", "Upper B", "Lower B", "Running", "Custom Strength"])

    if sesi == "Running":
        dropdown_options = ["Easy Run", "Interval Run", "Tempo Run", "Long Run", "Treadmill Run", "(Ketik Manual)"]
    elif sesi in PROGRAM_DATA:
        dropdown_options = [e["Exercise"] for e in PROGRAM_DATA[sesi]] + ["(Ketik Manual)"]
    else:
        dropdown_options = ["(Ketik Manual)", "Bench Press", "Squat", "Deadlift", "Overhead Press", "Pull Up"]

    exercise_choice = st.selectbox("Pilih Gerakan / Jenis Lari", dropdown_options)
    
    if exercise_choice == "(Ketik Manual)":
        exercise_custom = st.text_input("Nama Gerakan / Sesi (Ketik Manual)")
        exercise_final = exercise_custom.strip()
    else:
        exercise_final = exercise_choice

    st.markdown("---")

    if sesi == "Running":
        st.markdown("### 🏃‍♂️ Parameter Running")
        rc1, rc2, rc3 = st.columns(3)
        jarak = rc1.number_input("Jarak Lari (km)", min_value=0.1, value=5.0, step=0.1, format="%.2f")
        waktu_menit = rc2.number_input("Waktu Tempuh (Menit)", min_value=1.0, value=30.0, step=0.5)
        
        if jarak > 0:
            pace_decimal = waktu_menit / jarak
            pace_min = int(pace_decimal)
            pace_sec = int(round((pace_decimal - pace_min) * 60))
            if pace_sec == 60:
                pace_min += 1
                pace_sec = 0
            pace_str = f"{pace_min}'{pace_sec:02d}\"/km"
        else:
            pace_str = "0'00\"/km"

        rc3.metric("⏱️ Pace Otomatis", pace_str)

        rc4, rc5 = st.columns(2)
        rpe = rc4.number_input("RPE / Effort (1-10)", min_value=1, max_value=10, value=7)
        catatan = rc5.text_input("Catatan Lari (Misal: Heart Rate, Rute, Cuaca)")

        if st.button("➕ Simpan Sesi Running", type="primary"):
            if not exercise_final:
                st.error("⚠️ Silakan pilih atau ketik jenis lari terlebih dahulu!")
            else:
                new_entry = {
                    "User": current_user,
                    "Tanggal": tanggal.strftime("%Y-%m-%d"), 
                    "Hari": hari, 
                    "Sesi": sesi,
                    "Exercise": exercise_final, 
                    "Set": 1, 
                    "Reps": f"{waktu_menit} min", 
                    "Beban (kg)": jarak, 
                    "RIR": pace_str, 
                    "RPE": rpe, 
                    "Est. 1RM": "-",
                    "Catatan": catatan
                }
                df_updated = pd.concat([st.session_state["df_workout"], pd.DataFrame([new_entry])], ignore_index=True)
                save_worksheet(df_updated, "Workout_Logs", "df_workout")
                st.success(f"🏃‍♂️ Sesi Running ({exercise_final} - {jarak} km) tersimpan!")

    else:
        st.markdown("### 🏋️‍♂️ Parameter Angkatan")
        c4, c5, c6, c7, c8 = st.columns(5)
        set_num = c4.number_input("Set Ke-", min_value=1, value=1)
        reps = c5.number_input("Reps (Ulang)", min_value=1, value=10)
        beban = c6.number_input("Beban (kg)", min_value=0.0, value=20.0, step=0.5)
        rir = c7.number_input("RIR (0-5)", min_value=0, max_value=5, value=2)
        rpe = c8.number_input("RPE (1-10)", min_value=1, max_value=10, value=10-rir)

        est_1rm_val = calculate_1rm(beban, reps)
        st.caption(f"💡 **Est. 1RM (Satu Angkatan Maksimal):** {est_1rm_val} kg")

        catatan = st.text_input("Catatan Set / Form / Sensasi Otot")

        if st.button("➕ Simpan Set Latihan", type="primary"):
            if not exercise_final:
                st.error("⚠️ Silakan pilih atau ketik nama gerakan terlebih dahulu!")
            else:
                # 🥇 CEK PERSONAL RECORD (PR)
                df_all = st.session_state["df_workout"]
                mask_ex = (df_all["User"] == current_user) & (df_all["Exercise"] == exercise_final) & (df_all["Sesi"] != "Running")
                df_prev_ex = df_all[mask_ex]
                
                is_pr = False
                if not df_prev_ex.empty:
                    max_prev_beban = pd.to_numeric(df_prev_ex["Beban (kg)"], errors='coerce').max()
                    if pd.notnull(max_prev_beban) and beban > max_prev_beban and beban > 0:
                        is_pr = True
                elif beban > 0:
                    is_pr = True

                new_entry = {
                    "User": current_user,
                    "Tanggal": tanggal.strftime("%Y-%m-%d"), 
                    "Hari": hari, 
                    "Sesi": sesi,
                    "Exercise": exercise_final, 
                    "Set": set_num, 
                    "Reps": reps, 
                    "Beban (kg)": beban, 
                    "RIR": rir, 
                    "RPE": rpe, 
                    "Est. 1RM": est_1rm_val,
                    "Catatan": catatan
                }
                df_updated = pd.concat([df_all, pd.DataFrame([new_entry])], ignore_index=True)
                save_worksheet(df_updated, "Workout_Logs", "df_workout")

                if is_pr:
                    st.balloons()
                    st.success(f"🎉 **REKOR BARU (PR)!** Kamu berhasil memecahkan rekor angkatan {exercise_final} dengan beban {beban} kg!")
                else:
                    st.success(f"✅ Set {set_num} ({exercise_final}) tersimpan!")

        # ⏱️ WIDGET REST TIMER
        st.markdown("---")
        with st.expander("⏱️ Timer Istirahat Antar Set (Rest Timer)"):
            st.caption("Pilih durasi istirahat untuk memulai hitung mundur:")
            t_col1, t_col2, t_col3, t_col4 = st.columns(4)
            if t_col1.button("⏱️ 60 Detik"):
                run_rest_timer(60)
            if t_col2.button("⏱️ 90 Detik"):
                run_rest_timer(90)
            if t_col3.button("⏱️ 120 Detik"):
                run_rest_timer(120)
            if t_col4.button("⏱️ 180 Detik"):
                run_rest_timer(180)

    st.markdown("---")
    st.subheader(f"📜 Riwayat Workout & Running (@{current_user})")
    
    df_all_workout = st.session_state["df_workout"]
    df_user_workout_idx = df_all_workout[df_all_workout["User"] == current_user]

    if not df_user_workout_idx.empty:
        st.dataframe(df_user_workout_idx.reset_index(drop=True), use_container_width=True)

        with st.expander("🗑️ Hapus Baris Log Latihan"):
            st.caption("Pilih baris log yang salah dimasukkan untuk dihapus secara permanen.")
            log_options = {
                f"[{row['Tanggal']}] {row['Sesi']} - {row['Exercise']} (Set {row['Set']} | {row['Beban (kg)']}kg x {row['Reps']})": orig_idx 
                for orig_idx, row in df_user_workout_idx.iterrows()
            }
            selected_log_label = st.selectbox("Pilih log yang ingin dihapus:", list(log_options.keys()))
            if st.button("🔴 Hapus Log Ini", type="secondary"):
                target_orig_index = log_options[selected_log_label]
                df_updated = df_all_workout.drop(target_orig_index).reset_index(drop=True)
                success = save_worksheet(df_updated, "Workout_Logs", "df_workout")
                if success:
                    st.success("✅ Log latihan berhasil dihapus!")
                    st.rerun()
    else:
        st.info("Belum ada data latihan / running terdaftar untuk akun kamu.")

# ----------------------------------------------------
# MENU 3: DAILY HABITS
# ----------------------------------------------------
elif "Daily Habits" in menu:
    st.subheader("🥗 Daily Habits Tracker (Kebiasaan Harian)")
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

    if st.button("💾 Simpan Kebiasaan Harian", type="primary"):
        h_entry = {
            "User": current_user,
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
        df_updated = pd.concat([st.session_state["df_habits"], pd.DataFrame([h_entry])], ignore_index=True)
        save_worksheet(df_updated, "Habits_Logs", "df_habits")

    st.markdown("---")
    st.subheader(f"📜 Riwayat Kebiasaan Harian (@{current_user})")
    df_all_habits = st.session_state["df_habits"]
    df_user_habits_idx = df_all_habits[df_all_habits["User"] == current_user]

    if not df_user_habits_idx.empty:
        st.dataframe(df_user_habits_idx.reset_index(drop=True), use_container_width=True)

        with st.expander("🗑️ Hapus Baris Log Kebiasaan"):
            st.caption("Pilih baris log kebiasaan harian yang ingin dihapus:")
            habit_options = {
                f"[{row['Tanggal']}] Energi: {row['Energi']}/5 | Recovery: {row['Recovery']}/5": orig_idx 
                for orig_idx, row in df_user_habits_idx.iterrows()
            }
            selected_h_label = st.selectbox("Pilih log kebiasaan:", list(habit_options.keys()))
            if st.button("🔴 Hapus Log Kebiasaan Ini", type="secondary"):
                target_idx = habit_options[selected_h_label]
                df_updated = df_all_habits.drop(target_idx).reset_index(drop=True)
                if save_worksheet(df_updated, "Habits_Logs", "df_habits"):
                    st.success("✅ Log kebiasaan berhasil dihapus!")
                    st.rerun()
    else:
        st.info("Belum ada data kebiasaan harian.")

# ----------------------------------------------------
# MENU 4: PROGRESS MINGGUAN
# ----------------------------------------------------
elif "Progress Mingguan" in menu:
    st.subheader("📈 Rekap Evaluasi Mingguan")
    minggu = st.text_input("Minggu Ke- / Periode", "Minggu 1")
    c1, c2, c3 = st.columns(3)
    up = c1.number_input("Total Sesi Upper Selesai", min_value=0, value=2)
    low = c2.number_input("Total Sesi Lower Selesai", min_value=0, value=2)
    tidur_avg = c3.number_input("Tidur Rata-rata (Jam)", value=7.5)

    e1, e2 = st.columns(2)
    en_avg = e1.slider("Rata-rata Energi Mingguan (1-5)", 1.0, 5.0, 4.0)
    rec_avg = e2.slider("Rata-rata Recovery Mingguan (1-5)", 1.0, 5.0, 4.0)
    cat_w = st.text_input("Catatan Progres / Rencana Naik Beban")

    if st.button("📌 Simpan Rekap Mingguan", type="primary"):
        w_entry = {
            "User": current_user,
            "Minggu": minggu, 
            "Latihan Upper": up, 
            "Latihan Lower": low,
            "Total Sesi": up + low, 
            "Tidur Rata-rata": tidur_avg,
            "Energi": en_avg, 
            "Recovery": rec_avg, 
            "Catatan": cat_w
        }
        df_updated = pd.concat([st.session_state["df_weekly"], pd.DataFrame([w_entry])], ignore_index=True)
        save_worksheet(df_updated, "Weekly_Logs", "df_weekly")

    st.markdown("---")
    st.subheader(f"📜 Riwayat Evaluasi Mingguan (@{current_user})")
    df_all_weekly = st.session_state["df_weekly"]
    df_user_weekly_idx = df_all_weekly[df_all_weekly["User"] == current_user]

    if not df_user_weekly_idx.empty:
        st.dataframe(df_user_weekly_idx.reset_index(drop=True), use_container_width=True)

        with st.expander("🗑️️ Hapus Baris Rekap Mingguan"):
            st.caption("Pilih rekap mingguan yang ingin dihapus:")
            weekly_options = {
                f"[{row['Minggu']}] Total Sesi: {row['Total Sesi']} | Tidur Avg: {row['Tidur Rata-rata']} Jam": orig_idx 
                for orig_idx, row in df_user_weekly_idx.iterrows()
            }
            selected_w_label = st.selectbox("Pilih rekap mingguan:", list(weekly_options.keys()))
            if st.button("🔴 Hapus Rekap Mingguan Ini", type="secondary"):
                target_idx = weekly_options[selected_w_label]
                df_updated = df_all_weekly.drop(target_idx).reset_index(drop=True)
                if save_worksheet(df_updated, "Weekly_Logs", "df_weekly"):
                    st.success("✅ Rekap mingguan berhasil dihapus!")
                    st.rerun()
    else:
        st.info("Belum ada rekap mingguan.")

# ----------------------------------------------------
# MENU 5: DASHBOARD STATS
# ----------------------------------------------------
elif "Dashboard Stats" in menu:
    st.subheader(f"📊 Dashboard Progress (@{current_user})")
    df_user_workout = st.session_state["df_workout"][st.session_state["df_workout"]["User"] == current_user]

    if not df_user_workout.empty:
        df_gym = df_user_workout[df_user_workout["Sesi"] != "Running"].copy()
        df_run = df_user_workout[df_user_workout["Sesi"] == "Running"].copy()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Set Gym", len(df_gym))
        
        if not df_gym.empty:
            df_gym["Beban_num"] = pd.to_numeric(df_gym["Beban (kg)"], errors='coerce').fillna(0)
            df_gym["Reps_num"] = pd.to_numeric(df_gym["Reps"], errors='coerce').fillna(0)
            vol = (df_gym["Beban_num"] * df_gym["Reps_num"]).sum()
            col2.metric("Total Volume Gym", f"{vol:,.0f} kg")
        else:
            col2.metric("Total Volume Gym", "0 kg")

        if not df_run.empty:
            df_run["Jarak_num"] = pd.to_numeric(df_run["Beban (kg)"], errors='coerce').fillna(0)
            total_km = df_run["Jarak_num"].sum()
            col3.metric("Total Jarak Lari", f"{total_km:.1f} km")
        else:
            col3.metric("Total Jarak Lari", "0 km")

        col4.metric("Variasi Gerakan", df_user_workout["Exercise"].nunique())

        st.markdown("---")

        # 🥇 HIGHLIGHT PERSONAL RECORDS (PR)
        if not df_gym.empty:
            st.markdown("### 🥇 Rekor Angkatan Terberat (PR)")
            pr_df = df_gym.groupby("Exercise")["Beban_num"].max().reset_index()
            pr_df.columns = ["Nama Gerakan", "Beban Terberat (kg)"]
            st.dataframe(pr_df.sort_values(by="Beban Terberat (kg)", ascending=False), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("📈 Progress Beban Angkatan Gym (kg)")
            st.line_chart(df_gym, x="Tanggal", y="Beban (kg)", color="Exercise")

        if not df_run.empty:
            st.subheader("🏃‍♂️ Progress Jarak Lari (km)")
            st.line_chart(df_run, x="Tanggal", y="Beban (kg)", color="Exercise")

        # 📥 DOWNLOAD CSV BUTTON
        st.markdown("---")
        st.markdown("### 📥 Unduh Arsip Data")
        csv_data = df_user_workout.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Log Workout (.CSV)",
            data=csv_data,
            file_name=f"workout_log_{current_user}.csv",
            mime="text/csv",
            type="primary"
        )
    else:
        st.warning("⚠️ Belum ada data latihan / running yang dicatat untuk akun kamu.")

# ----------------------------------------------------
# MENU 6: PENGATURAN (SETTINGS)
# ----------------------------------------------------
elif "Pengaturan" in menu:
    st.subheader("⚙️ Pengaturan Akun & Profil")

    tab_profile, tab_security, tab_export = st.tabs(["👤 Edit Profil & Foto", "🔒 Keamanan & Password", "📥 Ekspor Data"])

    # TAB 1: EDIT PROFIL & FOTO
    with tab_profile:
        st.markdown("### 👤 Ubah Profil Pengguna")
        col_img, col_form = st.columns([1, 3])
        
        with col_img:
            if user_photo and str(user_photo).strip() != "":
                st.image(user_photo, caption="Foto Saat Ini", width=140)
            else:
                st.info("Belum ada foto profil")

        with col_form:
            st.text_input("Username", value=current_user, disabled=True)
            new_fullname = st.text_input("Nama Lengkap", value=user_fullname)
            uploaded_file = st.file_uploader("Unggah Foto Profil Baru (JPG/PNG)", type=["jpg", "jpeg", "png"])

        if st.button("💾 Simpan Perubahan Profil", type="primary"):
            if new_fullname.strip():
                df_u = st.session_state["df_users"]
                idx = df_u[df_u["Username"].astype(str).str.lower() == current_user].index
                
                if not idx.empty:
                    target_idx = idx[0]
                    df_u.loc[target_idx, "Nama"] = new_fullname.strip()
                    st.session_state["user_fullname"] = new_fullname.strip()

                    if uploaded_file is not None:
                        photo_b64 = process_and_compress_image(uploaded_file)
                        if photo_b64:
                            df_u.loc[target_idx, "Foto"] = photo_b64
                            st.session_state["user_photo"] = photo_b64

                    success = save_worksheet(df_u, "Users", "df_users")
                    if success:
                        st.success("✅ Profil berhasil diperbarui!")
                        st.rerun()
            else:
                st.error("⚠️ Nama lengkap tidak boleh kosong!")

    # TAB 2: UBAH PASSWORD
    with tab_security:
        st.markdown("### 🔒 Ubah Kata Sandi (Password)")
        old_pass = st.text_input("Password Saat Ini", type="password")
        new_pass = st.text_input("Password Baru", type="password")
        confirm_pass = st.text_input("Konfirmasi Password Baru", type="password")

        if st.button("🔑 Perbarui Password", type="primary"):
            df_u = st.session_state["df_users"]
            user_mask = df_u["Username"].astype(str).str.lower() == current_user
            user_row = df_u[user_mask]

            if user_row.empty or str(user_row.iloc[0]["Password"]) != old_pass:
                st.error("❌ Password saat ini tidak sesuai!")
            elif not new_pass.strip():
                st.error("⚠️ Password baru tidak boleh kosong!")
            elif new_pass != confirm_pass:
                st.error("❌ Konfirmasi password baru tidak cocok!")
            else:
                idx = user_row.index[0]
                df_u.loc[idx, "Password"] = new_pass
                success = save_worksheet(df_u, "Users", "df_users")
                if success:
                    st.success("🎉 Password berhasil diperbarui!")

    # TAB 3: EKSPOR DATA
    with tab_export:
        st.markdown("### 📥 Unduh Semua Data Kamu")
        st.caption("Kamu bisa mengunduh riwayat lengkap dalam format file `.csv` kapan saja.")

        df_u_w = st.session_state["df_workout"][st.session_state["df_workout"]["User"] == current_user]
        df_u_h = st.session_state["df_habits"][st.session_state["df_habits"]["User"] == current_user]
        df_u_wk = st.session_state["df_weekly"][st.session_state["df_weekly"]["User"] == current_user]

        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.download_button(
                "📥 Log Workout (.csv)", 
                data=df_u_w.to_csv(index=False).encode('utf-8'),
                file_name=f"workout_{current_user}.csv", 
                mime="text/csv"
            )
        with col_d2:
            st.download_button(
                "📥 Daily Habits (.csv)", 
                data=df_u_h.to_csv(index=False).encode('utf-8'),
                file_name=f"habits_{current_user}.csv", 
                mime="text/csv"
            )
        with col_d3:
            st.download_button(
                "📥 Progress Mingguan (.csv)", 
                data=df_u_wk.to_csv(index=False).encode('utf-8'),
                file_name=f"weekly_{current_user}.csv", 
                mime="text/csv"
            )
