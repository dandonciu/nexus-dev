import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import base64
import tempfile
from fpdf import FPDF
from backend.database.clients_config import clients_data, furnizor_data, client_aliases

PDF_DIR = tempfile.gettempdir()

def force_reset(): st.session_state.reset_counter += 1

def reset_cart():
    st.session_state.schita_comanda = []
    st.session_state.last_success_msg = None
    force_reset()

def clean_text(txt):
    replacements = {'ă':'a', 'â':'a', 'î':'i', 'ș':'s', 'ț':'t', 'Ă':'A', 'Â':'A', 'Î':'I', 'Ș':'S', 'Ț':'T', '↳':'->', '🍺':''}
    for k, v in replacements.items(): txt = str(txt).replace(k, v)
    return txt

def get_total_boxes(prod_key): 
    return (st.session_state.db[prod_key]['stock_pal'] * st.session_state.db[prod_key]['conversion']) + st.session_state.db[prod_key]['stock_box']

def get_available_stock_ui(prod_key):
    total_fizic = get_total_boxes(prod_key)
    in_cart = sum([(i.get('Paleti', 0) * st.session_state.db[prod_key]['conversion']) + i.get('Cutii', 0) for i in st.session_state.schita_comanda if i.get('Produs') == prod_key])
    rem = total_fizic - in_cart
    return rem // st.session_state.db[prod_key]['conversion'], rem % st.session_state.db[prod_key]['conversion']

def calculate_delta(prod_key, cmd_pal, cmd_box):
    return ((cmd_pal * st.session_state.db[prod_key]['conversion']) + cmd_box + sum([(i['Paleti'] * st.session_state.db[prod_key]['conversion']) + i['Cutii'] for i in st.session_state.schita_comanda if i['Produs'] == prod_key])) <= get_total_boxes(prod_key)

# ==========================================
# --- MOTOARE GENERARE PDF SEPARATE ---
# ==========================================

def generate_pdf_dispozitie(order_no, payload_log):
    pdf = FPDF()
    data_azi = datetime.now().strftime('%d/%m/%Y')
    pdf.add_page(); pdf.set_font("Arial", 'B', 12); pdf.cell(0, 8, "DISPOZITIE DE LIVRARE (COMANDA DEPOZIT)", align='C', ln=1)
    pdf.set_font("Arial", '', 10); pdf.cell(0, 5, f"Cmd NEXUS: {order_no} | Data: {data_azi}", align='C', ln=1); pdf.ln(10)
    pdf.set_font("Arial", 'B', 9); pdf.cell(10, 8, "Nr", 1, 0, 'C'); pdf.cell(30, 8, "Cod Raft", 1, 0, 'C'); pdf.cell(110, 8, "Denumire / Instructiune Stivuitorist", 1, 0, 'C'); pdf.cell(20, 8, "Cant", 1, 0, 'C'); pdf.cell(20, 8, "U/M", 1, 1, 'C')
    pdf.set_font("Arial", '', 9)
    for i, item in enumerate(payload_log):
        is_palet = "PAL" in item['UM'].upper()
        pdf.cell(10, 8, str(i+1), 1, 0, 'C'); pdf.set_font("Arial", 'B' if is_palet else '', 9)
        pdf.cell(30, 8, str(item.get('Cod Gestiune', '-')), 1, 0, 'C'); pdf.set_font("Arial", '', 9)    
        pdf.cell(110, 8, clean_text(item['Denumire'][:85]), 1, 0); pdf.cell(20, 8, str(item['Cant']), 1, 0, 'C')
        if is_palet: pdf.set_fill_color(220, 220, 220); pdf.cell(20, 8, item['UM'], 1, 1, 'C', fill=True)
        else: pdf.cell(20, 8, item['UM'], 1, 1, 'C')
    pdf.ln(15); pdf.cell(0, 5, "NEXUS B2B Auto-Generated", ln=1)
    filepath = os.path.join(PDF_DIR, f"Dispozitie_Depozit_{order_no}.pdf")
    pdf.output(filepath)
    return filepath

