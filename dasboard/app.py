import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import datetime as dt
from matplotlib.patches import Wedge

st.set_page_config(page_title="Dashboard Kualitas Udara", layout="wide")

st.title("Dashboard Analisis Kualitas Udara")

@st.cache_data
def load_data():
    return pd.read_csv("dasboard/kumpulan_data_bersih.csv")

try:
    df = load_data()
except Exception:
    st.error("File 'kumpulan_data_bersih.csv' tidak ditemukan. Pastikan file berada pada folder yang sama.")
    st.stop()


datetime_col = None
for c in ["datetime", "date", "tanggal", "waktu"]:
    if c in df.columns:
        datetime_col = c
        break

if datetime_col:
    df[datetime_col] = pd.to_datetime(df[datetime_col], errors="coerce")
    df = df.dropna(subset=[datetime_col]).sort_values(datetime_col)

if "year" not in df.columns and datetime_col:
    df["year"] = df[datetime_col].dt.year

target_pollutants = []
for col in df.columns:
    if col.upper() in ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]:
        target_pollutants.append(col)

if "RAIN" not in df.columns:
    st.error("Kolom RAIN tidak ditemukan di dataset.")
    st.stop()

if "station" not in df.columns:
    st.error("Kolom station tidak ditemukan di dataset.")
    st.stop()

if not target_pollutants:
    st.error("Kolom polutan utama (PM2.5, PM10, NO2, SO2, CO, O3) tidak ditemukan.")
    st.stop()

df["kategori_hujan"] = df["RAIN"].fillna(0).apply(lambda x: "Hujan" if x > 0 else "Tidak Hujan")


st.sidebar.header("Filter Dashboard")

station_list = sorted(df["station"].dropna().unique().tolist())
selected_stations = st.sidebar.multiselect("Pilih Station", station_list, default=station_list)
if selected_stations:
    df = df[df["station"].isin(selected_stations)]

if "year" in df.columns:
    year_list = sorted(df["year"].dropna().unique().tolist())
    selected_years = st.sidebar.multiselect("Pilih Tahun", year_list, default=year_list)
    if selected_years:
        df = df[df["year"].isin(selected_years)]

if datetime_col and not df.empty:
    min_date = df[datetime_col].min().date()
    max_date = df[datetime_col].max().date()
    selected_date = st.sidebar.date_input(
        "Pilih Rentang Tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(selected_date, tuple) and len(selected_date) == 2:
        start_date, end_date = selected_date
        df = df[(df[datetime_col].dt.date >= start_date) & (df[datetime_col].dt.date <= end_date)]

if df.empty:
    st.warning("Tidak ada data yang sesuai dengan filter.")
    st.stop()
st.caption("Instagram: @psw1244_")


def draw_donut(ax, value, total, title):
    sizes = [value, max(total - value, 0)]
    ax.pie(sizes, wedgeprops=dict(width=0.4), startangle=90, autopct=lambda p: f"{p:.1f}%" if p > 0 else "")
    ax.text(0, 0, f"{int(value)}", ha="center", va="center", fontsize=14, fontweight="bold")
    ax.set_title(title)

def draw_donut_by_year(ax, counts, title):
    labels = [str(int(x)) for x in counts.index]
    sizes = counts.values
    ax.pie(sizes, labels=labels, wedgeprops=dict(width=0.4), startangle=90, autopct=lambda p: f"{p:.1f}%" if p > 0 else "")
    ax.text(0, 0, f"Total\n{int(sizes.sum())}", ha="center", va="center", fontsize=12, fontweight="bold")
    ax.set_title(title)


tab1, tab2 = st.tabs(["Analisis Hujan", "Analisis Station"])

with tab1:
    st.header("Analisis Hujan terhadap Polutan")

    st.subheader("Frekuensi Hujan dan Tidak Hujan")
    freq = df["kategori_hujan"].value_counts().reindex(["Hujan", "Tidak Hujan"]).fillna(0)

    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.dataframe(freq.rename("Frekuensi").reset_index().rename(columns={"index": "Kategori"}), use_container_width=True)
    with col_b:
        fig1, ax1 = plt.subplots(figsize=(7, 4))
        ax1.bar(freq.index, freq.values)
        ax1.set_title("Frekuensi Kejadian Hujan")
        ax1.set_ylabel("Jumlah Observasi")
        st.pyplot(fig1)

    st.subheader("Rata-rata Polutan Saat Hujan dan Tidak Hujan")
    mean_by_rain = df.groupby("kategori_hujan")[target_pollutants].mean().reindex(["Hujan", "Tidak Hujan"])
    diff_df = pd.DataFrame({
        "Polutan": target_pollutants,
        "Rata-rata Saat Hujan": [mean_by_rain.loc["Hujan", p] if "Hujan" in mean_by_rain.index else None for p in target_pollutants],
        "Rata-rata Saat Tidak Hujan": [mean_by_rain.loc["Tidak Hujan", p] if "Tidak Hujan" in mean_by_rain.index else None for p in target_pollutants],
    })
    diff_df["Selisih (Hujan - Tidak Hujan)"] = diff_df["Rata-rata Saat Tidak Hujan"] - diff_df["Rata-rata Saat Hujan"]

    left, right = st.columns(2)
    with left:
        st.dataframe(diff_df, use_container_width=True)
    with right:
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        x = range(len(target_pollutants))
        rain_vals = diff_df["Rata-rata Saat Hujan"].fillna(0).values
        no_rain_vals = diff_df["Rata-rata Saat Tidak Hujan"].fillna(0).values
        width = 0.35
        ax2.bar([i - width/2 for i in x], rain_vals, width=width, label="Hujan")
        ax2.bar([i + width/2 for i in x], no_rain_vals, width=width, label="Tidak Hujan")
        ax2.set_xticks(list(x))
        ax2.set_xticklabels(target_pollutants, rotation=45)
        ax2.set_title("Perbandingan Rata-rata Polutan")
        ax2.legend()
        st.pyplot(fig2)

        fig3, ax3 = plt.subplots(figsize=(8, 4))
        ax3.bar(diff_df["Polutan"], diff_df["Selisih (Hujan - Tidak Hujan)"].fillna(0))
        ax3.set_title("Selisih Rata-rata: Hujan - Tidak Hujan")
        ax3.set_ylabel("Selisih")
        plt.xticks(rotation=45)
        st.pyplot(fig3)

    st.subheader("Korelasi Antar Polutan")
    corr_df = df[target_pollutants].corr()
    fig4, ax4 = plt.subplots(figsize=(7, 5))
    im = ax4.imshow(corr_df, aspect="auto")
    ax4.set_xticks(range(len(target_pollutants)))
    ax4.set_yticks(range(len(target_pollutants)))
    ax4.set_xticklabels(target_pollutants, rotation=45, ha="right")
    ax4.set_yticklabels(target_pollutants)
    ax4.set_title("Heatmap Korelasi Antar Polutan")
    for i in range(len(target_pollutants)):
        for j in range(len(target_pollutants)):
            val = corr_df.iloc[i, j]
            ax4.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=9)
    fig4.colorbar(im, ax=ax4)
    st.pyplot(fig4)

    if "year" in df.columns:
        st.subheader("Distribusi Hujan dan Tidak Hujan per Tahun")
        yearly_counts = df.groupby(["year", "kategori_hujan"]).size().unstack(fill_value=0)

        c1, c2 = st.columns(2)
        with c1:
            if "Hujan" in yearly_counts.columns and not yearly_counts["Hujan"].empty:
                fig5, ax5 = plt.subplots(figsize=(4, 4))
                draw_donut_by_year(ax5, yearly_counts["Hujan"], "Distribusi Hujan per Tahun")
                st.pyplot(fig5)
            else:
                st.write("Data hujan tidak tersedia untuk grafik donut.")
        with c2:
            if "Tidak Hujan" in yearly_counts.columns and not yearly_counts["Tidak Hujan"].empty:
                fig6, ax6 = plt.subplots(figsize=(4, 4))
                draw_donut_by_year(ax6, yearly_counts["Tidak Hujan"], "Distribusi Tidak Hujan per Tahun")
                st.pyplot(fig6)
            else:
                st.write("Data tidak hujan tidak tersedia untuk grafik donut.")

