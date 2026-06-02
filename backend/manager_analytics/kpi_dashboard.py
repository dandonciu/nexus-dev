import streamlit as st
import pandas as pd
import plotly.express as px
import math

def force_inject_mock_data():
    # OPȚIUNEA NUCLEARĂ: Suprascriem forțat baza de date ca să ucidem memoria veche
    st.session_state.db = {
        "Role Autocut Albe TAD 220m": {
            "cod_master": "MST-BKTp721", "oracle_pal": "PAL BKTp721", "oracle_box": "BKTp721",
            "stock_pal": 3, "stock_box": 0, "conversion": 64,
            "descriere": "Role din celuloză pură 100%, 2 straturi.",
            "livrari_totale": pd.DataFrame({
                "Client": [
                    "🏢 [HQ] SC CORPORATIA ALPHA SRL", " ├─ Filiala București Nord", " ├─ Filiala Cluj", "🏢 [HQ] BETA DISTRIBUTION",
                    "🏢 [HQ] SC CORPORATIA ALPHA SRL", " ├─ Filiala București Nord", " ├─ Filiala Cluj", "🏢 [HQ] BETA DISTRIBUTION",
                    "🏢 [HQ] SC CORPORATIA ALPHA SRL", " ├─ Filiala București Nord", " ├─ Filiala Cluj", "🏢 [HQ] BETA DISTRIBUTION",
                    "🏢 [HQ] SC CORPORATIA ALPHA SRL", " ├─ Filiala București Nord", " ├─ Filiala Cluj", "🏢 [HQ] BETA DISTRIBUTION"
                ],
                "Data": [
                    "10-01-2024", "12-01-2024", "05-01-2024", "08-01-2024",
                    "15-02-2024", "18-02-2024", "10-02-2024", "20-02-2024",
                    "05-03-2024", "10-03-2024", "15-03-2024", "22-03-2024",
                    "02-04-2024", "10-04-2024", "12-04-2024", "18-04-2024"
                ],
                "Volum_Paleti": [12, 5, 4, 20, 15, 8, 6, 25, 10, 4, 8, 18, 22, 6, 12, 30],
                "Status_Plata": ["Achitat", "Achitat", "Achitat", "Achitat", "Achitat", "Achitat", "Restanță", "În termen", "În termen", "Restanță", "Achitat", "În termen", "În termen", "Achitat", "Achitat", "Restanță"]
            })
        },
        "Lavete Craft Puromore Blue": {
            "cod_master": "MST-70117", "oracle_pal": "PAL 70117", "oracle_box": "70117",
            "stock_pal": 1, "stock_box": 10, "conversion": 120,
            "descriere": "Lavete industriale rezistente la solvenți, culoare albastră.",
            "livrari_totale": pd.DataFrame({
                "Client": [
                    "🏢 [HQ] SC CORPORATIA ALPHA SRL", " ├─ Filiala București Nord", " ├─ Filiala Cluj", "🏢 [HQ] BETA DISTRIBUTION",
                    "🏢 [HQ] SC CORPORATIA ALPHA SRL", " ├─ Filiala București Nord", " ├─ Filiala Cluj", "🏢 [HQ] BETA DISTRIBUTION"
                ],
                "Data": [
                    "05-01-2024", "20-01-2024", "15-01-2024", "10-01-2024",
                    "12-02-2024", "25-02-2024", "28-02-2024", "20-02-2024"
                ],
                "Volum_Paleti": [5, 2, 8, 15, 8, 4, 6, 20],
                "Status_Plata": ["Restanță", "Achitat", "În termen", "Achitat", "Achitat", "Achitat", "Restanță", "În termen"]
            })
        }
    }
    
    if 'istoric_comenzi_live' not in st.session_state:
        st.session_state.istoric_comenzi_live = []

    return ["🏢 [HQ] SC CORPORATIA ALPHA SRL", " ├─ Filiala București Nord", " ├─ Filiala Cluj", "🏢 [HQ] BETA DISTRIBUTION"]

