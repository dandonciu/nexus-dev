import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import base64
import tempfile
from fpdf import FPDF
from backend.database.clients_config import clients_data, furnizor_data, client_aliases

PDF_DIR = tempfile.gettempdir()

def force_reset(): 
    st.session_state.reset_counter += 1

def reset_cart():
    st.session_state.schita_comanda = []
    st.session_state.last_success_msg = None
    force_reset()

def clean_text(txt):
    replacements = {'ă':'a', 'â':'a', 'î':'i', 'ș':'s', 'ț':'t', 'Ă':'A', 'Â':'A', 'Î':'I', 'Ș':'S', 'Ț':'T'}
    for k, v in replacements.items(): txt = str(txt).replace(k, v)
    return txt

def get_total_boxes(prod_key): 
    return (st.session_state.db[prod_key]['stock_pal'] * st.session_state.db[prod_key]['conversion']) + st.session_state.db[prod_key]['stock_box']

def get_available_stock_ui(prod_key):
    rem = get_total_boxes(prod_key) - sum([(i.get('Paleti', 0) * st.session_state.db[prod_key]['conversion']) + i.get('Cutii', 0) for i in st.session_state.schita_comanda if i.get('Produs') == prod_key])
    return rem // st.session_state.db[prod_key]['conversion'], rem % st.session_state.db[prod_key]['conversion']

def calculate_delta(prod_key, cmd_pal, cmd_box):
    return ((cmd_pal * st.session_state.db[prod_key]['conversion']) + cmd_box + sum([(i['Paleti'] * st.session_state.db[prod_key]['conversion']) + i['Cutii'] for i in st.session_state.schita_comanda if i['Produs'] == prod_key])) <= get_total_boxes(prod_key)

