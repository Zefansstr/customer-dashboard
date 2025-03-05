import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

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

# Menghitung Profit (anggap Profit = 10% dari Deposit Amount)
df['Profit'] = df['Net Amount']

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
df['VIP'] = df['Deposit Amount'] > 20000
df['High Risk'] = (df['Withdraw Amount'] / df['Deposit Amount']) > 0.9

# Pastikan kolom sesuai dengan nama di dataset
if 'Deposit Amount' in df.columns:
    df['Grade'] = df['Deposit Amount'].apply(categorize)
    df['Net Category'] = df['Net Amount'].apply(categorize_net)
else:
    st.error("Kolom 'Deposit Amount' tidak ditemukan dalam dataset. Periksa nama kolom di file CSV.")

# Membuat menu navigasi di sidebar
st.sidebar.title("Menu Navigasi")
menu = st.sidebar.radio("Pilih Halaman:", ["Dashboard", "Tabel Segmentation", "Unduh Data"])

if menu == "Dashboard":
    st.title("Customer Segmentation Dashboard")
    st.write("Selamat datang di dashboard analisis customer segmentation.")
    
    # Menampilkan ringkasan angka penting
    st.metric("Total Deposit", f"RM{df['Deposit Amount'].sum():,.2f}")
    st.metric("Total Withdraw", f"RM{df['Withdraw Amount'].sum():,.2f}")
    st.metric("Total Pelanggan", len(df))
    st.metric("Total Profit", f"RM{df['Profit'].sum():,.2f}")
    
    # Analisis Visualisasi di Dashboard
    st.subheader("Distribusi Pelanggan per Grade")
    grade_counts = df['Grade'].value_counts()
    fig, ax = plt.subplots()
    ax.pie(grade_counts, labels=grade_counts.index, autopct='%1.1f%%', startangle=90)
    st.pyplot(fig)

    st.subheader("Total Deposit per Grade")
    fig, ax = plt.subplots()
    df.groupby('Grade')['Deposit Amount'].sum().plot(kind='bar', ax=ax)
    st.pyplot(fig)
    
    # Menampilkan Top 10 Pelanggan berdasarkan Deposit dan Withdraw
    st.subheader("Top 10 Pelanggan dengan Deposit Tertinggi")
    top_deposit = df.nlargest(10, 'Deposit Amount')[['Username', 'Deposit Amount']]
    st.dataframe(top_deposit)
    
    st.subheader("Top 10 Pelanggan dengan Withdraw Tertinggi")
    top_withdraw = df.nlargest(10, 'Withdraw Amount')[['Username', 'Withdraw Amount']]
    st.dataframe(top_withdraw)
    
elif menu == "Tabel Segmentation":
    st.title("Tabel Customer Segmentation")
    
    # Filter Username dan Net Category
    selected_username = st.text_input("Cari Username:", "")
    selected_net_category = st.selectbox("Pilih Kategori Net Amount:", ["Semua"] + list(df["Net Category"].unique()))
    show_vip = st.checkbox("Tampilkan Hanya VIP")
    
    filtered_df = df.copy()
    if selected_username:
        filtered_df = filtered_df[filtered_df["Username"].str.contains(selected_username, case=False, na=False)]
    if selected_net_category != "Semua":
        filtered_df = filtered_df[filtered_df["Net Category"] == selected_net_category]
    if show_vip:
        filtered_df = filtered_df[filtered_df["VIP"]]
    
    for grade in ['AAA', 'A', 'B', 'C', 'D']:
        st.subheader(f"Grade {grade}")
        grade_df = filtered_df[filtered_df['Grade'] == grade][['Username', 'Deposit Amount', 'Withdraw Amount', 'Net Amount', 'Profit', 'Net Category', 'High Withdraw', 'VIP', 'High Risk', 'Grade']]
        st.dataframe(grade_df)
        st.write(f"**Total Members in Grade {grade}: {len(grade_df)}**")
    
elif menu == "Unduh Data":
    st.title("Unduh Data Customer")
    st.download_button(
        label="Download Data CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="customer_segmentation.csv",
        mime="text/csv"
    )
