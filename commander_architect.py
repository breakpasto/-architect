import streamlit as st
import requests
import re
import urllib.parse

st.set_page_config(page_title="Commander Architect v4.2", page_icon="🧙‍♂️", layout="wide")

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

# --- INTERFACCIA ---
st.title("🧙‍♂️ Commander Architect v4.2")

with st.sidebar:
    st.header("⚙️ Configurazione")
    cmd_name = st.text_input("Inserisci Comandante:", placeholder="Es: Ghave, Guru of Spores")

if cmd_name:
    cmd_data = get_card(cmd_name)
    if cmd_data:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(cmd_data['image_uris']['normal'], use_container_width=True)
            st.metric("Costo Comandante", f"{cmd_data.get('prices', {}).get('eur', '0.00')} €")
        
        with col2:
            st.subheader("🔗 Database Combo & Sinergie")
            
            # --- GENERATORE DI LINK CORRETTO ---
            # 1. Usiamo 'commanderspellbook.com' (con la S)
            # 2. Formattiamo esattamente come il loro motore di ricerca interno
            # Sostituiamo gli spazi con %20 e le virgole con %2C
            formatted_name = cmd_name.replace(" ", "%20").replace(",", "%2C")
            spellbook_url = f"https://commanderspellbook.com/search/?q={formatted_name}"
            
            st.info(f"Clicca il tasto sotto per aprire le combo di **{cmd_name}** direttamente su Commander Spellbook.")
            
            st.link_button(f"🔥 Vedi Combo di {cmd_name}", spellbook_url, type="primary")
            
            st.divider()
            
            # Link EDHREC (sempre utile)
            edh_slug = cmd_name.lower().replace(",", "").replace("'", "").replace(" ", "-")
            edhrec_url = f"https://edhrec.com/commanders/{edh_slug}"
            st.link_button(f"📊 Strategie su EDHREC", edhrec_url)

    # --- SEZIONE BUDGET ---
    st.divider()
    st.subheader("📝 Calcolo Budget 100€")
    lista = st.text_area("Incolla la lista (99 carte):", height=150)
    
    if st.button("Verifica Prezzi", type="primary"):
        if lista:
            linee = [l.strip() for l in lista.split("\n") if l.strip()]
            totale = 0.0
            with st.expander("Dettaglio Analisi Prezzi"):
                for l in linee:
                    nome = re.sub(r'^(\d+x?|x)\s+', '', l).split(' (')[0].strip()
                    if nome.lower() == cmd_name.lower(): continue
                    p = get_market_price(nome)
                    totale += p
                    st.write(f"{nome}: {p:.2f} €")
            
            st.divider()
            is_ok = totale <= 100
            st.metric("TOTALE MAZZO", f"{totale:.2f} €", delta=f"{100-totale:.2f} €")
            if is_ok: st.balloons()
            else: st.error("Mazzo fuori budget!")
