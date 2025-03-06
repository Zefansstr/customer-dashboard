import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import re

# Konfigurasi tema dark mode
st.set_page_config(page_title="Customer Segmentation", layout="wide")

# Autentikasi Login
USER_CREDENTIALS = {"Check8899": "889900"}

# Fungsi logout
def logout():
    st.session_state.clear()
    st.rerun()

# Cek apakah sudah login
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.sidebar.title("🔑 Login")
    username = st.sidebar.text_input("👤 Username")
    password = st.sidebar.text_input("🔒 Password", type="password")
    
    if st.sidebar.button("Login"):
        if username in USER_CREDENTIALS and password == USER_CREDENTIALS[username]:
            st.session_state["logged_in"] = True
            st.session_state["username"] = username
            st.success("✅ Login berhasil! Selamat datang.")
            st.rerun()
        else:
            st.error("❌ Login gagal! Periksa username dan password.")
else:
    # Tombol logout
    st.sidebar.button("Logout", on_click=logout)
    
    # Membaca data dari CSV
    df = pd.read_csv("member_report.csv")

    # Membersihkan nama kolom untuk menghindari spasi atau karakter tidak terlihat
    df.columns = df.columns.str.strip()

    # Menghapus duplikat berdasarkan Username
    if 'Username' in df.columns:
        df = df.drop_duplicates(subset=['Username'], keep='first')

    # Menghapus pelanggan yang tidak memiliki Deposit Amount dan Withdraw Amount
    df = df[(df['Deposit Amount'] > 0) | (df['Withdraw Amount'] > 0)]

    # Menghitung selisih transaksi (Net Amount)
    df['Net Amount'] = df['Deposit Amount'] - df['Withdraw Amount']

    # Menghitung Profit (Profit = Net Amount jika positif, jika tidak 0)
    df['Profit'] = df['Deposit Amount'] - df['Withdraw Amount']

    # Menentukan kategori berdasarkan batas Deposit Amount yang ditentukan
    def categorize(amount):
        if amount > 5000:
            return 'AAA'
        elif amount <= 5000 and amount > 3000:
            return 'A'
        elif amount <= 3000 and amount > 2000:
            return 'B'
        elif amount <= 2000 and amount > 1000:
            return 'C'
        else:
            return 'D'

    # Menentukan kategori berdasarkan Net Amount
    def categorize_net(net_amount):
        if net_amount > 5000:
            return 'High Surplus'
        elif net_amount > 0:
            return 'Surplus'
        elif net_amount == 0:
            return 'Balanced'
        else:
            return 'Deficit'

    # Menentukan apakah withdraw amount lebih dari 50% dari deposit
    df['High Withdraw'] = df['Withdraw Amount'] > (df['Deposit Amount'] * 0.5)

    # Menentukan VIP & High Risk Customers
    df['VIP'] = df['Deposit Amount'] > 10000
    df['High Risk'] = (df['Withdraw Amount'] / df['Deposit Amount']) > 0.9

    # Pastikan kolom sesuai dengan nama di dataset
    if 'Deposit Amount' in df.columns:
        df['Grade'] = df['Deposit Amount'].apply(categorize)
        df['Net Category'] = df['Net Amount'].apply(categorize_net)
    else:
        st.error("Kolom 'Deposit Amount' tidak ditemukan dalam dataset. Periksa nama kolom di file CSV.")

    # Membuat menu navigasi di sidebar dengan ikon
    st.sidebar.title("📌 Menu Navigasi")
    menu = st.sidebar.radio("📊 Pilih Halaman:", ["📊 Dashboard", "📋 Tabel Segmentation", "📥 Unduh Data"])

    if menu == "📊 Dashboard":
        st.title("📊 Customer Segmentation Dashboard")
        st.write("Selamat datang di dashboard analisis customer segmentation.")
        
        # Menampilkan ringkasan angka penting dalam dua kolom
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Deposit", f"RM{df['Deposit Amount'].sum():,.2f}")
            st.metric("Total Withdraw", f"RM{df['Withdraw Amount'].sum():,.2f}")
        with col2:
            st.metric("Total Pelanggan", len(df))
            st.metric("Total Profit", f"RM{df['Profit'].sum():,.2f}")
        
        # Grafik Profit per Grade dalam expander
        with st.expander("📊 Lihat Grafik Profit per Grade"):
            st.subheader("Total Profit per Grade")
            fig, ax = plt.subplots()
            df.groupby('Grade')['Profit'].sum().plot(kind='bar', ax=ax)
            st.pyplot(fig)
        
        # Perbandingan Deposit vs Withdraw per Grade dalam expander
        with st.expander("📊 Lihat Perbandingan Deposit vs Withdraw"):
            st.subheader("Perbandingan Deposit vs Withdraw per Grade")
            fig, ax = plt.subplots()
            df.groupby('Grade')[['Deposit Amount', 'Withdraw Amount']].sum().plot(kind='bar', stacked=True, ax=ax)
            st.pyplot(fig)
        
    elif menu == "📋 Tabel Segmentation":
        st.title("📋 Tabel Customer Segmentation")
        
        # Filter Username dan Net Category
        selected_username = st.text_input("🔎 Cari Username:", "")
        selected_net_category = st.selectbox("📌 Pilih Kategori Net Amount:", ["Semua"] + list(df["Net Category"].unique()))
        show_vip = st.checkbox("⭐ Tampilkan Hanya VIP")
        
        filtered_df = df.copy()
        if selected_username:
            filtered_df = filtered_df[filtered_df["Username"].apply(lambda x: bool(re.search(selected_username, x, re.IGNORECASE)))]
        if selected_net_category != "Semua":
            filtered_df = filtered_df[filtered_df["Net Category"] == selected_net_category]
        if show_vip:
            filtered_df = filtered_df[filtered_df["VIP"]]
        
        for grade in ['AAA', 'A', 'B', 'C', 'D']:
            st.subheader(f"Grade {grade}")
            grade_df = filtered_df[filtered_df['Grade'] == grade]
            
            if grade_df.empty:
                st.write("🚨 Tidak ada pelanggan di kategori ini.")
            else:
                st.dataframe(grade_df)
                st.write(f"**Total Members in Grade {grade}: {len(grade_df)}**")
        
    elif menu == "📥 Unduh Data":
        st.title("📥 Unduh Data Customer")
        st.download_button(
            label="📥 Download Data CSV",
            data=df.to_csv(index=False).encode('utf-8'),
            file_name="customer_segmentation.csv",
            mime="text/csv"
        )