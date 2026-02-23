import streamlit as st
import requests
import re
import time
import urllib.parse

st.set_page_config(page_title="Commander Architect v2.4", page_icon="🧙‍♂️", layout="wide")

# --- FUNZIONI API ---

def get_card(name):
    url = f"https://api.scryfall.com/cards/named?exact={urllib.parse.quote(name)}"
    try:
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_market_price(card_name):
    url = f"https://api.scryfall.com/cards/search?q=!\"{urllib.parse.quote(card_name)}\"&unique=prints"
    try:
        r = requests.get(url, timeout=10).json()
        prices = [float(p['prices']['eur']) for p in r['data'] if p.get('prices', {}).get('eur')]
        return min(prices) if prices else 0.0
    except:
        return 0.0

def get_suggestions(colors):
    c_query = "".join(colors) if colors else "c"
    query = f"f:commander id<={c_query} eur<2.5 status:legal"
    url = f"https://api.scryfall.com/cards/search?q={urllib.parse.quote(query)}&order=edhrec"
    try:
        r = requests.get(url, timeout=10).json()
        return r.get('data', [])[:12]
    except:
        return []

def get_combos(commander_name):
    """Versione Ultra-Resiliente con fallback"""
    # Proviamo diversi endpoint in ordine di stabilità
    endpoints = [
        f"https://backend.commandspellbook.com/variants/?q={urllib.parse.quote(commander_name)}",
        f"https://backend.commandspellbook.com/api/variants/?q={urllib.parse.quote(commander_name)}"
    ]
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MTG-Budget-App/3.0"}
    
    for url in endpoints:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, dict) and 'results' in data:
                    return data['results']
                if isinstance(data, list):
                    return data
        except:
            continue # Se fallisce questo endpoint, prova il prossimo
    
    return [] # Se tutti i tentativi falliscono, restituisce vuoto senza errore

# --- INTERFACCIA ---

st.title("🧙‍♂️ Commander Architect v2.4")

with st.sidebar:
    st.header("⚙️ Configurazione")
    cmd_name = st.text_input("Inserisci Comandante:", placeholder="Es: Ghave, Guru of Spores")

if cmd_name:
    cmd_data = get_card(cmd_name)
    if cmd_data:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(cmd_data['image_uris']['normal'], use_container_width=True)
            st.metric("Budget Escluso", f"{cmd_data.get('prices', {}).get('eur', '0.00')} €")
        
        with col2:
            tab1, tab2 = st.tabs(["🔥 Top 10 Combo", "💡 Suggerimenti Budget"])
            
            with tab1:
                st.subheader("Combo Rilevate")
                # Se la connessione fallisce del tutto, usiamo un messaggio più utile
                try:
                    combos = get_combos(cmd_name)
                    if combos:
                        for i, c in enumerate(combos[:10]):
                            uses = c.get('uses', [])
                            other_cards = [u['card']['name'] for u in uses if u['card']['name'].lower() != cmd_name.lower()]
                            title = f"Combo #{i+1}: {', '.join(other_cards[:2])}"
                            with st.expander(title):
                                for u in uses: st.write(f"- {u['card']['name']}")
                                res = [r['name'] for r in c.get('results', [])]
                                st.success(f"🎯 {', '.join(res)}")
                                st.caption(c.get('description', 'Nessuna descrizione.'))
                    else:
                        st.info("Nessuna combo trovata o database momentaneamente non raggiungibile.")
                except:
                    st.error("Errore critico nel caricamento delle combo.")

            with tab2:
                suggestions = get_suggestions(cmd_data['color_identity'])
                cols = st.columns(3)
                for i, s in enumerate(suggestions):
                    with cols[i % 3]:
                        st.write(f"**{s['name']}**")
                        st.caption(f"{s.get('prices', {}).get('eur', 'N/A')}€")

    # --- SEZIONE BUDGET ---
    st.divider()
    st.subheader("📝 Mainboard Builder (99 carte)")
    lista_deck = st.text_area("Incolla lista:", height=150)
    
    if st.button("Verifica Budget", type="primary"):
        if lista_deck:
            totale = 0.0
            linee = [l.strip() for l in lista_deck.split("\n") if l.strip()]
            with st.expander("Dettaglio Prezzi"):
                for l in linee:
                    nome = re.sub(r'^(\d+x?|x)\s+', '', l).split(' (')[0].strip()
                    if nome.lower() != cmd_name.lower():
                        p = get_market_price(nome)
                        totale += p
                        st.write(f"{nome}: {p:.2f}€")
            
            st.divider()
            st.metric("TOTALE (Senza Cmd)", f"{totale:.2f} €", delta=f"{100-totale:.2f} €", delta_color="normal" if totale <= 100 else "inverse")
            if totale > 100: st.error("Sei sopra i 100€!")
            else: st.balloons()
        r = requests.get(url, timeout=10).json()
        return r.get('data', [])[:12]
    except:
        return []

