import streamlit as st
import requests
import re
import time

# Configurazione Pagina
st.set_page_config(page_title="Commander Architect", page_icon="🧙‍♂️", layout="wide")

# --- FUNZIONI DI SUPPORTO ---
def get_card(name):
    url = f"https://api.scryfall.com/cards/named?exact={name}"
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

def get_market_price(card_name):
    url = f"https://api.scryfall.com/cards/search?q=!\"{card_name}\"&unique=prints"
    try:
        r = requests.get(url, timeout=10).json()
        prices = [float(p['prices']['eur']) for p in r['data'] if p.get('prices', {}).get('eur')]
        return min(prices) if prices else 0.0
    except: return 0.0

def get_suggestions(colors):
    # Cerca carte popolari (EDHREC) nei colori del comandante sotto i 2.50€
    c_query = "".join(colors) if colors else "c"
    query = f"f:commander id<={c_query} eur<2.5 status:legal"
    url = f"https://api.scryfall.com/cards/search?q={query}&order=edhrec"
    try:
        r = requests.get(url).json()
        return r.get('data', [])[:12]
    except: return []

def get_combos(commander_name):
    # Interroga il database di Commander Spellbook
    url = f"https://backend.commandspellbook.com/api/variants/?q={commander_name}"
    try:
        r = requests.get(url).json()
        return r.get('results', [])
    except: return []

# --- INTERFACCIA ---
st.title("🧙‍♂️ Commander Deck Architect")
st.markdown("##### Crea mazzi budget da 100€ (Comandante Escluso)")

# 1. SEZIONE COMANDANTE
with st.sidebar:
    st.header("⚙️ Impostazioni")
    cmd_name = st.text_input("Inserisci il tuo Comandante:", placeholder="Es: Muldrotha, the Gravetide")
    st.info("Il costo del comandante non verrà conteggiato nel budget di 100€.")

if cmd_name:
    cmd_data = get_card(cmd_name)
    if cmd_data:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(cmd_data['image_uris']['normal'], use_container_width=True)
            st.metric("Prezzo Comandante (Escluso)", f"{cmd_data.get('prices', {}).get('eur', '0.00')} €")
        
        with col2:
            tab1, tab2 = st.tabs(["🔥 Combo Suggerite", "💡 Carte Sinergiche Budget"])
            
            with tab1:
                combos = get_combos(cmd_name)
                if combos:
                    for c in combos[:5]:
                        with st.expander(f"Combo con {c['results'][0]['name']}"):
                            st.write(f"**Carte necessarie:** {', '.join([card['card']['name'] for card in c['uses']])}")
                            st.caption(f"Effetto: {c['description']}")
                else:
                    st.write("Nessuna combo specifica trovata nel database per questo comandante.")
            
            with tab2:
                suggestions = get_suggestions(cmd_data['color_identity'])
                cols = st.columns(3)
                for i, s in enumerate(suggestions):
                    cols[i % 3].write(f"**{s['name']}**")
                    cols[i % 3].caption(f"Prezzo: {s.get('prices', {}).get('eur', 'N/A')}€")

    # 2. COSTRUZIONE MAZZO E BUDGET
    st.divider()
    st.subheader("📝 Build del Mazzo")
    
    lista_deck = st.text_area("Incolla qui le 99 carte (1 per riga):", height=200, placeholder="1 Sol Ring\n1 Command Tower...")
    
    if st.button("Calcola Budget Mainboard"):
        if lista_deck:
            linee = [l.strip() for l in lista_deck.split("\n") if l.strip()]
            totale_main = 0.0
            status = st.empty()
            
            with st.expander("Dettaglio Prezzi Mainboard"):
                for l in linee:
                    nome_carta = re.sub(r'^(\d+x?|x)\s+', '', l).split(' (')[0].strip()
                    # Salta il comandante se è stato inserito anche nella lista
                    if nome_carta.lower() == cmd_name.lower():
                        st.write(f"ℹ️ {nome_carta} (Comandante) - Saltato dal conteggio")
                        continue
                        
                    status.text(f"Analisi: {nome_carta}...")
                    prezzo = get_market_price(nome_carta)
                    totale_main += prezzo
                    st.write(f"{nome_carta}: {prezzo:.2f}€")
                    time.sleep(0.05)
            
            status.empty()
            st.divider()
            
            # Risultato Finale
            is_legale = totale_main <= 100
            label = "✅ BUDGET LEGALE" if is_legale else "❌ FUORI BUDGET"
            st.header(f"{label}: {totale_main:.2f} €")
            st.progress(min(totale_main / 100, 1.0))
            
            if not is_legale:
                st.warning(f"Sei fuori budget di {(totale_main - 100):.2f} €. Il comandante è già escluso!")
            else:
                st.balloons()
else:
    st.info("Digita il nome di un comandante per iniziare!")