with tab2:
    st.header("Analisis per Station")

    st.subheader("Nilai Tertinggi dan Terendah Setiap Polutan per Station")
    station_mean = df.groupby("station")[target_pollutants].mean()

    summary_rows = []
    for pol in target_pollutants:
        summary_rows.append({
            "Polutan": pol,
            "Station Tertinggi": station_mean[pol].idxmax(),
            "Nilai Tertinggi": station_mean[pol].max(),
            "Station Terendah": station_mean[pol].idxmin(),
            "Nilai Terendah": station_mean[pol].min(),
        })
    summary_df = pd.DataFrame(summary_rows)

    def highlight_extremes(row):
        styles = [""] * len(row)
        if row.name is not None:
            pass
        return styles

    st.dataframe(summary_df, use_container_width=True)

    st.subheader("Korelasi antara Variabel X dengan Polutan")
    col1, col2, col3 = st.columns(3)

    candidate_x = [c for c in df.columns if c not in ["kategori_hujan", datetime_col] and pd.api.types.is_numeric_dtype(df[c])]
    if not candidate_x:
        st.info("Tidak ada variabel numerik yang bisa dipilih sebagai X.")
    else:
        with col1:
            default_x = candidate_x.index("O3") if "O3" in candidate_x else 0
            selected_x = st.selectbox("Pilih variabel X", candidate_x, index=default_x)
        with col2:
            selected_pols = st.multiselect("Pilih polutan", target_pollutants, default=target_pollutants[:6] if len(target_pollutants) >= 3 else target_pollutants)


        filtered_all = df.copy()

        if not selected_pols:
            st.info("Pilih minimal satu polutan.")
        elif filtered_all.empty:
            st.warning("Tidak ada data yang tersedia untuk analisis.")
        else:
            n = len(selected_pols)
            ncols = min(n, 3)
            nrows = (n + ncols - 1) // ncols
            fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(4*ncols, 4*nrows), squeeze=False)

            corr_rows = []
            axes_flat = axes.flatten()
            for idx, pol in enumerate(selected_pols):
                ax = axes_flat[idx]
                temp = filtered_all[[selected_x, pol]].dropna()

                x_vals = temp.loc[:, selected_x]
                y_vals = temp.loc[:, pol]
                if isinstance(x_vals, pd.DataFrame):
                    x_vals = x_vals.iloc[:, 0]
                if isinstance(y_vals, pd.DataFrame):
                    y_vals = y_vals.iloc[:, 0]

                corr_val = x_vals.corr(y_vals) if len(temp) > 1 else None
                corr_rows.append({"Polutan": pol, "Korelasi": corr_val})

                ax.scatter(x_vals, y_vals, alpha=0.5)
                if len(x_vals) > 1:
                    slope, intercept = np.polyfit(x_vals, y_vals, 1)
                    ax.plot(x_vals, slope * x_vals + intercept, color='red', linewidth=2)
                ax.set_title(f"{selected_x} vs {pol}")
                ax.set_xlabel(selected_x)
                ax.set_ylabel(pol)

            for ax in axes_flat[n:]:
                ax.axis("off")

            plt.tight_layout()
            st.pyplot(fig)

            st.dataframe(pd.DataFrame(corr_rows), use_container_width=True)

