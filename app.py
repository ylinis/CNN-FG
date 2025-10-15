# app.py

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

@st.cache_data(ttl=14400) # Talpiname duomenis 4 valandoms
def gauti_alternative_duomenis():
    """
    Gauna visus istorinius Crypto Fear & Greed indekso duomenis iš alternative.me API.
    Grąžina pandas DataFrame.
    """
    try:
        # API adresas, limit=0 reiškia "gauti visus įrašus"
        url = "https://api.alternative.me/fng/?limit=0"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status() # Patikriname, ar užklausa sėkminga
        
        duomenys = r.json()['data']
        df = pd.DataFrame(duomenys)
        
        return df

    except requests.exceptions.RequestException as e:
        st.error(f"Tinklo klaida: Nepavyko pasiekti alternative.me API. Klaida: {e}")
        return None
    except (KeyError, IndexError):
        st.error("Klaida: API atsakymo formatas pasikeitė.")
        return None


def apdoroti_duomenis(df: pd.DataFrame):
    """
    Apdoroja gautą DataFrame: konvertuoja datas, filtruoja ir pervadina stulpelius.
    """
    try:
        # Pervadiname stulpelius
        df.rename(columns={
            'value': 'reiksme',
            'value_classification': 'ivertinimas',
            'timestamp': 'laiko_zymė'
        }, inplace=True)
        
        # Konvertuojame UNIX laiko žymę (string) į datos objektą
        df['data'] = pd.to_datetime(df['laiko_zymė'], unit='s')
        
        # --- Filtravimas pagal datą (paskutiniai metai) ---
        siandien = datetime.now()
        pries_metus = siandien - timedelta(days=365)
        
        # .loc filtras pagal datos intervalą
        filtruotas_df = df.loc[df['data'] >= pries_metus].copy()
        
        # Sutvarkome stulpelių eiliškumą ir formatą
        filtruotas_df['data'] = filtruotas_df['data'].dt.strftime('%Y-%m-%d')
        galutinis_df = filtruotas_df[['data', 'reiksme', 'ivertinimas']].sort_values(by='data', ascending=False)
        
        return galutinis_df
        
    except Exception as e:
        st.error(f"Klaida apdorojant duomenis: {e}")
        return None

# --- Streamlit Vartotojo Sąsaja ---
st.set_page_config(page_title="Crypto F&G Index", layout="centered")

st.title("💰 Crypto Fear & Greed Index Scraper")
st.markdown("Programa parsiunčia **paskutinių metų** istorinių duomenų iš [alternative.me](https://alternative.me/crypto/fear-and-greed-index/) ir paruošia juos `.csv` formatu.")

if st.button("Atsisiųsti paskutinių metų duomenis"):
    with st.spinner('Gaunami duomenys iš alternative.me API...'):
        pradiniai_duomenys = gauti_alternative_duomenis()

    if pradiniai_duomenys is not None:
        with st.spinner('Apdorojami ir filtruojami duomenys...'):
            df = apdoroti_duomenis(pradiniai_duomenys)

        if df is not None and not df.empty:
            st.success(f"✅ Duomenys sėkmingai gauti ir apdoroti! Iš viso eilučių: {len(df)}")
            
            st.header("Duomenų peržiūra (paskutiniai įrašai)")
            st.dataframe(df.head())
            
            csv_duomenys = df.to_csv(index=False).encode('utf-8')
            
            # Formuojame failo pavadinimą pagal datas
            pabaigos_data = datetime.now().strftime('%Y-%m-%d')
            pradzios_data = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            failo_pavadinimas = f"crypto_fg_index_{pradzios_data}_{pabaigos_data}.csv"
            
            st.download_button(
               label="Atsisiųsti CSV failą",
               data=csv_duomenys,
               file_name=failo_pavadinimas,
               mime='text/csv',
            )
        elif df is not None and df.empty:
            st.warning("Duomenys gauti, bet nurodytame laikotarpyje įrašų nerasta.")
