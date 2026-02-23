import streamlit as st
import requests
import re
import time
import urllib.parse

# 1. Configurazione Iniziale
st.set_page_config(page_title="Commander Architect v3.1", page_icon="🧙‍♂️", layout="wide")

# --- FUNZIONI API (SCRYFALL ENGINE) ---

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

def get_archetypes(cmd_data):
    """Analizza il testo del comandante per identificare la strategia."""
    text = cmd_data.get('oracle_text', '').lower()
    type_line = cmd_data.get('type_line', '').lower()
    
    # Mappa delle sinergie comuni
    archetypes = {
        "Counters (+1/+1)": ["+1/+1", "counter", "proliferate", "doubling"],
        "Graveyard/Reanimate": ["graveyard", "return", "reanimate", "dredge", "undergrowth"],
        "Artifacts": ["artifact", "equipment", "vehicle", "sacrifice artifact"],
        "Tokens": ["token", "create", "populate", "horde"],
        "Spellslinger": ["instant", "sorcery", "copy", "magecraft"],
        "Sacrifice/Aristocrats": ["sacrifice", "dies", "aristocrat", "death-trigger"],
        "Enchantments": ["enchantment", "constellation", "aura"],
        "Life Gain": ["lifegain", "life", "gain"]
    }
    
    found = []
    for key, terms in archetypes.items():
        if any(term in text for term in terms):
            found.append(key)
    return found

def get_targeted_synergies(cmd_data, limit=12):
    """Cerca carte economiche basate sulle meccaniche del comandante."""
    colors = "".join(cmd_data['color_identity']) if cmd_data['color_identity'] else "c"
    archs = get_archetypes(cmd_data)
    
    # Costruzione query intelligente
    if not archs:
        # Se non riconosce meccaniche, cerca le migliori generiche sotto i 3€
        query = f"f:commander id<={colors} eur<3"
    else:
        # Crea filtri basati sulle parole chiave trovate
        search_parts = []
        if "Counters (+1/+1)" in archs: search_parts.append('o:"+1/+1"')
        if "Graveyard/Reanimate" in archs: search_parts.append('o:graveyard')
        if "Artifacts" in archs: search_parts.append('o:artifact')
        if "Tokens" in archs: search_parts.append('o:token')
        if "Spellslinger" in archs: search_parts.append('o:instant o:sorcery')
        if "Sacrifice/Aristocrats" in archs: search_parts.append('o:sacrifice')
        
        query = f"f:commander id<={colors} ({' OR '.join(search_parts)}) eur<3"

    url = f"https://api.scryfall.com/cards/search?q={urllib.parse.quote(query)}&order=edhrec"
    try:
        r = requests.get(url, timeout=10).json()
        return r.get('data', [])[:limit]
    except:
        return []

# --- INTERFACCIA STREAMLIT ---

st.title("🧙‍♂️ Commander Deck Architect v3.1")
st.markdown("##### Sinergie Mirate & Calcolo Budget 100€")

with st.sidebar:
    st.header("⚙️ Configurazione")
    cmd_input = st.text_input("Nome Comandante (Eng):", placeholder="Es: Muldrotha, the Gravetide")
    st.divider()
    st.info("Questa versione analizza le abilità del comandante per suggerire carte a tema.")

if cmd_input:
    cmd_data = get_card(cmd_input)
    if cmd_data:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(cmd_data['image_uris']['normal'], use_container_width=True)
            st.metric("Prezzo (Escluso)", f"{cmd_data.get('prices', {}).get('eur', '0.00')} €")
            
        with col2:
            tab1, tab2 = st.tabs(["🎯 Sinergie Mirate", "📊 Analisi Strategia"])
            
            with tab1:
                st.subheader("Carte Sinergiche Budget (< 3€)")
                with st.spinner("Analisi Oracle Text in corso..."):
                    results = get_targeted_synergies(cmd_data)
                
                if results:
                    c1, c2 = st.columns(2)
                    for idx, card in enumerate(results):
                        target = c1 if idx % 2 == 0 else c2
                        with target:
                            st.write(f"🔹 **{card['name']}**")
                            st.caption(f"{card.get('prices', {}).get('eur', 'N/A')}€ | {card['type_line']}")
                else:
                    st.info("Nessuna sinergia specifica trovata. Vengono mostrate le carte generiche migliori.")

            with tab2:
                st.subheader("Archetipi Rilevati")
                archs = get_archetypes(cmd_data)
                if archs:
                    for a in archs:
                        st.success(f"✔️ Meccanica rilevata: **{a}**")
                    st.caption("L'app sta filtrando i suggerimenti in base a queste etichette.")
                else:
                    st.warning("Meccanica specifica non identificata. L'analisi userà criteri standard.")

    # --- SEZIONE CALCOLO BUDGET ---
    st.divider()
    st.subheader("📝 Verifica Budget Mainboard (99 carte)")
    deck_list = st.text_area("Incolla la tua lista:", height=200, placeholder="1 Sol Ring\n1 Arcane Signet...")
    
    if st.button("Verifica Budget", type="primary"):
        if deck_list:
            linee = [l.strip() for l in deck_list.split("\n") if l.strip()]
            totale_main = 0.0
            
            with st.expander("Dettaglio Analisi Prezzi"):
                for l in linee:
                    nome_pulito = re.sub(r'^(\d+x?|x)\s+', '', l).split(' (')[0].strip()
                    if nome_pulito.lower() == cmd_input.lower():
                        continue
                    
                    prezzo = get_market_price(nome_pulito)
                    totale_main += prezzo
                    st.write(f"{nome_pulito}: {prezzo:.2f}€")
                    time.sleep(0.02) # Velocissimo
            
            st.divider()
            is_ok = totale_main <= 100
            st.metric("TOTALE MAZZO", f"{totale_main:.2f} €", delta=f"{100-totale_main:.2f} €" if is_ok else f"Sforato di {totale_main-100:.2f} €")
            
            if is_ok:
                st.success("✅ Mazzo entro il budget di 100€!")
                st.balloons()
            else:
                st.error("❌ Mazzo fuori budget!")
        else:
            st.warning("Incolla una lista per calcolare il prezzo.")
else:
    st.info("Inserisci il comandante nella barra laterale per iniziare.")
