import streamlit as st
import pandas as pd
import datetime
import base64
import io
from PIL import Image

# ----------------------------------------------------
# 1. KONFIGURASI HALAMAN APLIKASI
# ----------------------------------------------------
st.set_page_config(
    page_title="Gym & Running Progress Tracker", 
    layout="wide", 
    page_icon="🏋️‍♂️"
)

# ----------------------------------------------------
# 2. HELPER FUNGSI FOTO PROFIL (BASE64)
# ----------------------------------------------------
def process_and_compress_image(uploaded_file):
    """Mengecilkan foto & mengubah ke string Base64 agar hemat ruang di Google Sheets"""
    try:
        img = Image.open(uploaded_file)
        img = img.convert("RGB")
        img.thumbnail((200, 200))  # Resize maksimal 200x200 pixel
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=80)
        b64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64_str}"
    except Exception as e:
        st.error(f"Gagal memproses gambar: {e}")
        return ""

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
COLS_WORKOUT = ["User", "Tanggal", "Hari", "Sesi", "Exercise", "Set", "Reps", "Beban (kg)", "RIR", "RPE", "Catatan"]
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
# 4. HALAMAN LOGIN, REGISTER & LUPA PASSWORD
# ----------------------------------------------------
if not st.session_state["logged_in"]:
    st.title("🏋️‍♂️ Gym & Running Progress Tracker")
    st.subheader("Silakan Login atau Buat Akun Baru")

    tab_login, tab_register, tab_forgot = st.tabs(["🔑 Login", "📝 Buat Akun Baru", "❓ Lupa Password"])

    # TAB LOGIN
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

    # TAB REGISTER
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

    # TAB LUPA PASSWORD
    with tab_forgot:
        st.markdown("### 🔑 Reset Password")
        st.caption("Masukkan username dan nama lengkap sesuai saat pendaftaran untuk reset password.")
        
        forgot_user = st.text_input("Username", key="forgot_u").strip().lower()
        forgot_name = st.text_input("Nama Lengkap (Sesuai Akun)", key="forgot_n").strip()
        forgot_new_pass = st.text_input("Password Baru", type="password", key="forgot_p")
        forgot_confirm_pass = st.text_input("Konfirmasi Password Baru", type="password", key="forgot_cp")

        if st.button("🔑 Reset Password", type="primary"):
            if not forgot_user or not forgot_name or not forgot_new_pass:
                st.error("⚠️ Semua kolom wajib diisi!")
            elif forgot_new_pass != forgot_confirm_pass:
                st.error("❌ Konfirmasi password baru tidak cocok!")
            else:
                df_u = st.session_state["df_users"]
                # Verifikasi Username & Nama Lengkap (case-insensitive)
                mask = (df_u["Username"].astype(str).str.lower() == forgot_user) & (df_u["Nama"].astype(str).str.strip().str.lower() == forgot_name.lower())
                matched_user = df_u[mask]

                if matched_user.empty:
                    st.error("❌ Username atau Nama Lengkap tidak cocok dengan data kami!")
                else:
                    target_idx = matched_user.index[0]
                    df_u.loc[target_idx, "Password"] = forgot_new_pass
                    success = save_worksheet(df_u, "Users", "df_users")
                    if success:
                        st.success("🎉 Password berhasil diperbarui! Silakan kembali ke tab **🔑 Login** untuk masuk.")

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

st.title("🏋️‍♂️ Gym & 🏃‍♂️ Running Progress Tracker")

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
    st.subheader("🏋️‍♂️ / 🏃‍♂️ Catat Sesi Latihan & Running Harian")
    
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

        catatan = st.text_input("Catatan Set / Form / Sensasi Otot")

        if st.button("➕ Simpan Set Latihan", type="primary"):
            if not exercise_final:
                st.error("⚠️ Silakan pilih atau ketik nama gerakan terlebih dahulu!")
            else:
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
                    "Catatan": catatan
                }
                df_updated = pd.concat([st.session_state["df_workout"], pd.DataFrame([new_entry])], ignore_index=True)
                save_worksheet(df_updated, "Workout_Logs", "df_workout")
                st.success(f"✅ Set {set_num} ({exercise_final}) tersimpan!")

    st.markdown("---")
    st.subheader(f"📜 Riwayat Workout & Running (@{current_user})")
    
    df_all_workout = st.session_state["df_workout"]
    df_user_workout_idx = df_all_workout[df_all_workout["User"] == current_user]

    if not df_user_workout_idx.empty:
        st.dataframe(df_user_workout_idx.reset_index(drop=True), use_container_width=True)

        with st.expander("🗑️️ Hapus Baris Log Latihan"):
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
                    st.success("✅ Log latihan berhasil dihapus dari Google Sheets!")
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
    df_user_habits = st.session_state["df_habits"][st.session_state["df_habits"]["User"] == current_user]
    st.dataframe(df_user_habits, use_container_width=True)

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
    df_user_weekly = st.session_state["df_weekly"][st.session_state["df_weekly"]["User"] == current_user]
    st.dataframe(df_user_weekly, use_container_width=True)

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
            col3.metric("Total Jarak Lari", "0 kg")

        col4.metric("Variasi Gerakan", df_user_workout["Exercise"].nunique())

        st.markdown("---")
        if not df_gym.empty:
            st.subheader("📈 Kenaikan Beban Angkatan Gym")
            st.line_chart(df_gym, x="Tanggal", y="Beban (kg)", color="Exercise")

        if not df_run.empty:
            st.subheader("🏃‍♂️ Progress Jarak Lari (km)")
            st.line_chart(df_run, x="Tanggal", y="Beban (kg)", color="Exercise")
    else:
        st.warning("⚠️ Belum ada data latihan / running yang dicatat untuk akun kamu.")

# ----------------------------------------------------
# MENU 6: PENGATURAN (SETTINGS)
# ----------------------------------------------------
elif "Pengaturan" in menu:
    st.subheader("⚙️ Pengaturan Akun & Profil")

    tab_profile, tab_security = st.tabs(["👤 Edit Profil & Foto", "🔒 Keamanan & Password"])

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
