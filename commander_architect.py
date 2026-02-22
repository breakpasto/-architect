import streamlit as st
import requests
import re
import time
import urllib.parse

# Configurazione della pagina
st.set_page_config(page_title="Commander Architect v2.1", page_icon="🧙‍♂️", layout="wide")

# --- FUNZIONI API ---

def get_card(name):
    """Recupera i dati della carta da Scryfall."""
    url = f"https://api.scryfall.com/cards/named?exact={urllib.parse.quote(name)}"
    try:
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_market_price(card_name):
    """Recupera il prezzo medio (Trend) da Scryfall."""
    url = f"https://api.scryfall.com/cards/search?q=!\"{urllib.parse.quote(card_name)}\"&unique=prints"
    try:
        r = requests.get(url, timeout=10).json()
        prices = [float(p['prices']['eur']) for p in r['data'] if p.get('prices', {}).get('eur')]
        return min(prices) if prices else 0.0
    except:
        return 0.0

def get_suggestions(colors):
    """Suggerisce carte budget basate su popolarità EDHREC."""
    c_query = "".join(colors) if colors else "c"
    query = f"f:commander id<={c_query} eur<2.5 status:legal"
    url = f"https://api.scryfall.com/cards/search?q={urllib.parse.quote(query)}&order=edhrec"
    try:
        r = requests.get(url, timeout=10).json()
        return r.get('data', [])[:12]
    except:
        return []

def get_combos(commander_name):
    """Interroga Commander Spellbook con gestione errori migliorata."""
    # Pulizia del nome per l'URL dell'API
    safe_name = urllib.parse.quote(f'"{commander_name}"')
    url = f"https://backend.commandspellbook.com/api/variants/?q={safe_name}"
    
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return data.get('results', [])
        else:
            return []
    except Exception as e:
        st.error(f"Errore di connessione al database combo: {e}")
        return []

# --- INTERFACCIA UTENTE ---

st.title("🧙‍♂️ Commander Deck Architect v2.1")
st.markdown("##### Sviluppo Mazzi Budget 100€ (Comandante Escluso)")

with st.sidebar:
    st.header("⚙️ Configurazione")
    cmd_name = st.text_input("Inserisci il tuo Comandante:", placeholder="Es: Ghave, Guru of Spores")
    st.divider()
    st.info("L'app cerca combo e suggerimenti basandosi sui dati in tempo reale di Scryfall e Commander Spellbook.")

if cmd_name:
    cmd_data = get_card(cmd_name)
    if cmd_data:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(cmd_data['image_uris']['normal'], use_container_width=True)
            st.metric("Prezzo Comandante (Escluso)", f"{cmd_data.get('prices', {}).get('eur', '0.00')} €")
        
        with col2:
            tab1, tab2 = st.tabs(["🔥 Top 10 Combo", "💡 Suggerimenti Budget"])
            
            with tab1:
                st.subheader(f"Combo con {cmd_name}")
                with st.spinner("Interrogazione database Commander Spellbook..."):
                    combos = get_combos(cmd_name)
                
                if combos:
                    for i, c in enumerate(combos[:10]):
                        # Estrae nomi delle carte coinvolte
                        other_cards = [card['card']['name'] for card in c['uses'] if card['card']['name'].lower() != cmd_name.lower()]
                        title = f"Combo #{i+1}: {cmd_name} + {', '.join(other_cards[:2])}"
                        
                        with st.expander(title):
                            st.markdown("**Componenti della combo:**")
                            for card in c['uses']:
                                st.write(f"- {card['card']['name']}")
                            
                            st.markdown("**Risultato:**")
                            res_names = [r['name'] for r in c['results']]
                            st.success(f"🎯 {', '.join(res_names)}")
                            
                            st.markdown("**Come funziona:**")
                            st.caption(c['description'])
                else:
                    st.warning(f"Nessuna combo specifica trovata per '{cmd_name}'. Prova a verificare il nome esatto (es. includi virgole).")
            
            with tab2:
                st.subheader("Sinergie Budget (< 2.50€)")
                suggestions = get_suggestions(cmd_data['color_identity'])
                if suggestions:
                    cols = st.columns(3)
                    for i, s in enumerate(suggestions):
                        with cols[i % 3]:
                            st.write(f"**{s['name']}**")
                            st.caption(f"Prezzo: {s.get('prices', {}).get('eur', 'N/A')}€")
                else:
                    st.write("Nessun suggerimento trovato.")

    # --- SEZIONE LISTA E BUDGET ---
    st.divider()
    st.subheader("📝 Verifica Budget Mainboard")
    lista_deck = st.text_area("Incolla qui la tua lista (99 carte):", height=200, placeholder="1 Sol Ring\n1 Arcane Signet...")
    
    if st.button("Calcola Totale Mainboard", type="primary"):
        if lista_deck:
            linee = [l.strip() for l in lista_deck.split("\n") if l.strip()]
            totale_main = 0.0
            status_calc = st.empty()
            
            with st.expander("Dettaglio Prezzi Singoli"):
                for l in linee:
                    nome_pulito = re.sub(r'^(\d+x?|x)\s+', '', l).split(' (')[0].strip()
                    
                    if nome_pulito.lower() == cmd_name.lower():
                        st.info(f"ℹ️ {nome_pulito}: Identificato come Comandante (Costo 0.00€)")
                        continue
                        
                    status_calc.text(f"🔍 Prezzo: {nome_pulito}...")
                    prezzo = get_market_price(nome_pulito)
                    totale_main += prezzo
                    st.write(f"{nome_pulito}: {prezzo:.2f}€")
                    time.sleep(0.05)
            
            status_calc.empty()
            st.divider()
            
            is_legale = totale_main <= 100
            if is_legale:
                st.balloons()
                st.success(f"### MAZZO LEGALE: {totale_main:.2f} €")
            else:
                st.error(f"### MAZZO FUORI BUDGET: {totale_main:.2f} €")
            
            st.progress(min(totale_main / 100, 1.0))
            
            c1, c2 = st.columns(2)
            c1.metric("Totale Speso", f"{totale_main:.2f} €")
            c2.metric("Differenza Budget", f"{100 - totale_main:.2f} €", delta_color="normal" if is_legale else "inverse")
        else:
            st.warning("Inserisci una lista per il calcolo.")
else:
    st.info("Inserisci il nome di un comandante nella barra laterale per caricare dati e combo.")