# ==========================================
# --- MOTOR PDF ---
# ==========================================
def generate_pdf_document(order_no, client_name, payload_fiscal, payload_log):
    pdf = FPDF(); c_data = clients_data[client_name]; f_data = furnizor_data
    data_azi = datetime.now().strftime('%d/%m/%Y')
    
    # PAGINA 1: AVIZ (Legal, fara preturi)
    pdf.add_page(); pdf.set_font("Arial", 'B', 14); pdf.cell(0, 8, "AVIZ DE INSOTIRE A MARFII", align='C', ln=1)
    pdf.set_font("Arial", '', 9); pdf.cell(0, 5, f"Seria NS nr. {order_no} | Data: {data_azi}", align='C', ln=1); pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 9); pdf.cell(95, 5, clean_text(f"Furnizor: {f_data['Nume']}"), ln=0); pdf.set_x(110); pdf.cell(85, 5, clean_text(f"Client: {client_name}"), ln=1)
    pdf.set_font("Arial", '', 8); pdf.cell(95, 4, f"CIF: {f_data['CIF']} | J: {f_data['RegCom']}", ln=0); pdf.set_x(110); pdf.cell(85, 4, f"CIF: {c_data['CIF']} | J: {c_data['RegCom']}", ln=1)
    pdf.cell(95, 4, clean_text(f"Adresa: {f_data['Adresa']}"), ln=0); pdf.set_x(110); pdf.multi_cell(85, 4, clean_text(f"Adresa: {c_data['Adresa']}")); pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 8); pdf.cell(10, 8, "Nr.", 1, 0, 'C'); pdf.cell(130, 8, "Denumirea produselor", 1, 0, 'C'); pdf.cell(20, 8, "U.M.", 1, 0, 'C'); pdf.cell(30, 8, "Cantitate", 1, 1, 'C')
    pdf.set_font("Arial", '', 8)
    for i, item in enumerate(payload_fiscal):
        pdf.cell(10, 5, str(i+1), 'L,T,R', 0, 'C'); pdf.cell(130, 5, clean_text(f"({item.get('Cod_Depozit', '-')}) {item['Nomenclator Oficial'][:75]}"), 'L,T,R', 0, 'L')
        pdf.cell(20, 5, clean_text(item['Cantitate (U.M.)'].split(' ')[1]), 'L,T,R', 0, 'C'); pdf.cell(30, 5, str(float(item['Cantitate (U.M.)'].split(' ')[0])), 'L,T,R', 1, 'C')
        pdf.cell(10, 4, "", 'L,B,R', 0, 'C'); pdf.set_text_color(100, 100, 100); pdf.cell(130, 4, "Cod NC: 48236990", 'L,B,R', 0, 'L'); pdf.set_text_color(0, 0, 0)
        pdf.cell(20, 4, "", 'L,B,R', 0, 'C'); pdf.cell(30, 4, "", 'L,B,R', 1, 'C')
    for _ in range(2):
        pdf.cell(10, 6, "", 1, 0); pdf.cell(130, 6, "", 1, 0); pdf.cell(20, 6, "", 1, 0); pdf.cell(30, 6, "", 1, 1)

    pdf.set_font("Arial", 'B', 8); pdf.cell(190, 6, f"Nr. comanda achizitie: AR {order_no}/{data_azi.split('/')[2]}", 'L,T,R', 1, 'L')
    pdf.set_font("Arial", '', 8); pdf.cell(190, 6, f"AR {order_no} (Comanda {client_name})", 'L,B,R', 1, 'L'); pdf.ln(5)
    
    pdf.cell(95, 5, "Semnatura si stampila furnizorului:", 'L,T,R', 0, 'L'); pdf.cell(95, 5, "Date privind expeditia:", 'L,T,R', 1, 'L')
    pdf.cell(95, 5, "", 'L,R', 0, 'L'); pdf.cell(95, 5, "Numele delegatului: .....................................................", 'L,R', 1, 'L')
    pdf.set_font("Arial", '', 6); pdf.cell(95, 5, "Intocmit de: NEXUS Auto-Sistem", 'L,R', 0, 'L'); pdf.set_font("Arial", '', 8)
    pdf.cell(95, 5, "Mijloc de transport: ................................. nr: ..................", 'L,R', 1, 'L')
    pdf.cell(95, 5, "", 'L,B,R', 0, 'L'); pdf.cell(95, 5, f"Expedierea s-a facut in prezenta noastra la data: {data_azi}", 'L,B,R', 1, 'L')

    # PAGINA 2: DISPOZITIE DEPOZIT
    pdf.add_page(); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "DISPOZITIE DE LIVRARE (COMANDA DEPOZIT)", align='C', ln=1)
    pdf.set_font("Arial", '', 10); pdf.cell(0, 5, f"Nr. {order_no} / Data: {data_azi}", align='C', ln=1); pdf.ln(10)
    pdf.set_font("Arial", 'B', 9); pdf.cell(10, 8, "Nr", 1, 0, 'C'); pdf.cell(30, 8, "Cod Raft", 1, 0, 'C'); pdf.cell(110, 8, "Denumire / Instructiune Stivuitorist", 1, 0, 'C'); pdf.cell(20, 8, "Cant", 1, 0, 'C'); pdf.cell(20, 8, "U/M", 1, 1, 'C')
    
    pdf.set_font("Arial", '', 9)
    for i, item in enumerate(payload_log):
        is_palet = "PAL" in item['UM'].upper()
        pdf.cell(10, 8, str(i+1), 1, 0, 'C'); pdf.set_font("Arial", 'B' if is_palet else '', 9)
        pdf.cell(30, 8, str(item.get('Cod Gestiune', '-')), 1, 0, 'C'); pdf.set_font("Arial", '', 9)    
        # Aici lasam textul sa fie un pic mai lung pentru sfat
        pdf.cell(110, 8, clean_text(item['Denumire'][:85]), 1, 0); pdf.cell(20, 8, str(item['Cant']), 1, 0, 'C')
        if is_palet: pdf.set_fill_color(220, 220, 220); pdf.cell(20, 8, item['UM'], 1, 1, 'C', fill=True)
        else: pdf.cell(20, 8, item['UM'], 1, 1, 'C')

    pdf.ln(20); pdf.cell(0, 5, "Dispus livrarea ....................      Gestionar ....................      Primitor ....................", ln=1)
    filepath = os.path.join(PDF_DIR, f"DOCUMENTE_NEXUS_{order_no}.pdf")
    pdf.output(filepath)
    return filepath

