# app.py

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date

@st.cache_data
def gauti_ir_apdoroti_duomenis(pradzios_data: date, pabaigos_data: date):
    """
    Gauna ir apdoroja CNN Fear and Greed indekso duomenis.
    Grąžina pandas DataFrame arba None, jei įvyko klaida.
    """
    try:
        # <<< --- PAKEITIMAS YRA ČIA --- >>>
        # Užuot nurodę pabaigos datą, kreipiamės į bendrą adresą,
        # tikėdamiesi gauti visus istorinius duomenis.
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        # <<< --- PAKEITIMO PABAIGA --- >>>
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        
        duomenys = r.json()
        
        # Tolimesnis kodas lieka visiškai toks pat
        df = pd.DataFrame(duomenys['fear_and_greed_historical']['data'])
        df.rename(columns={'x': 'timestamp', 'y': 'reiksme', 'rating': 'ivertinimas'}, inplace=True)
        df['data'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True).dt.date
        df.set_index(pd.to_datetime(df['data']), inplace=True)
        
        # Filtruojame visą gautą duomenų rinkinį pagal vartotojo pasirinktas datas
        filtruotas_df = df.loc[pradzios_data.strftime('%Y-%m-%d'):pabaigos_data.strftime('%Y-%m-%d')]
        
        if filtruotas_df.empty:
            return pd.DataFrame()

        galutinis_df = filtruotas_df[['data', 'reiksme', 'ivertinimas']].sort_index(ascending=False).copy()
        return galutinis_df

    except requests.exceptions.HTTPError as e:
        st.error(f"Serveris atmetė užklausą. Klaidos kodas: {e.response.status_code}. Gali būti, kad CNN pakeitė prieigą arba laikinai blokuoja užklausas.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Tinklo klaida: Nepavyko gauti duomenų iš CNN. Pabandykite vėliau. Klaida: {e}")
        return None
    except Exception as e:
        st.error(f"Įvyko nenumatyta klaida apdorojant duomenis. Klaida: {e}")
        return None

# --- Streamlit Vartotojo Sąsaja (lieka nepakitusi) ---

st.set_page_config(page_title="Fear & Greed Index Scraper", layout="centered")

st.title("📊 CNN Fear & Greed Index Scraper")
st.markdown("Pasirinkite norimą datų intervalą ir atsisiųskite istorinius duomenis `.csv` formatu.")

st.header("1. Pasirinkite datas")
col1, col2 = st.columns(2)

with col1:
    pradzios_data = st.date_input("Pradžios data", date(2020, 1, 1)) # Pakeičiau numatytąją datą

with col2:
    pabaigos_data = st.date_input("Pabaigos data", datetime.now())

st.header("2. Generuokite failą")

if st.button("Gauti duomenis ir paruošti atsisiuntimui"):
    if pradzios_data > pabaigos_data:
        st.error("Klaida: Pradžios data negali būti vėlesnė už pabaigos datą.")
    else:
        with st.spinner('Siunčiama užklausa ir apdorojami duomenys...'):
            df = gauti_ir_apdoroti_duomenis(pradzios_data, pabaigos_data)

        if df is not None:
            if not df.empty:
                st.success(f"✅ Duomenys sėkmingai gauti! Iš viso eilučių: {len(df)}")
                st.header("3. Peržiūra ir atsisiuntimas")
                st.dataframe(df.head())
                
                csv_duomenys = df.to_csv(index=False).encode('utf-8')
                failo_pavadinimas = f"fear_greed_index_{pradzios_data}_{pabaigos_data}.csv"
                
                st.download_button(
                   label="Atsisiųsti CSV failą",
                   data=csv_duomenys,
                   file_name=failo_pavadinimas,
                   mime='text/csv',
                )
            else:
                st.warning("Pasirinktame datų intervale duomenų nerasta.")