def generate_pdf_aviz(order_no, client_name, payload_fiscal):
    pdf = FPDF(); c_data = clients_data[client_name]; f_data = furnizor_data
    data_azi = datetime.now().strftime('%d/%m/%Y')
    pdf.add_page(); pdf.set_font("Arial", 'B', 14); pdf.cell(0, 8, "AVIZ DE INSOTIRE A MARFII", align='C', ln=1)
    pdf.set_font("Arial", '', 9); pdf.cell(0, 5, f"Seria NS nr. {order_no} | Data: {data_azi}", align='C', ln=1); pdf.ln(5)
    pdf.set_font("Arial", 'B', 9); pdf.cell(95, 5, clean_text(f"Furnizor: {f_data['Nume']}"), ln=0); pdf.set_x(110); pdf.cell(85, 5, clean_text(f"Client: {client_name}"), ln=1)
    pdf.set_font("Arial", '', 8); pdf.cell(95, 4, f"CIF: {f_data['CIF']} | J: {f_data['RegCom']}", ln=0); pdf.set_x(110); pdf.cell(85, 4, f"CIF: {c_data['CIF']} | J: {c_data['RegCom']}", ln=1)
    pdf.cell(95, 4, clean_text(f"Adresa: {f_data['Adresa']}"), ln=0); pdf.set_x(110); pdf.multi_cell(85, 4, clean_text(f"Adresa: {c_data['Adresa']}")); pdf.ln(5)
    pdf.set_font("Arial", 'B', 8); pdf.cell(10, 8, "Nr.", 1, 0, 'C'); pdf.cell(130, 8, "Denumirea produselor", 1, 0, 'C'); pdf.cell(20, 8, "U.M.", 1, 0, 'C'); pdf.cell(30, 8, "Cantitate", 1, 1, 'C')
    pdf.set_font("Arial", '', 8)
    for i, item in enumerate(payload_fiscal):
        pdf.cell(10, 5, str(i+1), 'L,T,R', 0, 'C'); pdf.cell(130, 5, clean_text(f"({item.get('Cod_Depozit', '-')}) {item['Nomenclator Oficial'][:75]}"), 'L,T,R', 0, 'L')
        um_split = item['Cantitate (U.M.)'].split(' ')
        val_c = um_split[0]; um_c = um_split[1] if len(um_split) > 1 else ""
        pdf.cell(20, 5, clean_text(um_c), 'L,T,R', 0, 'C'); pdf.cell(30, 5, str(float(val_c)), 'L,T,R', 1, 'C')
        pdf.cell(10, 4, "", 'L,B,R', 0, 'C'); pdf.set_text_color(100, 100, 100); pdf.cell(130, 4, "Cod NC: 48236990", 'L,B,R', 0, 'L'); pdf.set_text_color(0, 0, 0)
        pdf.cell(20, 4, "", 'L,B,R', 0, 'C'); pdf.cell(30, 4, "", 'L,B,R', 1, 'C')
    for _ in range(2):
        pdf.cell(10, 6, "", 1, 0); pdf.cell(130, 6, "", 1, 0); pdf.cell(20, 6, "", 1, 0); pdf.cell(30, 6, "", 1, 1)
    pdf.set_font("Arial", 'B', 8); pdf.cell(190, 6, f"Nr. comanda achizitie: AR {order_no}/{data_azi.split('/')[2]}", 'L,T,R', 1, 'L')
    pdf.set_font("Arial", '', 8); pdf.cell(190, 6, f"AR {order_no} (Comanda {client_name})", 'L,B,R', 1, 'L'); pdf.ln(5)
    pdf.cell(95, 5, "Semnatura si stampila furnizorului:", 'L,T,R', 0, 'L'); pdf.cell(95, 5, "Date privind expeditia:", 'L,T,R', 1, 'L')
    pdf.cell(95, 5, "", 'L,R', 0, 'L'); pdf.cell(95, 5, "Nume delegat / Transportator:", 'L,R', 1, 'L')
    pdf.cell(95, 5, "NOVA SAFE SRL", 'L,B,R', 0, 'L'); pdf.cell(95, 5, f"Data expedierii: {data_azi}", 'L,B,R', 1, 'L')
    filepath = os.path.join(PDF_DIR, f"Aviz_{order_no}.pdf")
    pdf.output(filepath)
    return filepath

