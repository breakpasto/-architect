import streamlit as st
import requests
import re
import time

# Configurazione della pagina per una visualizzazione ottimale su Mobile e Desktop
st.set_page_config(page_title="Commander Architect v2.0", page_icon="🧙‍♂️", layout="wide")

# --- FUNZIONI DI SUPPORTO (API) ---

def get_card(name):
    """Recupera i dati principali di una carta tramite Scryfall."""
    url = f"https://api.scryfall.com/cards/named?exact={name}"
    try:
        r = requests.get(url, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_market_price(card_name):
    """Recupera il prezzo medio 'eur' (Trend) per una carta specifica."""
    url = f"https://api.scryfall.com/cards/search?q=!\"{card_name}\"&unique=prints"
    try:
        r = requests.get(url, timeout=10).json()
        # Filtra solo i prezzi validi in Euro
        prices = [float(p['prices']['eur']) for p in r['data'] if p.get('prices', {}).get('eur')]
        return min(prices) if prices else 0.0
    except:
        return 0.0

def get_suggestions(colors):
    """Cerca carte sinergiche budget (< 2.50€) basate sulla popolarità EDHREC."""
    c_query = "".join(colors) if colors else "c"
    # Query: Legale in commander, identità colore, prezzo < 2.50, ordinata per rank EDHREC
    query = f"f:commander id<={c_query} eur<2.5 status:legal"
    url = f"https://api.scryfall.com/cards/search?q={query}&order=edhrec"
    try:
        r = requests.get(url, timeout=10).json()
        return r.get('data', [])[:12] # Restituisce le prime 12
    except:
        return []

def get_combos(commander_name):
    """Interroga il database di Commander Spellbook per trovare combo specifiche."""
    url = f"https://backend.commandspellbook.com/api/variants/?q={commander_name}"
    try:
        r = requests.get(url, timeout=10).json()
        return r.get('results', [])
    except:
        return []

# --- INTERFACCIA STREAMLIT ---

st.title("🧙‍♂️ Commander Deck Architect")
st.markdown("##### Crea mazzi budget da 100€ (Comandante Escluso)")

# Barra laterale per l'inserimento del Comandante
with st.sidebar:
    st.header("⚙️ Configurazione")
    cmd_name = st.text_input("Inserisci il tuo Comandante:", placeholder="Es: Muldrotha, the Gravetide")
    st.info("💡 Il costo del comandante NON viene conteggiato nel limite dei 100€.")

if cmd_name:
    cmd_data = get_card(cmd_name)
    if cmd_data:
        # Layout principale: Immagine e Suggerimenti/Combo
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(cmd_data['image_uris']['normal'], use_container_width=True)
            st.metric("Costo Comandante (Escluso)", f"{cmd_data.get('prices', {}).get('eur', '0.00')} €")
        
        with col2:
            tab1, tab2 = st.tabs(["🔥 Top 10 Combo", "💡 Suggerimenti Budget"])
            
            with tab1:
                st.subheader("Possibili Combo con il tuo Comandante")
                combos = get_combos(cmd_name)
                if combos:
                    # Mostra al massimo 10 combo come richiesto
                    for i, c in enumerate(combos[:10]):
                        # Estrae nomi delle carte coinvolte (escludendo il comandante dal titolo)
                        other_cards = [card['card']['name'] for card in c['uses'] if card['card']['name'].lower() != cmd_name.lower()]
                        title = f"Combo #{i+1}: {cmd_name} + {', '.join(other_cards[:2])}"
                        
                        with st.expander(title):
                            st.markdown("**Componenti:**")
                            for card in c['uses']:
                                st.write(f"- {card['card']['name']}")
                            
                            st.markdown("**Risultato:**")
                            risultati = [r['name'] for r in c['results']]
                            st.success(f"🎯 {', '.join(risultati)}")
                            
                            st.markdown("**Descrizione:**")
                            st.caption(c['description'])
                else:
                    st.write("Nessuna combo specifica trovata per questo comandante.")
            
            with tab2:
                st.subheader("Carte popolari sotto i 2.50€")
                suggestions = get_suggestions(cmd_data['color_identity'])
                if suggestions:
                    cols = st.columns(3)
                    for i, s in enumerate(suggestions):
                        with cols[i % 3]:
                            st.write(f"**{s['name']}**")
                            st.caption(f"Prezzo: {s.get('prices', {}).get('eur', 'N/A')}€")
                else:
                    st.write("Nessun suggerimento trovato per questa combinazione di colori.")

    # 2. SEZIONE COSTRUZIONE LISTA E BUDGET
    st.divider()
    st.subheader("📝 Mainboard Builder")
    st.write("Incolla le 99 carte (escluso il comandante).")
    
    lista_deck = st.text_area("Lista Moxfield:", height=200, placeholder="1 Sol Ring\n1 Arcane Signet...")
    
    if st.button("Verifica Budget (99 carte)", type="primary"):
        if lista_deck:
            linee = [l.strip() for l in lista_deck.split("\n") if l.strip()]
            totale_main = 0.0
            status = st.empty()
            
            with st.expander("Dettaglio Analisi Prezzi"):
                for l in linee:
                    # Pulizia nome carta (rimozione quantità e codici set)
                    nome_pulito = re.sub(r'^(\d+x?|x)\s+', '', l).split(' (')[0].strip()
                    
                    # Se il comandante è nella lista, non lo contiamo
                    if nome_pulito.lower() == cmd_name.lower():
                        st.info(f"ℹ️ {nome_pulito}: Identificato come Comandante (Costo 0.00€)")
                        continue
                        
                    status.text(f"🔍 Valutazione: {nome_pulito}...")
                    prezzo = get_market_price(nome_pulito)
                    totale_main += prezzo
                    st.write(f"{nome_pulito}: {prezzo:.2f}€")
                    time.sleep(0.05) # Per non bloccare le API
            
            status.empty()
            st.divider()
            
            # --- RISULTATO BUDGET ---
            is_legale = totale_main <= 100
            
            if is_legale:
                st.balloons()
                st.header(f"✅ Mazzo Legale: {totale_main:.2f} €")
            else:
                st.header(f"❌ Mazzo Fuori Budget: {totale_main:.2f} €")
            
            # Barra di progresso visuale
            st.progress(min(totale_main / 100, 1.0))
            
            c1, c2 = st.columns(2)
            c1.metric("Budget Utilizzato", f"{totale_main:.2f} €")
            c2.metric("Rimanenza / Sforamento", f"{100 - totale_main:.2f} €", delta_color="normal" if is_legale else "inverse")
            
            if not is_legale:
                st.error(f"Devi rimuovere {totale_main - 100:.2f} € dalla mainboard per rientrare nel limite.")
        else:
            st.warning("Incolla una lista di carte per procedere al calcolo.")
else:
    st.info("👈 Inserisci il nome del tuo Comandante nella barra laterale per iniziare!")