def display_pdf(file_path):
    with open(file_path, "rb") as f: base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    st.markdown(f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>', unsafe_allow_html=True)

# ==========================================
# --- FUNCTIA PRINCIPALA A MODULULUI ---
# ==========================================
def render_lansare_module():
    if 'order_number' not in st.session_state: st.session_state.order_number = 218395
    if 'reset_counter' not in st.session_state: st.session_state.reset_counter = 0
    if 'schita_comanda' not in st.session_state: st.session_state.schita_comanda = []
    if 'mod_previzualizare' not in st.session_state: st.session_state.mod_previzualizare = False
    if 'istoric_comenzi_live' not in st.session_state: st.session_state.istoric_comenzi_live = []
    if 'last_success_msg' not in st.session_state: st.session_state.last_success_msg = None

    col_titlu, col_cmd = st.columns([4, 1])
    with col_titlu: st.title("📦 NEXUS Lansare Comenzi")
    with col_cmd: st.info(f"**Nr. Cmd:** {st.session_state.order_number}\n\n**Data:** {datetime.now().strftime('%d.%m.%Y')}")

    tab1, tab2 = st.tabs(["🛒 Formare Comandă", "🚚 Gestiune Rampă & Acte"])
    
    with tab1:
        comenzi_asteapta_acte = [c for c in st.session_state.istoric_comenzi_live if c['Status'] == "Incarcat"]
        if len(comenzi_asteapta_acte) > 0:
            st.error(f"🚨 ACȚIUNE NECESARĂ: {len(comenzi_asteapta_acte)} comandă(i) au fost încărcate! Treci la Rampă pentru a emite PDF-urile.")
        
        if st.session_state.last_success_msg:
            st.success(st.session_state.last_success_msg)

        if not st.session_state.mod_previzualizare:
            client_ales = st.selectbox("Client (schimbarea golește coșul!)", list(clients_data.keys()), on_change=reset_cart)
            baza_produse = list(st.session_state.db.keys()); aliasuri_client_curent = client_aliases.get(client_ales, {})
            selected_option = st.selectbox("Produs", baza_produse + list(aliasuri_client_curent.keys()), on_change=force_reset, key="select_prod")
            
            if selected_option in aliasuri_client_curent:
                prod_name = aliasuri_client_curent[selected_option]; alias_folosit = selected_option
                st.info(f"🔄 Alias recunoscut: **{selected_option}** = **{prod_name}**")
            else: prod_name = selected_option; alias_folosit = None

            p_data = st.session_state.db[prod_name]
            av_pal, av_box = get_available_stock_ui(prod_name)
            
            # --- BLOCUL VERDE ADAUGAT INAPOI AICI ---
            st.markdown(f"""
            <div style='background-color: #f0f7f4; padding: 20px; border-radius: 8px; border-left: 5px solid #28a745; margin-bottom: 20px;'>
                <div style='display: flex; flex-wrap: wrap; justify-content: space-between;'>
                    <div style='flex: 1; min-width: 180px; margin-bottom: 10px;'>
                        <div style='font-size: 0.85rem; color: #555; margin-bottom: 2px;'>Cod produs (NEXUS)</div>
                        <div style='font-size: 1.4rem; color: #28a745; font-weight: bold;'>{p_data.get('cod_master', '-')}</div>
                    </div>
                    <div style='flex: 1; min-width: 150px; margin-bottom: 10px;'>
                        <div style='font-size: 0.85rem; color: #555; margin-bottom: 2px;'>Cod NIR</div>
                        <div style='font-size: 1.4rem; color: #28a745; font-weight: bold;'>{p_data.get('cod_nir', '-')}</div>
                    </div>
                    <div style='flex: 1; min-width: 200px; margin-bottom: 10px;'>
                        <div style='font-size: 0.85rem; color: #555; margin-bottom: 2px;'>Cod dB Depozit (Palet)</div>
                        <div style='font-size: 1.4rem; color: #28a745; font-weight: bold;'>{p_data.get('oracle_pal', '-')}</div>
                    </div>
                    <div style='flex: 1; min-width: 150px; margin-bottom: 10px;'>
                        <div style='font-size: 0.85rem; color: #555; margin-bottom: 2px;'>Cod dB Depozit (Cutie)</div>
                        <div style='font-size: 1.4rem; color: #28a745; font-weight: bold;'>{p_data.get('oracle_box', '-')}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            # ----------------------------------------
            
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            col_s1.metric("📦 Stoc PALEȚI", av_pal); col_s2.metric("📦 Stoc CUTII", av_box)
            col_s3.metric("🔄 WMS", f"{p_data['conversion']} cut/pal"); col_s4.metric("⚖️ Fiscal", f"{p_data['conversie_baza']} {p_data['um_baza']}/cut")
            
            col_q1, col_q2, _ = st.columns([1, 1, 2])
            with col_q1: order_pal = st.number_input("Nr. PALEȚI:", min_value=0, step=1, key=f'input_pal_{st.session_state.reset_counter}')
            with col_q2: order_box = st.number_input("Nr. CUTII (fracție):", min_value=0, step=1, key=f'input_box_{st.session_state.reset_counter}')
            
            if st.button("➕ Adaugă în Listă"):
                st.session_state.last_success_msg = None 
                if order_pal == 0 and order_box == 0: st.warning("Introduceți o cantitate.")
                elif not calculate_delta(prod_name, order_pal, order_box): st.error("❌ STOC INSUFICIENT!")
                else:
                    st.session_state.schita_comanda.append({"Produs": prod_name, "Cod_NIR": p_data['cod_nir'], "Alias_Folosit": alias_folosit, "Paleti": order_pal, "Cutii": order_box, "Cod_Depozit_Pal": p_data['oracle_pal'], "Cod_Depozit_Box": p_data['oracle_box'], "UM_Baza": p_data['um_baza'], "Conversie_Baza": p_data['conversie_baza']})
                    force_reset(); st.rerun()

            st.divider()
            if len(st.session_state.schita_comanda) > 0:
                st.markdown(f"#### 🛒 Produse în comandă (Către: **{client_ales}**)")
                for idx, item in enumerate(st.session_state.schita_comanda):
                    c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
                    c1.markdown(item['Produs'] + (f" <br><span style='color:#e67e22;font-size:0.85rem;'>(Ref: {item['Alias_Folosit']})</span>" if item.get('Alias_Folosit') else ""), unsafe_allow_html=True)
                    c2.markdown(f"{item['Cod_Depozit_Pal']} / {item['Cod_Depozit_Box']}")
                    c3.markdown(f"**{item['Paleti']}** Pal | **{item['Cutii']}** Cut")
                    c4.markdown(f"**{((item['Paleti'] * st.session_state.db[item['Produs']]['conversion']) + item['Cutii']) * item['Conversie_Baza']}** {item['UM_Baza']}")
                    if c5.button("❌", key=f"del_row_{idx}"): st.session_state.schita_comanda.pop(idx); st.rerun()
                
                st.divider()
                c_btn1, c_btn2 = st.columns([1, 3])
                with c_btn1:
                    if st.button("🗑️ Golește Lista"): reset_cart(); st.rerun()
                with c_btn2:
                    if st.button("👁️ Previzualizare și Scindare Dimo-NEXUS", type="primary", use_container_width=True):
                        st.session_state.client_temporar_comandat = client_ales
                        st.session_state.mod_previzualizare = True; st.rerun()

        # ECRAN B: PREVIZUALIZARE DIMO-NEXUS
        else:
            client_ales_prev = st.session_state.client_temporar_comandat
            st.markdown("### 🔍 Previzualizare & Lansare")
            
            payload_log = []; payload_fisc = []

            for item in st.session_state.schita_comanda:
                nf = item['Produs']; P = st.session_state.db[nf]['conversion']; L = st.session_state.db[nf]['stock_box']
                
                # AUTO-CONVERSIE ABSOLUTĂ (Indiferent ce tastează omul, NEXUS sparge în Paleți + Rest)
                total_baxuri = (item['Paleti'] * P) + item['Cutii']
                pal = total_baxuri // P
                C = total_baxuri % P
                
                if C > 0:
                    if (P - C) < C and L < C:
                        if pal > 0: payload_log.append({"Cod Gestiune": item['Cod_Depozit_Pal'], "Denumire": f"{nf} (Sigilat)", "Cant": str(pal), "UM": "PAL"})
                        payload_log.append({"Cod Gestiune
