import pandas as pd

# Date Furnizor
furnizor_data = {
    "Nume": "NOVA SAFE SRL", "RegCom": "J2015015825407", "CIF": "RO35368260",
    "Adresa": "Str. Turturelelor 11B, Bucuresti", "Banca": "Banca Transilvania", "IBAN": "RO72BTRLRONCRT0363372001"
}

# Date Clienți & Fiscale
clients_data = {
    "S.C. SIDE GRUP S.R.L.": {"RegCom": "J2003000200023", "CIF": "RO15216895", "Adresa": "Felnac, Nr.1000, judet Arad"},
    "DSCM TECH SRL": {"RegCom": "J17/1179/2013", "CIF": "RO32278456", "Adresa": "Com T.Vladimirescu 993, Galati"}
}

# Alias-uri
client_aliases = {
    "S.C. SIDE GRUP S.R.L.": {"Prosoape Verzi Pliate": "Prosoape V verzi"},
    "DSCM TECH SRL": {"Role Albe Stergere": "Role autocut albe TAD 220m", "Saci negri mari": "Saci menaj 120L negri LDPE"}
}

# Inițializare Database Gestiune WMS (Pentru st.session_state)
def init_db():
    return {
        "Prosoape V verzi": {
            "cod_nir": "NIR-209520", "oracle_pal": "PAL NV710", "oracle_box": "NV710", 
            "stock_pal": 4, "stock_box": 15, "conversion": 32, "um_baza": "Pachete", "conversie_baza": 20,
            "livrari_totale": pd.DataFrame({"Client": ["S.C. SIDE GRUP S.R.L."], "Data": ["10-01-2024"], "Volum_Paleti": [2], "Status_Plata": ["Achitat"]})
        },
        "Role autocut albe TAD 220m": {
            "cod_nir": "NIR-156350", "oracle_pal": "PAL BKTp721", "oracle_box": "BKTp721", 
            "stock_pal": 4, "stock_box": 32, "conversion": 48, "um_baza": "Role", "conversie_baza": 6,
            "livrari_totale": pd.DataFrame({"Client": ["DSCM TECH SRL"], "Data": ["15-01-2024"], "Volum_Paleti": [4], "Status_Plata": ["Achitat"]})
        },
        "Saci menaj 120L negri LDPE": {
            "cod_nir": "NIR-211125", "oracle_pal": "PAL IVFLX120LD-N", "oracle_box": "IVFLX120LD-N", 
            "stock_pal": 5, "stock_box": 20, "conversion": 60, "um_baza": "Role", "conversie_baza": 15,
            "livrari_totale": pd.DataFrame({"Client": ["DSCM TECH SRL"], "Data": ["12-02-2024"], "Volum_Paleti": [1], "Status_Plata": ["În termen"]})
        }
    }