def get_combos(commander_name):
    """Interroga Commander Spellbook con gestione errori DNS e nuovi endpoint."""
    # Usiamo il filtro "q" per cercare il comandante nel database delle varianti
    safe_name = urllib.parse.quote(commander_name)
    url = f"https://backend.commandspellbook.com/variants/?q={safe_name}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            # La risposta può essere una lista o un dizionario con 'results'
            if isinstance(data, dict):
                return data.get('results', [])
            return data
        return []
    except Exception as e:
        # Messaggio di errore tecnico in console, ma l'utente vede un alert pulito
        return None

# --- INTERFACCIA UTENTE ---

st.title("🧙‍♂️ Commander Deck Architect v2.3")
st.markdown("##### Sviluppo Mazzi Budget 100€ (Comandante Escluso)")

with st.sidebar:
    st.header("⚙️ Configurazione")
    cmd_name = st.text_input("Inserisci il tuo Comandante:", placeholder="Es: Ghave, Guru of Spores")
    st.divider()
    st.info("L'app calcola il budget escludendo il costo del comandante scelto.")

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
                st.subheader(f"Combo rilevate per {cmd_name}")
                with st.spinner("Connessione a Commander Spellbook in corso..."):
                    combos = get_combos(cmd_name)
                
                if combos is None:
                    st.warning("⚠️ Impossibile raggiungere il database delle combo. Potrebbe esserci un problema temporaneo di rete o DNS.")
                elif combos:
                    # Mostra fino a 10 combo
                    for i, c in enumerate(combos[:10]):
                        # Estrae nomi delle altre carte
                        uses = c.get('uses', [])
                        other_cards = [u['card']['name'] for u in uses if u['card']['name'].lower() != cmd_name.lower()]
                        title = f"Combo #{i+1}: {', '.join(other_cards[:2])}"
                        
                        with st.expander(title):
                            st.markdown("**Componenti della combo:**")
                            for u in uses:
                                st.write(f"- {u['card']['name']}")
                            
                            st.markdown("**Risultato:**")
                            results = [r['name'] for r in c.get('results', [])]
                            st.success(f"🎯 {', '.join(results)}")
                            
                            st.markdown("**Esecuzione:**")
                            st.caption(c.get('description', 'Descrizione non disponibile.'))
                else:
                    st.info(f"Nessuna combo specifica trovata per '{cmd_name}'.")
            
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

    # --- SEZIONE CALCOLO BUDGET ---
    st.divider()
    st.subheader("📝 Verifica Budget Mainboard (Le altre 99 carte)")
    lista_deck = st.text_area("Incolla la lista (esportazione Moxfield o testo semplice):", height=200)
    
    if st.button("Calcola Totale Mainboard", type="primary"):
        if lista_deck:
            linee = [l.strip() for l in lista_deck.split("\n") if l.strip()]
            totale_main = 0.0
            status_calc = st.empty()
            
            with st.expander("Dettaglio Prezzi Mainboard"):
                for l in linee:
                    # Estrazione pulita del nome
                    nome_pulito = re.sub(r'^(\d+x?|x)\s+', '', l).split(' (')[0].strip()
                    
                    # Escludiamo il comandante se presente nella lista
                    if nome_pulito.lower() == cmd_name.lower():
                        st.info(f"ℹ️ {nome_pulito}: Comandante rilevato (Costo 0.00€)")
                        continue
                        
                    status_calc.text(f"🔍 Recupero prezzo: {nome_pulito}...")
                    prezzo = get_market_price(nome_pulito)
                    totale_main += prezzo
                    st.write(f"{nome_pulito}: {prezzo:.2f}€")
                    time.sleep(0.05) # Delay cortesia per API
            
            status_calc.empty()
            st.divider()
            
            # Verdetto Finale
            is_legale = totale_main <= 100
            if is_legale:
                st.balloons()
                st.header(f"✅ MAZZO BUDGET: {totale_main:.2f} €")
            else:
                st.header(f"❌ FUORI BUDGET: {totale_main:.2f} €")
            
            st.progress(min(totale_main / 100, 1.0))
            
            c1, c2 = st.columns(2)
            c1.metric("Totale Speso", f"{totale_main:.2f} €")
            c2.metric("Disponibilità", f"{100 - totale_main:.2f} €", delta_color="normal" if is_legale else "inverse")
        else:
            st.warning("Inserisci la lista delle carte per calcolare il budget.")
else:
    st.info("👈 Inserisci il nome del tuo Comandante nella barra laterale per iniziare!")
