# app.py

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date

# --- Pagrindinė duomenų gavimo funkcija (beveik nepakitusi) ---
# Padarome ją labiau universalią - ji grąžins DataFrame, o ne saugos failą.
@st.cache_data # Streamlit talpins (cache) funkcijos rezultatus
def gauti_ir_apdoroti_duomenis(pradzios_data: date, pabaigos_data: date):
    """
    Gauna ir apdoroja CNN Fear and Greed indekso duomenis.
    Grąžina pandas DataFrame arba None, jei įvyko klaida.
    """
    try:
        url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{pabaigos_data.strftime('%Y-%m-%d')}"
        
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        
        duomenys = r.json()
        
        df = pd.DataFrame(duomenys['fear_and_greed_historical']['data'])
        df.rename(columns={'x': 'timestamp', 'y': 'reiksme', 'rating': 'ivertinimas'}, inplace=True)
        df['data'] = pd.to_datetime(df['timestamp'], unit='ms', utc=True).dt.date
        df.set_index(pd.to_datetime(df['data']), inplace=True)
        
        # Filtruojame pagal nurodytą datų intervalą
        filtruotas_df = df.loc[pradzios_data.strftime('%Y-%m-%d'):pabaigos_data.strftime('%Y-%m-%d')]
        
        if filtruotas_df.empty:
            return pd.DataFrame() # Grąžiname tuščią DataFrame

        galutinis_df = filtruotas_df[['data', 'reiksme', 'ivertinimas']].sort_index(ascending=False).copy()
        return galutinis_df

    except requests.exceptions.RequestException as e:
        st.error(f"Tinklo klaida: Nepavyko gauti duomenų iš CNN. Pabandykite vėliau. Klaida: {e}")
        return None
    except Exception as e:
        st.error(f"Įvyko nenumatyta klaida apdorojant duomenis. Klaida: {e}")
        return None

# --- Streamlit Vartotojo Sąsaja ---

# 1. Puslapio konfigūracija (antraštė naršyklės skirtuke)
st.set_page_config(page_title="Fear & Greed Index Scraper", layout="centered")

# 2. Antraštė ir aprašymas
st.title("📊 CNN Fear & Greed Index Scraper")
st.markdown("Pasirinkite norimą datų intervalą ir atsisiųskite istorinius duomenis `.csv` formatu.")

# 3. Datos pasirinkimo valdikliai
st.header("1. Pasirinkite datas")
col1, col2 = st.columns(2) # Sukuriame du stulpelius geresniam išdėstymui

with col1:
    pradzios_data = st.date_input("Pradžios data", date(2022, 1, 1))

with col2:
    pabaigos_data = st.date_input("Pabaigos data", datetime.now())

# 4. Mygtukas ir duomenų generavimas
st.header("2. Generuokite failą")

if st.button("Gauti duomenis ir paruošti atsisiuntimui"):
    if pradzios_data > pabaigos_data:
        st.error("Klaida: Pradžios data negali būti vėlesnė už pabaigos datą.")
    else:
        # Rodyti pranešimą, kol duomenys gaunami
        with st.spinner('Gaunami ir apdorojami duomenys... Tai gali užtrukti kelias sekundes.'):
            df = gauti_ir_apdoroti_duomenis(pradzios_data, pabaigos_data)

        # Patikriname, ar funkcija grąžino duomenis
        if df is not None:
            if not df.empty:
                st.success("✅ Duomenys sėkmingai gauti!")
                
                # 5. Duomenų peržiūra ir atsisiuntimo mygtukas
                st.header("3. Peržiūra ir atsisiuntimas")
                st.markdown("Žemiau matote kelias pirmas sugeneruotų duomenų eilutes:")
                st.dataframe(df.head()) # Rodo lentelę su duomenimis
                
                # Konvertuojame DataFrame į CSV formatą (byte string)
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