def generate_pdf_certificat(order_no, client_name, payload_fiscal):
    pdf = FPDF(); c_data = clients_data[client_name]; f_data = furnizor_data
    data_azi = datetime.now().strftime('%d/%m/%Y')
    pdf.add_page(); pdf.set_font("Arial", 'B', 14); pdf.cell(0, 8, "CERTIFICAT DE CONFORMITATE SI CALITATE", align='C', ln=1)
    pdf.set_font("Arial", '', 9); pdf.cell(0, 5, f"Pentru Aviz NS nr. {order_no} | Data: {data_azi}", align='C', ln=1); pdf.ln(10)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 6, clean_text(f"Subscrisa {f_data['Nume']}, declaram pe propria raspundere ca produsele livrate catre {client_name}, mentionate mai jos, respecta standardele de calitate si siguranta in vigoare."))
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 9); pdf.cell(20, 8, "Nr.", 1, 0, 'C'); pdf.cell(140, 8, "Produs Livrat", 1, 0, 'C'); pdf.cell(30, 8, "Cantitate", 1, 1, 'C')
    pdf.set_font("Arial", '', 9)
    for i, item in enumerate(payload_fiscal):
        pdf.cell(20, 6, str(i+1), 1, 0, 'C'); pdf.cell(140, 6, clean_text(f"{item['Nomenclator Oficial'][:80]}"), 1, 0, 'L'); pdf.cell(30, 6, clean_text(item['Cantitate (U.M.)']), 1, 1, 'C')
    pdf.ln(15)
    pdf.set_font("Arial", 'B', 10); pdf.cell(0, 6, "Reprezentant Calitate NOVA SAFE SRL,", ln=1)
    filepath = os.path.join(PDF_DIR, f"Certificat_Conf_{order_no}.pdf")
    pdf.output(filepath)
    return filepath


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

    tab1, tab2, tab3 = st.tabs(["🛒 Formare Comandă", "🚚 Gestiune Rampă & Acte", "📜 Istoric & Arhivă"])
    
    with tab1:
        comenzi_asteapta_acte = [c for c in st.session_state.istoric_comenzi_live if c['Status'] in ["Incarcat", "Draft Acte"]]
        if len(comenzi_asteapta_acte) > 0:
            st.error(f"🚨 ACȚIUNE NECESARĂ: {len(comenzi_asteapta_acte)} comandă(i) au marfa încărcată! Treci la Rampă pentru Validare și SEND.")
        
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
            
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            col_s1.metric("📦 Stoc PALEȚI", av_pal); col_s2.metric("📦 Stoc CUTII", av_box)
            col_s3.metric("🔄 WMS", f"{p_data['conversion']} cut/pal"); col_s4.metric("⚖️ Fiscal", f"{p_data.get('conversie_baza','-')} {p_data.get('um_baza','-')}/cut")
            
            col_q1, col_q2, _ = st.columns([1, 1, 2])
            with col_q1: order_pal = st.number_input("Nr. PALEȚI:", min_value=0, step=1, key=f'input_pal_{st.session_state.reset_counter}')
            with col_q2: order_box = st.number_input("Nr. CUTII (fracție):", min_value=0, step=1, key=f'input_box_{st.session_state.reset_counter}')
            
            if st.button("➕ Adaugă în Listă"):
                st.session_state.last_success_msg = None 
                if order_pal == 0 and order_box == 0: st.warning("Introduceți o cantitate.")
                elif not calculate_delta(prod_name, order_pal, order_box): st.error("❌ STOC INSUFICIENT!")
                else:
                    st.session_state.schita_comanda.append({"Produs": prod_name, "Cod_NIR": p_data.get('cod_nir','-'), "Alias_Folosit": alias_folosit, "Paleti": order_pal, "Cutii": order_box, "Cod_Depozit_Pal": p_data['oracle_pal'], "Cod_Depozit_Box": p_data['oracle_box'], "UM_Baza": p_data.get('um_baza','-'), "Conversie_Baza": p_data.get('conversie_baza', 1)})
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

        # ECRAN B: PREVIZUALIZARE & SCINDARE CORECTĂ
        else:
            client_ales_prev = st.session_state.client_temporar_comandat
            st.markdown("### 🔍 Previzualizare & Lansare")
            
            payload_log = []; payload_fisc = []

            for item in st.session_state.schita_comanda:
                nf = item['Produs']
                P = st.session_state.db[nf]['conversion']
                L = st.session_state.db[nf]['stock_box'] 
                conv = item['Conversie_Baza']
                um = item['UM_Baza']
                
                total_baxuri = (item['Paleti'] * P) + item['Cutii']
                pal = total_baxuri // P
                C = total_baxuri % P
                
                if pal > 0:
                    txt_pal = f"cutii cod {item['Cod_Depozit_Pal']} - {pal} palet(i) = {pal * P} cutii"
                    payload_fisc.append({"Cod_Depozit": item['Cod_Depozit_Pal'], "Nomenclator Oficial": txt_pal, "Cantitate (U.M.)": f"{pal * P * conv} {um}"})
                
                if C > 0:
                    if C <= L:
                        txt_liber = f"cutii cod {item['Cod_Depozit_Box']} - {C} cutii"
                        payload_fisc.append({"Cod_Depozit": item['Cod_Depozit_Box'], "Nomenclator Oficial": txt_liber, "Cantitate (U.M.)": f"{C * conv} {um}"})
                        payload_log.append({"Cod Gestiune": item['Cod_Depozit_Box'], "Denumire": nf, "Cant": str(C), "UM": "Cutii"})
                        payload_log.append({"Cod Gestiune": "->", "Denumire": "Sfat: Iei din stocul liber de pe raft", "Cant": "-", "UM": "-"})
                    else:
                        if L > 0: 
                            txt_liber_2 = f"cutii cod {item['Cod_Depozit_Box']} - {L} cutii"
                            payload_fisc.append({"Cod_Depozit": item['Cod_Depozit_Box'], "Nomenclator Oficial": txt_liber_2, "Cantitate (U.M.)": f"{L * conv} {um}"})
                            payload_log.append({"Cod Gestiune": item['Cod_Depozit_Box'], "Denumire": nf, "Cant": str(L), "UM": "Cutii"})
                            payload_log.append({"Cod Gestiune": "->", "Denumire": f"Sfat: Iei {L} cutii ramase libere", "Cant": "-", "UM": "-"})
                        
                        txt_spart = f"cutii cod {item['Cod_Depozit_Pal']} - {C - L} cutii"
                        payload_fisc.append({"Cod_Depozit": item['Cod_Depozit_Pal'], "Nomenclator Oficial": txt_spart, "Cantitate (U.M.)": f"{(C - L) * conv} {um}"})
                        payload_log.append({"Cod Gestiune": item['Cod_Depozit_Pal'], "Denumire": f"{nf} (Spart din palet)", "Cant": str(C - L), "UM": "Cutii"})
                        payload_log.append({"Cod Gestiune": "->", "Denumire": "Sfat: Desfaci 1 Palet Nou pentru restul", "Cant": "-", "UM": "-"})

                if pal > 0: 
                    payload_log.insert(0, {"Cod Gestiune": item['Cod_Depozit_Pal'], "Denumire": f"{nf} (Sigilat)", "Cant": str(pal), "UM": "PAL"})

            cp1, cp2 = st.columns(2)
            with cp1: st.warning("🚚 Spre Stivuitorist"); st.dataframe(pd.DataFrame(payload_log)[['Cod Gestiune', 'Denumire', 'Cant', 'UM']], hide_index=True)
            with cp2: st.success("🧾 Spre SmartBill"); st.dataframe(pd.DataFrame(payload_fisc)[['Cod_Depozit', 'Nomenclator Oficial', 'Cantitate (U.M.)']], hide_index=True)
            
            st.divider()
            c_b1, c_b2, c_b3 = st.columns([1, 2, 2])
            with c_b1:
                if st.button("🔙 Întoarce-te"): st.session_state.mod_previzualizare = False; st.rerun()
            
            def executa_lansare():
                for item in st.session_state.schita_comanda:
                    p = item['Produs']; P = st.session_state.db[p]['conversion']; C = item['Cutii']; pal = item['Paleti']
                    s_ramas = get_total_boxes(p) - ((pal * P) + C)
                    st.session_state.db[p]['stock_pal'] = s_ramas // P; st.session_state.db[p]['stock_box'] = s_ramas % P
                
                # GENERAM DOAR DISPOZITIA DE DEPOZIT AICI!
                pdf_disp = generate_pdf_dispozitie(st.session_state.order_number, payload_log)

                st.session_state.istoric_comenzi_live.append({
                    "Comanda": st.session_state.order_number, "Client": client_ales_prev,
                    "Schita_Originala": st.session_state.schita_comanda.copy(),
                    "Payload_Logistic": payload_log, "Payload_Fiscal": payload_fisc, 
                    "Status": "Asteapta Incarcare", "pdf_dispozitie": pdf_disp
                })
                st.session_state.order_number += 1
                st.session_state.schita_comanda = []
                st.session_state.mod_previzualizare = False
                
            with c_b2:
                if st.button("🚀 Lansează și rămâi AICI", use_container_width=True):
                    executa_lansare()
                    st.session_state.last_success_msg = f"✅ Comanda NS-{st.session_state.order_number - 1} a fost trimisă la Depozit. Poți adăuga una nouă."
                    st.rerun()
            with c_b3:
                if st.button("🚚 Lansează și mergi la RAMPĂ", type="primary", use_container_width=True):
                    executa_lansare()
                    st.session_state.last_success_msg = f"✅ Comanda NS-{st.session_state.order_number - 1} e la Depozit! (Vezi Tab-ul 'Gestiune Rampă')"
                    st.rerun()

    # ==========================================
    # --- TAB 2: GESTIUNE RAMPĂ & ACTE ---
    # ==========================================
    with tab2:
        st.markdown("### 🚚 Gestiune Rampă (Validare și SEND)")
        if len(st.session_state.istoric_comenzi_live) == 0: st.info("Nicio comandă la rampă.")
        
        for idx, cmd in enumerate(reversed(st.session_state.istoric_comenzi_live)):
            real_idx = len(st.session_state.istoric_comenzi_live) - 1 - idx 
            
            if cmd['Status'] == "Asteapta Incarcare": status_color = "🔴"
            elif cmd['Status'] == "Incarcat": status_color = "🟡"
            elif cmd['Status'] == "Draft Acte": status_color = "🔵"
            else: status_color = "🟢"

            st.markdown(f"#### {status_color} Cmd NEXUS-{cmd['Comanda']} | {cmd['Client']} | Status: {cmd['Status']}")
            
            with st.expander("👁️ Vezi Comanda către Depozit (Ce scot ei fizic)"):
                st.dataframe(pd.DataFrame(cmd['Payload_Logistic']), hide_index=True)
                if 'pdf_dispozitie' in cmd and os.path.exists(cmd['pdf_dispozitie']):
                    with open(cmd['pdf_dispozitie'], "rb") as file:
                        st.download_button("📥 Descarcă Dispoziția Depozit", data=file, file_name=f"Dispozitie_{cmd['Comanda']}.pdf", mime="application/pdf", key=f"disp_dl_{real_idx}")
                
            # PASUL 1: Incarcare Fizica
            if cmd['Status'] == "Asteapta Incarcare":
                col_a, col_b = st.columns(2)
                with col_a: 
                    if st.button("✅ Confirmă Încărcarea Mărfii", key=f"inc_{real_idx}", type="primary"): 
                        st.session_state.istoric_comenzi_live[real_idx]['Status'] = "Incarcat"; st.rerun()
                with col_b:
                    if st.button("🔙 Anulează (Marfa se întoarce în Stoc)", key=f"ret_{real_idx}"):
                        if len(st.session_state.schita_comanda) > 0:
                            st.error("Golește coșul curent din Tab-ul 1 înainte de a aduce o comandă de la Rampă!")
                        else:
                            # REFUND STOC
                            for i_item in cmd['Schita_Originala']:
                                p_name = i_item['Produs']
                                P_conv = st.session_state.db[p_name]['conversion']
                                total_boxes_to_return = (i_item['Paleti'] * P_conv) + i_item['Cutii']
                                new_total = get_total_boxes(p_name) + total_boxes_to_return
                                st.session_state.db[p_name]['stock_pal'] = new_total // P_conv
                                st.session_state.db[p_name]['stock_box'] = new_total % P_conv

                            st.session_state.schita_comanda = cmd['Schita_Originala'].copy()
                            st.session_state.client_temporar_comandat = cmd['Client']
                            st.session_state.istoric_comenzi_live.pop(real_idx)
                            st.session_state.last_success_msg = "⚠️ Comanda a fost anulată. Marfa a revenit în stoc. Modifică cantitățile în Tab-ul 1."
                            st.rerun()
                        
            # PASUL 2: Generare Draft Acte Legale
            elif cmd['Status'] == "Incarcat":
                st.info("Marfa a fost confirmată fizic. Generăm documentele de ieșire legale.")
                if st.button("📝 Generează Draft Acte (Aviz & Certificat)", type="primary", key=f"draft_{real_idx}"):
                    pdf_a = generate_pdf_aviz(cmd['Comanda'], cmd['Client'], cmd['Payload_Fiscal'])
                    pdf_c = generate_pdf_certificat(cmd['Comanda'], cmd['Client'], cmd['Payload_Fiscal'])
                    st.session_state.istoric_comenzi_live[real_idx]['Status'] = "Draft Acte"
                    st.session_state.istoric_comenzi_live[real_idx]['pdf_aviz'] = pdf_a
                    st.session_state.istoric_comenzi_live[real_idx]['pdf_certificat'] = pdf_c
                    st.rerun()
                    
            # PASUL 3: Validare si SEND
            elif cmd['Status'] == "Draft Acte":
                st.markdown("##### 📄 Documente Pregătite (Verificare Ochiometrică):")
                c_d1, c_d2 = st.columns(2)
                with c_d1:
                    with open(cmd['pdf_aviz'], "rb") as file: 
                        st.download_button("📄 Vizualizare Aviz", data=file, file_name=f"Aviz_{cmd['Comanda']}.pdf", mime="application/pdf", key=f"dl_a_{real_idx}")
                with c_d2:
                    with open(cmd['pdf_certificat'], "rb") as file: 
                        st.download_button("🏅 Vizualizare Certificat Conf.", data=file, file_name=f"Certificat_{cmd['Comanda']}.pdf", mime="application/pdf", key=f"dl_c_{real_idx}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.warning("⚠️ Odată apăsat SEND, Avizul pleacă la SmartBill și actele către Depozit/Arhivă.")
                if st.button("🚀 SEND (Aprobă & Distribuie)", type="primary", key=f"send_{real_idx}", use_container_width=True):
                    st.session_state.istoric_comenzi_live[real_idx]['Status'] = "Trimis Finalizat"
                    st.rerun()

            # PASUL 4: GATA
            elif cmd['Status'] == "Trimis Finalizat":
                st.success("✅ Acte emise fizic (Depozit) & Date trimise la SmartBill (e-Factura) cu succes.")
                
            st.divider()

    # ==========================================
    # --- TAB 3: ISTORIC & ARHIVA ---
    # ==========================================
    with tab3:
        st.markdown("### 📜 Arhivă Comenzi Finalizate")
        
        if len(st.session_state.istoric_comenzi_live) == 0:
            st.info("Nicio comandă procesată astăzi.")
        else:
            istoric_df = []
            for c in reversed(st.session_state.istoric_comenzi_live):
                istoric_df.append({
                    "Comandă": f"NEXUS-{c['Comanda']}",
                    "Client": c['Client'],
                    "Status": "✅ Gata" if c['Status'] == "Trimis Finalizat" else c['Status'],
                    "Articole": len(c['Schita_Originala'])
                })
            
            st.dataframe(pd.DataFrame(istoric_df), use_container_width=True, hide_index=True)
            
            st.divider()
            st.markdown("#### 📥 Re-Descărcare Documente (Arhivă PDF)")
            
            comenzi_cu_acte = [c for c in reversed(st.session_state.istoric_comenzi_live) if c['Status'] in ["Draft Acte", "Trimis Finalizat"]]
            
            if len(comenzi_cu_acte) == 0:
                st.warning("Nu există documente PDF generate încă în sesiune.")
            else:
                for cmd in comenzi_cu_acte:
                    with st.expander(f"📦 Cmd: NEXUS-{cmd['Comanda']} | {cmd['Client']}"):
                        col_doc1, col_doc2, col_doc3 = st.columns(3)
                        
                        if 'pdf_dispozitie' in cmd and os.path.exists(cmd['pdf_dispozitie']):
                            with open(cmd['pdf_dispozitie'], "rb") as file:
                                col_doc1.download_button("📥 Disp. Depozit", data=file, file_name=f"Dispozitie_{cmd['Comanda']}.pdf", key=f"arh_d_{cmd['Comanda']}")
                                
                        if 'pdf_aviz' in cmd and os.path.exists(cmd['pdf_aviz']):
                            with open(cmd['pdf_aviz'], "rb") as file:
                                col_doc2.download_button("📥 Aviz", data=file, file_name=f"Aviz_{cmd['Comanda']}.pdf", key=f"arh_a_{cmd['Comanda']}")
                                
                        if 'pdf_certificat' in cmd and os.path.exists(cmd['pdf_certificat']):
                            with open(cmd['pdf_certificat'], "rb") as file:
                                col_doc3.download_button("📥 Certificat Conf.", data=file, file_name=f"Certificat_{cmd['Comanda']}.pdf", key=f"arh_c_{cmd['Comanda']}")
