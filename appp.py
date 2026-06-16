import streamlit as st
import pandas as pd
import os
import unicodedata

# Configuration de la page Streamlit (Impérativement en premier)
st.set_page_config(page_title="Gestion de Patrimoine", layout="wide")

# --- GESTION DYNAMIQUE DES CHEMINS ---
base_dir = os.getcwd()
current_file_path = os.path.join(base_dir, "patrimoine.csv")
image_dir = os.path.join(base_dir, "image")
logo_path = os.path.join(base_dir, "RAMANANDRAIBE EXPORTATION S.A MAROANTSETRA.png")

if not os.path.exists(image_dir):
    os.makedirs(image_dir)

# Liste stricte des colonnes requises
cols = ["N° Matricule (Etiquetage)", "Type", "Désignation", "Identification", "Nombre", "Localisation", "Détenteur", "Observations", "Image"]

# --- FONCTION DE RECHERCHE D'IMAGES INTELLIGENTE ---
def normaliser_nom(texte):
    """ Enlève les accents, majuscules et espaces pour comparer les noms de fichiers """
    if not isinstance(texte, str):
        return ""
    texte = unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode('utf-8')
    return texte.lower().replace(" ", "").replace("_", "").replace("-", "").replace("y", "i")

def corriger_chemin_image(chemin_csv):
    """ Scanne le dossier réel et trouve la photo même s'il y a des fautes (i vs y, majuscules...) """
    if pd.isna(chemin_csv) or not isinstance(chemin_csv, str) or chemin_csv.strip() == "":
        return ""
    
    nom_recherche = os.path.basename(chemin_csv).strip()
    nom_recherche_sans_ext = os.path.splitext(nom_recherche)[0]
    nom_recherche_normalise = normaliser_nom(nom_recherche_sans_ext)
    
    if os.path.exists(image_dir):
        fichiers_reels = os.listdir(image_dir)
        for fichier in fichiers_reels:
            fichier_sans_ext = os.path.splitext(fichier)[0]
            if normaliser_nom(fichier_sans_ext) == nom_recherche_normalise:
                return f"image/{fichier}"
        for fichier in fichiers_reels:
            fichier_sans_ext_norm = normaliser_nom(os.path.splitext(fichier)[0])
            if nom_recherche_normalise in fichier_sans_ext_norm or fichier_sans_ext_norm in nom_recherche_normalise:
                return f"image/{fichier}"

    if nom_recherche.lower().endswith(".jpeg"):
        nom_recherche = nom_recherche[:-5] + ".jpg"
    return f"image/{nom_recherche}"

# --- CHARGEMENT ET NETTOYAGE STRICT DU CSV ---
@st.cache_data
def charger_donnees():
    if os.path.exists(current_file_path):
        try:
            # Lecture brute du fichier avec encodage adapté
            df = pd.read_csv(current_file_path, sep=";", encoding="latin-1", on_bad_lines='skip')
            
            # 1. Éliminer les colonnes fantômes d'Excel
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            df.columns = df.columns.str.strip()
            
            # 2. Nettoyage ligne par ligne de toutes les cases
            for col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                # On nettoie les résidus de doubles virgules en fin de ligne
                df[col] = df[col].str.rstrip(',')
                df[col] = df[col].replace("nan", "").replace("None", "")
            
            # 3. Sécurité d'injection si une colonne manque
            for col in cols:
                if col not in df.columns:
                    df[col] = ""
            
            return df[cols]
        except Exception as e:
            st.error(f"Erreur lors du nettoyage du fichier CSV : {e}")
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

# Initialisation des états Streamlit
if "data_df" not in st.session_state:
    st.session_state.data_df = charger_donnees()

if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

def sauvegarder():
    try:
        st.session_state.data_df.to_csv(current_file_path, sep=";", index=False, encoding="latin-1")
        st.success("💾 Fichier `patrimoine.csv` mis à jour avec succès !")
    except Exception as e:
        st.error(f"Erreur de sauvegarde : {e}")

