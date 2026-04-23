import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📊 Dashboard Analisis E-Commerce")

# =====================
# LOAD DATA
# =====================
@st.cache_data
def load_data():
    df = pd.read_csv("akhir_df.csv")
    df["order_purchase_timestamp"] = pd.to_datetime(df["order_purchase_timestamp"])
    return df

df = load_data()
df = df[df["order_status"] == "delivered"]

# =====================
# SIDEBAR FILTER
# =====================
menu = st.sidebar.selectbox(
    "Pilih Analisis",
    ["EDA Kategori", "EDA State", "RFM Analysis"]
)

# =====================
# KPI GLOBAL
# =====================
st.subheader("📌 Ringkasan Data")

col1, col2, col3 = st.columns(3)

col1.metric("Total Transaksi", df["order_id"].nunique())
col2.metric("Total Customer", df["customer_unique_id"].nunique())
col3.metric("Total Revenue", f"{int((df['price']+df['freight_value']).sum()):,}")

st.markdown("---")

# =====================
# EDA KATEGORI
# =====================
if menu == "EDA Kategori":
    st.header("📦 Analisis Kategori Produk")

    kategori_df = df.groupby("product_category_name_english")["order_item_id"] \
        .count().sort_values(ascending=False)

    total = kategori_df.sum()
    kategori_df = kategori_df.reset_index()
    kategori_df.columns = ["kategori", "total_terjual"]
    kategori_df["persentase"] = (kategori_df["total_terjual"] / total) * 100

    top10 = kategori_df.head(10)

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(top10["kategori"], top10["total_terjual"])
        plt.xticks(rotation=45)
        plt.title("Top 10 Kategori")
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots(figsize=(5,5))
        ax.pie(
            top10["persentase"],
            labels=top10["kategori"],
            autopct='%1.1f%%',
            startangle=140
        )
        ax.set_title("Kontribusi (%)")
        st.pyplot(fig)

    top_kat = top10.iloc[0]

    st.success(f"""
    🏆 Kategori Teratas: {top_kat['kategori']}  
    📦 Total: {int(top_kat['total_terjual'])} unit  
    📊 Kontribusi: {top_kat['persentase']:.2f}%
    """)

    st.info("""
    💡 Insight:
    Kategori produk didominasi oleh kebutuhan rumah tangga seperti bed_bath_table.
    Hal ini menunjukkan bahwa produk kebutuhan sehari-hari memiliki permintaan tinggi.
    """)

# =====================
# EDA STATE
# =====================
elif menu == "EDA State":
    st.header("🌍 Analisis State")

    state_df = df.groupby("customer_state")["order_id"] \
        .nunique().sort_values(ascending=False)

    total = state_df.sum()
    state_df = state_df.reset_index()
    state_df.columns = ["state", "total_transaksi"]
    state_df["persentase"] = (state_df["total_transaksi"] / total) * 100

    top10 = state_df.head(10)

    col1, col2 = st.columns(2)

    with col1:
        fig, ax = plt.subplots(figsize=(6,4))
        ax.bar(top10["state"], top10["total_transaksi"])
        plt.title("Top 10 State")
        st.pyplot(fig)

    with col2:
        fig, ax = plt.subplots(figsize=(5,5))
        ax.pie(
            top10.head(5)["persentase"],
            labels=top10.head(5)["state"],
            autopct="%1.1f%%"
        )
        plt.title("Top 5 Kontribusi")
        st.pyplot(fig)

    top_state = top10.iloc[0]

    st.success(f"""
    🏆 State Teratas: {top_state['state']}  
    📊 Total: {int(top_state['total_transaksi'])} transaksi  
    📈 Kontribusi: {top_state['persentase']:.2f}%
    """)

    st.info("""
    💡 Insight:
    Aktivitas transaksi sangat terpusat di São Paulo (SP),
    kemungkinan karena populasi besar dan tingkat urbanisasi tinggi.
    """)

# =====================
# RFM ANALYSIS
# =====================
elif menu == "RFM Analysis":
    st.header("👤 RFM Analysis")

    df["total_price"] = df["price"] + df["freight_value"]

    snapshot_date = df["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

    rfm = df.groupby("customer_unique_id").agg({
        "order_purchase_timestamp": lambda x: (snapshot_date - x.max()).days,
        "order_id": "nunique",
        "total_price": "sum"
    })

    rfm.columns = ["recency", "frequency", "monetary"]

    # SCORING
    rfm["R_score"] = pd.qcut(rfm["recency"], 4, labels=[4,3,2,1])
    rfm["F_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1,2,3,4])
    rfm["M_score"] = pd.qcut(rfm["monetary"], 4, labels=[1,2,3,4])

    rfm["RFM_score"] = (
        rfm["R_score"].astype(str) +
        rfm["F_score"].astype(str) +
        rfm["M_score"].astype(str)
    )

    # SEGMENT
    def segment(row):
        if row["RFM_score"] == "444":
            return "Best Customers"
        elif row["R_score"] == 4:
            return "Recent Customers"
        elif row["F_score"] == 4:
            return "Loyal Customers"
        elif row["M_score"] == 4:
            return "Big Spenders"
        else:
            return "Others"

    rfm["segment"] = rfm.apply(segment, axis=1)

    # VISUAL
    fig, ax = plt.subplots(figsize=(6,4))
    rfm["segment"].value_counts().plot(kind="bar", ax=ax)

    ax.set_title("Distribusi Segmentasi Customer")
    ax.set_xlabel("Segment")
    ax.set_ylabel("Jumlah Customer")
    plt.xticks(rotation=45)

    st.pyplot(fig)

    st.info("""
    💡 Insight:
    Mayoritas pelanggan berada pada kategori "Others",
    menunjukkan banyak pelanggan dengan aktivitas rendah.
    Strategi yang dapat dilakukan adalah meningkatkan retensi dan engagement pelanggan.
    """)

    st.dataframe(rfm.head())

# =====================
# DEFAULT
# =====================
else:
    st.info("Pilih menu di sidebar untuk memulai analisis 🚀")