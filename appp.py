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

# Liste stricte des colonnes requises dans l'application
cols = ["N° Matricule (Etiquetage)", "Type", "Désignation", "Identification", "Nombre", "Localisation", "Détenteur", "Observations", "Image"]

# --- FONCTION DE RECHERCHE D'IMAGES FLOUE ---
def normaliser_nom(texte):
    """ Enlève les accents, majuscules, espaces et gère les i/y """
    if not isinstance(texte, str):
        return ""
    # CORRECTION : Utilisation directe sans le paramètre 'text='
    texte = unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode('utf-8')
    return texte.lower().replace(" ", "").replace("_", "").replace("-", "").replace("y", "i")

def corriger_chemin_image(chemin_csv):
    """ Trouve l'image physique dans le dossier même si le nom diffère légèrement """
    if pd.isna(chemin_csv) or not isinstance(chemin_csv, str) or chemin_csv.strip() == "":
        return ""
    
    nom_recherche = os.path.basename(chemin_csv).strip()
    nom_recherche_sans_ext = os.path.splitext(nom_recherche)[0]
    nom_recherche_normalise = normaliser_nom(nom_recherche_sans_ext)
    
    if os.path.exists(image_dir):
        fichiers_reels = os.listdir(image_dir)
        for fichier in fichiers_reels:
            if normaliser_nom(os.path.splitext(fichier)[0]) == nom_recherche_normalise:
                return f"image/{fichier}"
        for fichier in fichiers_reels:
            fichier_sans_ext_norm = normaliser_nom(os.path.splitext(fichier)[0])
            if nom_recherche_normalise in fichier_sans_ext_norm or fichier_sans_ext_norm in nom_recherche_normalise:
                return f"image/{fichier}"

    if nom_recherche.lower().endswith(".jpeg"):
        nom_recherche = nom_recherche[:-5] + ".jpg"
    return f"image/{nom_recherche}"

# --- CHARGEMENT ET NETTOYAGE CHIRURGICAL DU CSV ---
@st.cache_data
def charger_donnees():
    if os.path.exists(current_file_path):
        try:
            # Lecture brute du CSV avec séparateur point-virgule
            df = pd.read_csv(current_file_path, sep=";", encoding="latin-1", on_bad_lines='skip')
            
            # NETTOYAGE 1 : Nettoyer les en-têtes corrompus par Excel (ex: "Image,," -> "Image")
            df.columns = df.columns.astype(str).str.strip().str.rstrip(',')
            
            # Éliminer les colonnes fantômes sans nom
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # NETTOYAGE 2 : Nettoyer chaque case des virgules de fin de ligne
            for col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.rstrip(',')
                df[col] = df[col].replace("nan", "").replace("None", "")
            
            # NETTOYAGE 3 : S'assurer que toutes les colonnes requises existent obligatoirement
            for col in cols:
                if col not in df.columns:
                    df[col] = ""
            
            return df[cols]
        except Exception as e:
            st.error(f"Erreur lors de l'analyse du fichier CSV : {e}")
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

# Initialisation des sessions Streamlit
if "data_df" not in st.session_state:
    st.session_state.data_df = charger_donnees()

if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

def sauvegarder():
    try:
        st.session_state.data_df.to_csv(current_file_path, sep=";", index=False, encoding="latin-1")
        st.success("💾 Modifications sauvegardées !")
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
recherche = st.text_input("🔍 Filtrer par mot-clé (Matricule, Désignation, Localisation...) :")

df_affiche = st.session_state.data_df.copy()
if recherche:
    masque = (
        df_affiche["Désignation"].str.contains(recherche, case=False, na=False) |
        df_affiche["Localisation"].str.contains(recherche, case=False, na=False) |
        df_affiche["Détenteur"].str.contains(recherche, case=False, na=False) |
        df_affiche["N° Matricule (Etiquetage)"].str.contains(recherche, case=False, na=False)
    )
    df_affiche = df_affiche[masque]

# Affichage du tableau propre
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

# --- FORMULAIRE ET APERÇU PHOTO ---
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
    
    uploaded_file = st.file_uploader("🖼️ Remplacer la photo :", type=["png", "jpg", "jpeg"])
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
            st.info(f"Fichier recherché : `{img_path_relatif}`")
        else:
            st.warning("⚠️ Aucun lien de photo associé.")
    else:
        st.info("💡 Sélectionnez une ligne pour charger sa fiche complète.")

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
    if st.button("💾 Mettre à jour la sélection", use_container_width=True):
        if st.session_state.selected_index is not None:
            for col in cols:
                st.session_state.data_df.at[st.session_state.selected_index, col] = form_data[col]
            sauvegarder()
            st.rerun()