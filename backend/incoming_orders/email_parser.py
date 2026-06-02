import streamlit as st
import pandas as pd

def render_email_parser_module():
    st.title("📨 NEXUS Inbox")
    st.info("🤖 Botul NEXUS monitorizează adresa de email (ex: comenzi@novasafe.ro) pentru a prelua și decoda fișierele cu comenzi - Excel sau PDF - de la clienți.")
    st.info("🤖 Botul NEXUS trimite mesaje de confirmare preluare/livrare comenzi.")
    st.info("🤖 Botul NEXUS monitorizează adresa de email (ex: nova_facturi@novasafe.ro) pentru a prelua și decoda fișierele cu facturi - Excel sau PDF - de la Furnizori și a le trimite în format normalizat către SmartBill.")
    st.info("📨 Documentele se trimit spre arhivare în Vault.")
    
    st.divider()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("📬 De ex: Inbox Comenzi Necitite")
        # Un tabel de mockup (fals deocamdată) ca să vedem cum va arăta
        mock_emails = pd.DataFrame({
            "Client": ["S.C. SIDE GRUP S.R.L.", "DSCM TECH SRL", "CORPORATIA ALPHA"],
            "Subiect Email": ["Comanda ferma marfa", "Fwd: Necesar consumabile", "Comanda_Luni.xlsx"],
            "Atașament": ["📄 comanda_123.pdf", "📊 necesar.xlsx", "📊 Comanda_Luni.xlsx"],
            "Status Robot": ["🟢 Decodat cu succes", "🟡 Necesită confirmare", "🔴 Eroare format"]
        })
        st.dataframe(mock_emails, hide_index=True, use_container_width=True)
        
    with col2:
        st.markdown("### ⚙️ Comenzi Bot")
        if st.button("🔄 Scanează Inbox-ul acum", use_container_width=True, type="primary"):
            st.toast("Se conectează la serverul IMAP...", icon="⏳")
            
        if st.button("🚀 Trimite în Buffer (Lansare)", use_container_width=True):
            st.toast("Comenzile ar fi fost trimise spre WMS!", icon="✅")
