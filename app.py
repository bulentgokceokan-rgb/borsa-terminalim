import ccxt
import pandas as pd
import streamlit as st
from streamlit_lightweight_charts import renderLightweightCharts
import yfinance as yf

st.set_page_config(layout="wide", page_title="Kişisel Borsa & Veri Terminali")

VARLIKLAR = {
    "Akbank": "AKBNK.IS",
    "Aselsan": "ASELS.IS",
    "Ons Altın": "GC=F",
    "Gümüş": "SI=F",
    "Bitcoin": "BTC/USDT",
}


@st.cache_data(ttl=60)
def veri_cek(sembol, periyot):
    if "/USDT" in sembol:
        binance = ccxt.binance()
        mumlar = binance.fetch_ohlcv(sembol, timeframe=periyot, limit=500)
        df = pd.DataFrame(
            mumlar, columns=["Tarih", "Open", "High", "Low", "Close", "Volume"]
        )
        df["Tarih"] = pd.to_datetime(df["Tarih"], unit="ms")
        return df
    else:
        sure = "60d" if periyot in ["5m", "15m"] else "1y"
        df = yf.download(
            tickers=sembol, period=sure, interval=periyot, progress=False
        )
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        zaman_kolonu = "Datetime" if "Datetime" in df.columns else "Date"
        df.rename(columns={zaman_kolonu: "Tarih"}, inplace=True)
        return df[["Tarih", "Open", "High", "Low", "Close", "Volume"]].dropna()


sol_kolon, sag_kolon = st.columns([0.78, 0.22])

with sag_kolon:
    st.subheader("İzleme Listesi")
    secilen_isim = st.radio(
        "Grafikte Göster:",
        list(VARLIKLAR.keys()),
        label_visibility="collapsed",
    )
    st.divider()

    for isim, kod in VARLIKLAR.items():
        try:
            ozet_df = veri_cek(kod, "1d")
            if len(ozet_df) >= 2:
                son = float(ozet_df["Close"].iloc[-1])
                onceki = float(ozet_df["Close"].iloc[-2])
                degisim = ((son - onceki) / onceki) * 100
                renk = "🟢" if degisim >= 0 else "🔴"
                st.markdown(f"**{isim}** `{son:.2f}` {renk} `%{degisim:.2f}`")
        except Exception:
            st.markdown(f"**{isim}** (Veri bekleniyor...)")

with sol_kolon:
    ust_1, ust_2, ust_3 = st.columns([0.4, 0.3, 0.3])
    with ust_1:
        st.subheader(f"{secilen_isim} ({VARLIKLAR[secilen_isim]})")
    with ust_2:
        periyot = st.selectbox(
            "Zaman Dilimi",
            ["5m", "15m", "1h", "1d"],
            index=1,
            label_visibility="collapsed",
        )

    aktif_sembol = VARLIKLAR[secilen_isim]
    df = veri_cek(aktif_sembol, periyot)

    with ust_3:
        csv_veri = df.to_csv(index=False).encode("utf-8")
        dosya_adi = f"{secilen_isim}_{periyot}_verisi.csv"
        st.download_button(
            label=f"📥 {periyot} Verisini İndir (CSV)",
            data=csv_veri,
            file_name=dosya_adi,
            mime="text/csv",
            use_container_width=True,
        )

    mum_listesi = []
    for _, satir in df.iterrows():
        mum_listesi.append({
            "time": int(pd.to_datetime(satir["Tarih"]).timestamp()),
            "open": float(satir["Open"]),
            "high": float(satir["High"]),
            "low": float(satir["Low"]),
            "close": float(satir["Close"]),
        })

    grafik_ayarlari = {
        "height": 580,
        "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {
            "vertLines": {"color": "#1e222d"},
            "horzLines": {"color": "#1e222d"},
        },
        "timeScale": {"timeVisible": True, "secondsVisible": False},
    }

    renderLightweightCharts(
        [
            {
                "chart": grafik_ayarlari,
                "series": [{"type": "Candlestick", "data": mum_listesi}],
            }
        ],
        key=f"chart_{aktif_sembol}_{periyot}",
    )
