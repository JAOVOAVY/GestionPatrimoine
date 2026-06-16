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

# --- FONCTION DE NORMALISATION ET RECHERCHE FLOUE AVANCÉE ---
def normaliser_nom(texte):
    """ Enlève les accents, majuscules, espaces, doubles lettres et gère les i/y """
    if not isinstance(texte, str):
        return ""
    
    corrections = {
        "Ã©": "e", "Ã¨": "e", "Ãª": "e", "Ã«": "e", "é": "e", "è": "e", "ê": "e", "ë": "e",
        "Ã ": "a", "Ã¢": "a", "à": "a", "â": "a",
        "Ã´": "o", "ô": "o", "ö": "o",
        "Ã¹": "u", "û": "u", "ù": "u",
        "Ã§": "c", "ç": "c",
    }
    
    texte_nettoye = texte.lower()
    for corrompu, correct in corrections.items():
        texte_nettoye = texte_nettoye.replace(corrompu, correct)
        
    texte_nettoye = unicodedata.normalize('NFD', texte_nettoye).encode('ascii', 'ignore').decode('utf-8')
    return texte_nettoye.lower().replace(" ", "").replace("_", "").replace("-", "").replace("y", "i").replace("mm", "m")

def calculer_similarite(s1, s2):
    """ Calcule un score de proximité simple entre deux chaînes """
    set1, set2 = set(s1), set(s2)
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union) if union else 0

def corriger_chemin_image(chemin_csv):
    """ Trouve l'image physique sur GitHub même s'il y a des fautes d'orthographe """
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
        
        meilleur_score = 0
        meilleur_fichier = None
        for fichier in fichiers_reels:
            fichier_sans_ext_norm = normaliser_nom(os.path.splitext(fichier)[0])
            score = calculer_similarite(nom_recherche_normalise, fichier_sans_ext_norm)
            if score > meilleur_score and score > 0.70:
                meilleur_score = score
                meilleur_fichier = fichier
                
        if meilleur_fichier:
            return f"image/{meilleur_fichier}"

    if nom_recherche.lower().endswith(".jpeg"):
        nom_recherche = nom_recherche[:-5] + ".jpg"
    return f"image/{nom_recherche}"

# --- CHARGEMENT ET RECONSTRUCTION STRICTE DU TABLEAU ---
@st.cache_data
def charger_donnees():
    if os.path.exists(current_file_path):
        try:
            df = pd.read_csv(current_file_path, sep=";", encoding="latin-1", on_bad_lines='skip')
            
            if df.shape[1] >= len(cols):
                nouvelles_colonnes = list(df.columns)
                for i in range(len(cols)):
                    nouvelles_colonnes[i] = cols[i]
                df.columns = nouvelles_colonnes
            else:
                df.columns = df.columns.astype(str).str.strip().str.rstrip(',')
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                for col in cols:
                    if col not in df.columns:
                        df[col] = ""
            
            for col in cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip().str.rstrip(',')
                    df[col] = df[col].replace("nan", "").replace("None", "")
                else:
                    df[col] = ""
            
            return df[cols]
        except Exception as e:
            st.error(f"Erreur lors de la reconstruction du tableau : {e}")
            return pd.DataFrame(columns=cols)
    return pd.DataFrame(columns=cols)

if "data_df" not in st.session_state:
    st.session_state.data_df = charger_donnees()

if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

def sauvegarder():
    try:
        st.session_state.data_df.to_csv(current_file_path, sep=";", index=False, encoding="latin-1")
        st.success("💾 Modifications sauvegardées avec succès !")
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

st.header("🔍 Consultation & Filtres")

# --- ESPACE FILTRES ---
col_search, col_type, col_loc = st.columns([0.5, 0.25, 0.25])

with col_search:
    recherche = st.text_input("🔍 Recherche par mot-clé (Désignation, Matricule...) :", value="")

with col_type:
    # CORRECTION ICI : Conversion forcée str(t) pour éviter le bug AttributeError
    options_type = [str(t).strip() for t in st.session_state.data_df["Type"].unique() if pd.notna(t) and str(t).strip() != ""]
    liste_types = ["Tous"] + sorted(list(set(options_type)))
    filtre_type = st.selectbox("📁 Filtrer par Type :", options=liste_types)

with col_loc:
    # CORRECTION ICI : Conversion forcée str(l) pour éviter le bug AttributeError
    options_loc = [str(l).strip() for l in st.session_state.data_df["Localisation"].unique() if pd.notna(l) and str(l).strip() != ""]
    liste_locs = ["Tous"] + sorted(list(set(options_loc)))
    filtre_localisation = st.selectbox("📍 Filtrer par Localisation :", options=liste_locs)

# Application des filtres sur la copie du DataFrame
df_affiche = st.session_state.data_df.copy()

# 1. Filtre par défaut (Mot-clé)
if recherche:
    masque_recherche = (
        df_affiche["Désignation"].str.contains(recherche, case=False, na=False) |
        df_affiche["Détenteur"].str.contains(recherche, case=False, na=False) |
        df_affiche["N° Matricule (Etiquetage)"].str.contains(recherche, case=False, na=False) |
        df_affiche["Identification"].str.contains(recherche, case=False, na=False)
    )
    df_affiche = df_affiche[masque_recherche]

# 2. Application du filtre 'Type'
if filtre_type != "Tous":
    df_affiche = df_affiche[df_affiche["Type"] == filtre_type]

# 3. Application du filtre 'Localisation'
if filtre_localisation != "Tous":
    df_affiche = df_affiche[df_affiche["Localisation"] == filtre_localisation]

# Affichage du tableau filtré
event = st.dataframe(df_affiche, use_container_width=True, hide_index=False, on_select="rerun", selection_mode="single-row")

if event and "rows" in event.selection and len(event.selection["rows"]) > 0:
    index_affiche = event.selection["rows"][0]
    st.session_state.selected_index = df_affiche.index[index_affiche]
    
    for col in cols:
        valeur_cellule = str(st.session_state.data_df.at[st.session_state.selected_index, col])
        st.session_state[f"input_{col}"] = valeur_cellule
else:
    if st.session_state.selected_index is not None:
        st.session_state.selected_index = None
        for col in cols:
            st.session_state[f"input_{col}"] = ""

st.markdown("---")

# --- FORMULAIRE D'ÉDITION ET APERÇU PHOTO ---
st.header("📝 Fiche de Détail")
col_form, col_img_preview = st.columns([0.6, 0.4])

with col_form:
    form_data = {}
    for col in cols:
        if col != "Image":
            valeur_defaut = str(st.session_state.get(f"input_{col}", ""))
            form_data[col] = st.text_input(f"{col} :", value=valeur_defaut, key=f"widget_{col}")
    
    chemin_image_actuel = str(st.session_state.get("input_Image", ""))
    form_data["Image"] = st.text_input("Chemin de l'image (CSV) :", value=chemin_image_actuel, key="widget_Image")
    
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