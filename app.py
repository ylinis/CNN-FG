# app.py

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date

@st.cache_data
def gauti_finhacker_duomenis(pradzios_data: date, pabaigos_data: date):
    """
    Nuskaito Fear & Greed indekso duomenis iš finhacker.cz HTML lentelės.
    Grąžina pandas DataFrame arba None, jei įvyko klaida.
    """
    try:
        url = "https://finhacker.cz/fear-and-greed-index-historical-data/"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()

        # Pandas automatiškai nuskaito visas lenteles puslapyje.
        # Svetainėje yra kelios lentelės, mums reikia antrosios (indeksas 1).
        lenteles = pd.read_html(r.content, header=0)
        df = lenteles[1]
        
        # --- Duomenų valymas ---
        # 1. Pervadiname stulpelius į logiškesnius
        df.rename(columns={
            'Date': 'data',
            'F&G Value': 'reiksme',
            'F&G Rating': 'ivertinimas'
        }, inplace=True)
        
        # 2. Konvertuojame 'data' stulpelį į datos objektą
        df['data'] = pd.to_datetime(df['data'], format='%B %d, %Y')
        
        # 3. Nustatome datą kaip indeksą, kad galėtume filtruoti
        df.set_index('data', inplace=True)
        
        # 4. Išfiltruojame pagal vartotojo pasirinktas datas
        filtruotas_df = df.loc[pradzios_data.strftime('%Y-%m-%d'):pabaigos_data.strftime('%Y-%m-%d')]
        
        if filtruotas_df.empty:
            return pd.DataFrame()

        # Grąžiname datą iš indekso atgal į stulpelį patogumui
        galutinis_df = filtruotas_df.reset_index().sort_values(by='data', ascending=False)
        
        # Sutvarkome stulpelių eiliškumą
        return galutinis_df[['data', 'reiksme', 'ivertinimas']]

    except requests.exceptions.RequestException as e:
        st.error(f"Tinklo klaida: Nepavyko pasiekti finhacker.cz. Klaida: {e}")
        return None
    except (IndexError, KeyError):
        st.error("Klaida: Nepavyko rasti arba apdoroti duomenų lentelės. Gali būti, kad svetainės struktūra pasikeitė.")
        return None
    except Exception as e:
        st.error(f"Įvyko nenumatyta klaida: {e}")
        return None


# --- Streamlit Vartotojo Sąsaja (lieka beveik nepakitusi) ---

st.set_page_config(page_title="F&G Index Scraper", layout="centered")

st.title("📊 Fear & Greed Index Scraper (finhacker.cz)")
st.markdown("Pasirinkite norimą datų intervalą ir atsisiųskite istorinius duomenis `.csv` formatu.")

st.header("1. Pasirinkite datas")
col1, col2 = st.columns(2)

with col1:
    pradzios_data = st.date_input("Pradžios data", date(2020, 1, 1))

with col2:
    pabaigos_data = st.date_input("Pabaigos data", datetime.now())

st.header("2. Generuokite failą")

if st.button("Gauti duomenis ir paruošti atsisiuntimui"):
    if pradzios_data > pabaigos_data:
        st.error("Klaida: Pradžios data negali būti vėlesnė už pabaigos datą.")
    else:
        with st.spinner('Nuskaitoma finhacker.cz svetainė ir apdorojami duomenys...'):
            df = gauti_finhacker_duomenis(pradzios_data, pabaigos_data)

        if df is not None:
            if not df.empty:
                st.success(f"✅ Duomenys sėkmingai gauti! Iš viso eilučių: {len(df)}")
                st.header("3. Peržiūra ir atsisiuntimas")
                st.dataframe(df.head())
                
                # Konvertuojame datas atgal į YYYY-MM-DD formatą CSV faile
                df['data'] = df['data'].dt.strftime('%Y-%m-%d')
                
                csv_duomenys = df.to_csv(index=False).encode('utf-8')
                failo_pavadinimas = f"finhacker_fg_index_{pradzios_data}_{pabaigos_data}.csv"
                
                st.download_button(
                   label="Atsisiųsti CSV failą",
                   data=csv_duomenys,
                   file_name=failo_pavadinimas,
                   mime='text/csv',
                )
            else:
                st.warning("Pasirinktame datų intervale duomenų nerasta.")
