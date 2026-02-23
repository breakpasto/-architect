import streamlit as st
import requests
import re
import time
import urllib.parse

# 1. Configurazione Iniziale
st.set_page_config(page_title="Commander Architect v2.8", page_icon="🧙‍♂️", layout="wide")

# 2. Funzioni API
def get_card(name):
    try:
        url = f"https://api.scryfall.com/cards/named?exact={urllib.parse.quote(name)}"
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_market_price(card_name):
    try:
        url = f"https://api.scryfall.com/cards/search?q=!\"{urllib.parse.quote(card_name)}\"&unique=prints"
        r = requests.get(url, timeout=10).json()
        prices = [float(p['prices']['eur']) for p in r['data'] if p.get('prices', {}).get('eur')]
        return min(prices) if prices else 0.0
    except:
        return 0.0

def get_suggestions(colors):
    try:
        c_query = "".join(colors) if colors else "c"
        query = f"f:commander id<={c_query} eur<2.5 status:legal"
        url = f"https://api.scryfall.com/cards/search?q={urllib.parse.quote(query)}&order=edhrec"
        r = requests.get(url, timeout=10).json()
        return r.get('data', [])[:12]
    except:
        return []

def get_combos_hybrid(commander_name, color_identity):
    """Tenta prima la ricerca per nome, poi per identità di colore se la prima fallisce."""
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    
    # Test 1: Ricerca specifica per Comandante
    try:
        url_name = f"https://backend.commandspellbook.com/variants?q={urllib.parse.quote(commander_name)}"
        r = requests.get(url_name, headers=headers, timeout=12)
        if r.status_code == 200:
            res = r.json().get('results', []) if isinstance(r.json(), dict) else r.json()
            if res: return res, "specifica"
    except:
        pass # Fallback al colore

    # Test 2: Ricerca per Identità di Colore (Fallback)
    try:
        ci = "".join(color_identity).lower() if color_identity else "c"
        url_color = f"https://backend.commandspellbook.com/variants?q=ci%3A{ci}"
        r = requests.get(url_color, headers=headers, timeout=12)
        if r.status_code == 200:
            res = r.json().get('results', []) if isinstance(r.json(), dict) else r.json()
            return res, "colore"
    except:
        return None, "errore"
    
    return [], "nessuna"

# 3. Interfaccia Utente
st.title("🧙‍♂️ Commander Deck Architect")
st.markdown("##### Budget 100€ (Comandante Escluso)")

with st.sidebar:
    st.header("⚙️ Settings")
    cmd_input = st.text_input("Nome Comandante:", placeholder="Es: Ghave, Guru of Spores")

if cmd_input:
    cmd_data = get_card(cmd_input)
    if cmd_data:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(cmd_data['image_uris']['normal'], use_container_width=True)
            st.metric("Prezzo Comandante", f"{cmd_data.get('prices', {}).get('eur', '0.00')} €")
        
        with col2:
            t1, t2 = st.tabs(["🔥 Top 10 Combo", "💡 Suggerimenti"])
            with t1:
                with st.spinner("Analisi sinergie e combo..."):
                    combos, tipo_ricerca = get_combos_hybrid(cmd_input, cmd_data['color_identity'])
                
                if tipo_ricerca == "errore":
                    st.warning("⚠️ Database Combo offline. Riprova più tardi.")
                elif combos:
                    msg = "Combo specifiche trovate!" if tipo_ricerca == "specifica" else f"Migliori combo nei colori {tipo_ricerca}:"
                    st.info(msg)
                    for i, c in enumerate(combos[:10]):
                        uses = c.get('uses', [])
                        c_names = [u['card']['name'] for u in uses]
                        with st.expander(f"Combo #{i+1}: {', '.join(c_names[:2])}"):
                            for u in uses: st.write(f"- {u['card']['name']}")
                            res_list = [r['name'] for r in c.get('results', [])]
                            st.success(f"🎯 {', '.join(res_list)}")
                            st.caption(c.get('description', ''))
                else:
                    st.info("Nessuna combo trovata per questa configurazione.")
            
            with t2:
                suggerimenti = get_suggestions(cmd_data['color_identity'])
                sc1, sc2, sc3 = st.columns(3)
                for idx, s in enumerate(suggerimenti):
                    target = [sc1, sc2, sc3][idx % 3]
                    target.write(f"**{s['name']}**")
                    target.caption(f"{s.get('prices', {}).get('eur', 'N/A')} €")

    # 4. Calcolo Budget
    st.divider()
    deck_list = st.text_area("Incolla la lista (99 carte):", height=200)
    if st.button("Verifica Budget", type="primary"):
        if deck_list:
            linee = [l.strip() for l in deck_list.split("\n") if l.strip()]
            totale = 0.0
            with st.expander("Dettaglio Prezzi"):
                for riga in linee:
                    nome = re.sub(r'^(\d+x?|x)\s+', '', riga).split(' (')[0].strip()
                    if nome.lower() == cmd_input.lower(): continue
                    p = get_market_price(nome)
                    totale += p
                    st.write(f"{nome}: {p:.2f} €")
            
            st.divider()
            st.metric("TOTALE", f"{totale:.2f} €", delta=f"{100-totale:.2f} €", delta_color="normal" if totale<=100 else "inverse")
            if totale <= 100: st.balloons()
            else: st.error("Fuori budget!")
else:
    st.info("Inserisci un comandante per iniziare.")
