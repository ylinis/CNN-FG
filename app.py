# app.py

import streamlit as st
import pandas as pd
from datetime import datetime, date

# Selenium importai
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException # Importuojame specifinę klaidą

@st.cache_data(ttl=3600)
def gauti_duomenis_su_selenium(pradzios_data: date, pabaigos_data: date):
    """
    Nuskaito Fear & Greed indekso duomenis iš finhacker.cz,
    naudojant Selenium naršyklės automatizavimui.
    """
    # <<< --- PAKEITIMAI YRA ŠIAME BLOKE --- >>>
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(options=options)
        url = "https://finhacker.cz/fear-and-greed-index-historical-data/"
        driver.get(url)

        # Naudojame patikimesnį selektorių (ieškome lentelės su klase 'tablepress')
        # ir laukiame, kol ji taps MATOMA, o ne tik esanti DOM.
        wait = WebDriverWait(driver, 30) # Padidiname laukimo laiką iki 30s
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "table.tablepress")))

        page_source = driver.page_source
        lenteles = pd.read_html(page_source)
        # Saugumo sumetimais, ieškome lentelės, kurioje yra tikėtinas stulpelis 'F&G Value'
        df = next((tbl for tbl in lenteles if 'F&G Value' in tbl.columns), None)

        if df is None:
            st.error("Klaida: Duomenų lentelė buvo rasta, bet jos formatas netinkamas.")
            return None

    except TimeoutException:
        st.error("Laukimo laikas baigėsi: Nepavyko rasti duomenų lentelės per 30 sekundžių. Gali būti, kad svetainės struktūra vėl pasikeitė.")
        return None
    except Exception as e:
        st.error(f"Selenium klaida: Nepavyko gauti duomenų. Klaida: {e}")
        return None
    finally:
        if 'driver' in locals():
            driver.quit()
    # <<< --- PAKEITIMŲ PABAIGA --- >>>

    # --- Duomenų valymas (lieka nepakitęs) ---
    try:
        df.rename(columns={
            'Date': 'data',
            'F&G Value': 'reiksme',
            'F&G Rating': 'ivertinimas'
        }, inplace=True)
        
        df['data'] = pd.to_datetime(df['data'], format='%B %d, %Y')
        df.set_index('data', inplace=True)
        
        filtruotas_df = df.loc[pradzios_data.strftime('%Y-%m-%d'):pabaigos_data.strftime('%Y-%m-%d')]
        
        if filtruotas_df.empty:
            return pd.DataFrame()

        galutinis_df = filtruotas_df.reset_index().sort_values(by='data', ascending=False)
        return galutinis_df[['data', 'reiksme', 'ivertinimas']]

    except (IndexError, KeyError) as e:
        st.error(f"Pandas klaida: Nepavyko apdoroti duomenų lentelės. Gali būti, kad jos stulpelių pavadinimai pasikeitė. Klaida: {e}")
        return None


# --- Streamlit Vartotojo Sąsaja (lieka nepakitusi) ---
st.set_page_config(page_title="F&G Index Scraper", layout="centered")
st.title("📊 Fear & Greed Index Scraper (finhacker.cz)")
st.markdown("Pasirinkite norimą datų intervalą ir atsisiųskite istorinius duomenis `.csv` formatu.")
st.header("1. Pasirinkite datas")
col1, col2 = st.columns(2)
with col1:
    pradzios_data = st.date_input("Pradžios data", date(2023, 1, 1))
with col2:
    pabaigos_data = st.date_input("Pabaigos data", datetime.now())

st.header("2. Generuokite failą")
if st.button("Gauti duomenis ir paruošti atsisiuntimui"):
    if pradzios_data > pabaigos_data:
        st.error("Klaida: Pradžios data negali būti vėlesnė už pabaigos datą.")
    else:
        with st.spinner('Paleidžiama naršyklė serveryje ir laukiama duomenų... Tai gali užtrukti iki 30 sekundžių.'):
            df = gauti_duomenis_su_selenium(pradzios_data, pabaigos_data)

        if df is not None:
            if not df.empty:
                st.success(f"✅ Duomenys sėkmingai gauti! Iš viso eilučių: {len(df)}")
                st.header("3. Peržiūra ir atsisiuntimas")
                st.dataframe(df.head())
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