# --- INTERFACE GRAPHIQUE ---
col_logo, col_titre = st.columns([0.15, 0.85])
with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
with col_titre:
    st.title("📦 Gestion de Patrimoine - Version Web Interactive")
    st.subheader("RAMANANDRAIBE EXPORTATION SA Maroantsetra")

st.markdown("---")

st.header("🔍 Consultation du Répertoire")
recherche = st.text_input("🔍 Filtrer la liste (Saisir un mot clé) :")

df_affiche = st.session_state.data_df.copy()
if recherche:
    masque = (
        df_affiche["Désignation"].str.contains(recherche, case=False, na=False) |
        df_affiche["Localisation"].str.contains(recherche, case=False, na=False) |
        df_affiche["Détenteur"].str.contains(recherche, case=False, na=False) |
        df_affiche["N° Matricule (Etiquetage)"].str.contains(recherche, case=False, na=False)
    )
    df_affiche = df_affiche[masque]

event = st.dataframe(df_affiche, use_container_width=True, hide_index=False, on_select="rerun", selection_mode="single-row")

if event and "rows" in event.selection and len(event.selection["rows"]) > 0:
    index_affiche = event.selection["rows"][0]
    st.session_state.selected_index = df_affiche.index[index_affiche]
    for col in cols:
        st.session_state[f"input_{col}"] = st.session_state.data_df.at[st.session_state.selected_index, col]
else:
    if st.session_state.selected_index is not None:
        st.session_state.selected_index = None
        for col in cols:
            if f"input_{col}" in st.session_state: st.session_state[f"input_{col}"] = ""

st.markdown("---")

# --- FORMULAIRE ET CONFIGURATION ---
st.header("📝 Fiche de Détail")
col_form, col_img_preview = st.columns([0.6, 0.4])

with col_form:
    form_data = {}
    for col in cols:
        if col != "Image":
            valeur_defaut = str(st.session_state.get(f"input_{col}", ""))
            form_data[col] = st.text_input(f"{col} :", value=valeur_defaut)
    
    chemin_image_actuel = str(st.session_state.get("input_Image", ""))
    form_data["Image"] = st.text_input("Chemin de l'image (CSV) :", value=chemin_image_actuel)
    
    uploaded_file = st.file_uploader("🖼️ Remplacer la photo par un fichier local :", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        nouveau_chemin_local = os.path.join(image_dir, uploaded_file.name)
        with open(nouveau_chemin_local, "wb") as f:
            f.write(uploaded_file.getbuffer())
        form_data["Image"] = f"image/{uploaded_file.name}"

with col_img_preview:
    st.write("### 🖼️ Aperçu Visuel")
    if st.session_state.selected_index is not None:
        img_path_brut = st.session_state.data_df.at[st.session_state.selected_index, "Image"]
        img_path_relatif = corriger_chemin_image(img_path_brut)
        
        if img_path_relatif and os.path.exists(img_path_relatif):
            st.image(img_path_relatif, caption=f"Matricule : {form_data['N° Matricule (Etiquetage)']}", use_container_width=True)
        elif img_path_relatif:
            st.error(f"⚠️ Image manquante sur GitHub.")
            st.info(f"Nom recherché : `{img_path_relatif}`")
        else:
            st.warning("⚠️ Aucun lien de photo associé.")
    else:
        st.info("💡 Sélectionnez un actif pour charger sa fiche complète.")

st.markdown("### Actions")
col_b1, col_b2 = st.columns(2)
with col_b1:
    if st.button("➕ Ajouter comme nouvel actif", use_container_width=True):
        if form_data["N° Matricule (Etiquetage)"].strip() == "":
            st.error("Le N° Matricule est obligatoire.")
        else:
            st.session_state.data_df = pd.concat([st.session_state.data_df, pd.DataFrame([form_data])], ignore_index=True)
            sauvegarder()
            st.rerun()
with col_b2:
    if st.button("💾 Mettre à jour l'actif sélectionné", use_container_width=True):
        if st.session_state.selected_index is not None:
            for col in cols:
                st.session_state.data_df.at[st.session_state.selected_index, col] = form_data[col]
            sauvegarder()
            st.rerun()