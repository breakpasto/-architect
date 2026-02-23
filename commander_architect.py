import streamlit as st
import requests
import re
import time
import urllib.parse

st.set_page_config(page_title="Commander Architect v3.0", page_icon="🧙‍♂️", layout="wide")

# --- FUNZIONI API (SOLO SCRYFALL - SUPER STABILI) ---

def get_card(name):
    try:
        url = f"https://api.scryfall.com/cards/named?exact={urllib.parse.quote(name)}"
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

def get_market_price(card_name):
    try:
        url = f"https://api.scryfall.com/cards/search?q=!\"{urllib.parse.quote(card_name)}\"&unique=prints"
        r = requests.get(url, timeout=10).json()
        prices = [float(p['prices']['eur']) for p in r['data'] if p.get('prices', {}).get('eur')]
        return min(prices) if prices else 0.0
    except: return 0.0

def get_synergies(colors, q_type="staples"):
    """Recupera carte sinergiche divise per categoria tramite Scryfall"""
    c_query = "".join(colors) if colors else "c"
    # staples = carte popolari, finishers = carte per chiudere la partita
    if q_type == "finishers":
        query = f"f:commander id<={c_query} (otag:win-con OR o:win) eur<5"
    else:
        query = f"f:commander id<={c_query} eur<2 status:legal"
    
    url = f"https://api.scryfall.com/cards/search?q={urllib.parse.quote(query)}&order=edhrec"
    try:
        r = requests.get(url, timeout=10).json()
        return r.get('data', [])[:10]
    except: return []

# --- INTERFACCIA ---

st.title("🧙‍♂️ Commander Architect v3.0")
st.caption("Versione Ultra-Stabile (Senza errori di connessione)")

with st.sidebar:
    st.header("⚙️ Settings")
    cmd_input = st.text_input("Nome Comandante:", placeholder="Es: Muldrotha, the Gravetide")

if cmd_input:
    cmd_data = get_card(cmd_input)
    if cmd_data:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(cmd_data['image_uris']['normal'], use_container_width=True)
            st.metric("Costo Comandante", f"{cmd_data.get('prices', {}).get('eur', '0.00')} €")
        
        with col2:
            t1, t2 = st.tabs(["🏆 Win Conditions", "💡 Suggerimenti Budget"])
            with t1:
                st.subheader("Carte per chiudere la partita")
                wins = get_synergies(cmd_data['color_identity'], "finishers")
                if wins:
                    for w in wins:
                        st.write(f"✅ **{w['name']}** - {w.get('prices', {}).get('eur', 'N/A')}€")
                        st.caption(f"Tipo: {w['type_line']}")
                else: st.info("Nessuna win-con specifica trovata nei tuoi colori.")
            
            with t2:
                st.subheader("Migliori carte sotto i 2€")
                staples = get_synergies(cmd_data['color_identity'], "staples")
                sc1, sc2 = st.columns(2)
                for idx, s in enumerate(staples):
                    target = sc1 if idx % 2 == 0 else sc2
                    target.write(f"🔹 **{s['name']}** ({s.get('prices', {}).get('eur', 'N/A')}€)")

    # --- CALCOLO BUDGET ---
    st.divider()
    deck_list = st.text_area("Incolla qui la lista per il calcolo dei 100€:", height=150)
    if st.button("Calcola Prezzo Totale", type="primary"):
        if deck_list:
            linee = [l.strip() for l in deck_list.split("\n") if l.strip()]
            tot = 0.0
            with st.expander("Vedi analisi prezzi singoli"):
                for riga in linee:
                    n = re.sub(r'^(\d+x?|x)\s+', '', riga).split(' (')[0].strip()
                    if n.lower() == cmd_input.lower(): continue
                    p = get_market_price(n)
                    tot += p
                    st.write(f"{n}: {p:.2f} €")
            st.metric("TOTALE MAZZO", f"{tot:.2f} €", delta=f"{100-tot:.2f} €")
            if tot <= 100: st.balloons()
            else: st.error("Sei sopra il limite di 100€!")

else: st.info("Inserisci il nome di un comandante per iniziare.")
