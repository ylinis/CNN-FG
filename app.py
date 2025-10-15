# app.py

import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

@st.cache_data(ttl=14400) # Talpiname duomenis 4 valandoms, kad neapkrautume API
def gauti_alternative_duomenis():
    """
    Gauna VISUS istorinius Crypto Fear & Greed indekso duomenis iš alternative.me API.
    Grąžina pandas DataFrame.
    """
    try:
        # API adresas, limit=0 reiškia "gauti visus įrašus"
        url = "https://api.alternative.me/fng/?limit=0"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        r = requests.get(url, headers=headers, timeout=20)
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


def apdoroti_ir_filtruoti(df: pd.DataFrame, laikotarpis: str):
    """
    Apdoroja gautą DataFrame ir filtruoja pagal pasirinktą laikotarpį.
    laikotarpis: 'metai' arba 'visas'.
    """
    try:
        df_kopija = df.copy()
        # Pervadiname stulpelius
        df_kopija.rename(columns={
            'value': 'reiksme',
            'value_classification': 'ivertinimas',
            'timestamp': 'laiko_zymė'
        }, inplace=True)
        
        # Konvertuojame UNIX laiko žymę (string) į datos objektą
        df_kopija['data'] = pd.to_datetime(df_kopija['laiko_zymė'], unit='s')
        
        filtruotas_df = df_kopija

        # Jei pasirinkti metai, atliekame filtravimą
        if laikotarpis == 'metai':
            siandien = datetime.now()
            pries_metus = siandien - timedelta(days=365)
            filtruotas_df = df_kopija.loc[df_kopija['data'] >= pries_metus].copy()
        
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
st.markdown("Programa parsiunčia istorinių duomenų iš [alternative.me](https://alternative.me/crypto/fear-and-greed-index/) ir paruošia juos `.csv` formatu.")
st.info("Pasirinkite norimą laikotarpį ir spauskite atitinkamą mygtuką.")

# Gauname duomenis iš anksto, kad nereikėtų laukti paspaudus mygtuką
pradiniai_duomenys = gauti_alternative_duomenis()

if pradiniai_duomenys is not None:
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Atsisiųsti paskutinių metų duomenis", use_container_width=True):
            with st.spinner('Apdorojami ir filtruojami duomenys...'):
                df = apdoroti_ir_filtruoti(pradiniai_duomenys, laikotarpis='metai')
    
    with col2:
        if st.button("Atsisiųsti visus istorinius duomenis", use_container_width=True):
             with st.spinner('Apdorojami duomenys...'):
                df = apdoroti_ir_filtruoti(pradiniai_duomenys, laikotarpis='visas')
    
    # Rodyti rezultatus, jei `df` buvo sukurtas po mygtuko paspaudimo
    if 'df' in locals() and df is not None:
        if not df.empty:
            st.success(f"✅ Duomenys sėkmingai paruošti! Iš viso eilučių: {len(df)}")
            
            st.header("Duomenų peržiūra (paskutiniai įrašai)")
            st.dataframe(df.head())
            
            csv_duomenys = df.to_csv(index=False).encode('utf-8')
            
            # Formuojame failo pavadinimą pagal datas
            pradzios_data = df['data'].min()
            pabaigos_data = df['data'].max()
            failo_pavadinimas = f"crypto_fg_index_{pradzios_data}_{pabaigos_data}.csv"
            
            st.download_button(
               label="Atsisiųsti CSV failą",
               data=csv_duomenys,
               file_name=failo_pavadinimas,
               mime='text/csv',
            )
        else:
            st.warning("Nurodytame laikotarpyje įrašų nerasta.")
else:
    st.error("Nepavyko gauti pradinių duomenų iš API. Bandykite perkrauti puslapį.")