def render_manager_dashboard():
    clients_mock = force_inject_mock_data()
    
    st.title("📈 NEXUS Dashboard Manager")
    
    tab_op, tab_an = st.tabs(["⚡ A. Situație Operativă", "📊 B. Privire de Ansamblu (Analiză)"])
    
    with tab_op:
        st.subheader("1. Indicatori Rapizi (Azi)")
        c_k1, c_k2, c_k3 = st.columns(3)
        c_k1.success("Livrări în grafic: 4")
        c_k2.warning("Recepții în așteptare: 1")
        c_k3.error("Facturi restante: 2")
        
        st.divider()
        st.subheader("🔴 LIVE FEED: Comenzi Noi")
        if len(st.session_state.istoric_comenzi_live) > 0:
            df_live = pd.DataFrame(st.session_state.istoric_comenzi_live)
            st.dataframe(df_live, use_container_width=True, hide_index=True)
        else:
            st.info("Nicio comandă nouă lansată astăzi.")
            
        st.divider()
        st.subheader("2. Analiză Stoc Punctual (Reconciliere WMS)")
        mgr_prod = st.selectbox("Selectare Produs:", list(st.session_state.db.keys()))
        p_val = st.session_state.db[mgr_prod]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Paleți Intacți", p_val['stock_pal'])
        c2.metric("Cutii Libere", p_val['stock_box'])
        c3.metric("Conversie WMS", f"{p_val['conversion']} cutii/palet")
        
        total_boxes = (p_val['stock_pal'] * p_val['conversion']) + p_val['stock_box']
        billed = math.ceil(total_boxes / p_val['conversion'])
        c4.metric("Se facturează (Paleți)", f"{billed} paleți")

        if p_val['stock_box'] > (p_val['conversion'] * 0.7):
            st.error(f"🔴 ATENȚIE: Aveți prea multe cutii libere ({p_val['stock_box']}).")
        elif p_val['stock_box'] > 0:
            st.warning("🟠 INFO: Există cutii libere în depozit.")
        else:
            st.success("🟢 OPTIM: Nu aveți fracții desfăcute în depozit.")
                
    with tab_an:
        col_m1, col_m2 = st.columns([2, 2])
        with col_m1: analiza_client = st.selectbox("Selectează Client / Filială:", clients_mock)
        with col_m2: analiza_produs = st.selectbox("Selectează Produs pt. Analiză:", list(st.session_state.db.keys()), key="mgr_prod_an")
        
        st.divider()
        df_toate = st.session_state.db[analiza_produs]["livrari_totale"]
        color_discrete_map = {'Achitat': '#28a745', 'În termen': '#17a2b8', 'Restanță': '#dc3545'}
        
        df_toate['Data_Obj'] = pd.to_datetime(df_toate['Data'], format='%d-%m-%Y')
        df_toate['Luna'] = df_toate['Data_Obj'].dt.strftime('%b %Y')
        
        # 1. GRAFIC LUNI
        st.markdown(f"#### 📆 Volum Livrări pe Luni: **{analiza_produs}** (Toți Clienții)")
        df_luni = df_toate.groupby(['Luna', 'Status_Plata'])['Volum_Paleti'].sum().reset_index()
        
        fig_luni = px.bar(
            df_luni, x='Luna', y='Volum_Paleti', color='Status_Plata',
            text='Volum_Paleti', color_discrete_map=color_discrete_map,
            title="Sinteză Lunară (Bază de date Oracle)",
            barmode='group' 
        )
        fig_luni.update_layout(xaxis_type='category', xaxis_title="Lună", yaxis_title="Număr Paleți Livrați", bargap=0.3)
        fig_luni.update_traces(textposition='outside')
        st.plotly_chart(fig_luni, use_container_width=True)

        st.divider()

        # 2. GRAFIC TOP CLIENȚI
        st.markdown(f"#### 🏆 Top Clienți după Volum: **{analiza_produs}**")
        df_top = df_toate.groupby(['Client'])['Volum_Paleti'].sum().reset_index()
        df_top = df_top.sort_values(by='Volum_Paleti', ascending=False)
        
        fig_top = px.bar(
            df_top, x='Client', y='Volum_Paleti',
            text='Volum_Paleti', color='Volum_Paleti', 
            color_continuous_scale='Blues',
            title="Distribuția volumelor per client"
        )
        fig_top.update_layout(xaxis_type='category', xaxis_title="Client", yaxis_title="Volum Total (Paleți)", bargap=0.4)
        fig_top.update_traces(textposition='outside')
        st.plotly_chart(fig_top, use_container_width=True)

        st.divider()

        # 3. GRAFIC ISTORIC
        st.markdown(f"#### 🔎 Istoric Detaliat pentru: **{analiza_client}**")
        df_filtrat = df_toate[df_toate['Client'] == analiza_client]
        
        if df_filtrat.empty:
            st.warning(f"Nu există date de livrare pentru {analiza_produs} către {analiza_client}.")
        else:
            fig_detaliu = px.bar(
                df_filtrat, x='Data', y='Volum_Paleti', color='Status_Plata',
                text='Volum_Paleti', color_discrete_map=color_discrete_map,
                title="Livrări la nivel de zi (Achitat / Restanțe)"
            )
            fig_detaliu.update_layout(xaxis_type='category', xaxis_title="Dată Livrare", yaxis_title="Număr Paleți", bargap=0.3)
            fig_detaliu.update_traces(textposition='outside')
            st.plotly_chart(fig_detaliu, use_container_width=True)
