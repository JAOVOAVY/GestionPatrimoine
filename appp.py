import streamlit as st
import pandas as pd
import os

# Configuration de la page Streamlit (Impérativement en premier)
st.set_page_config(page_title="Gestion de Patrimoine", layout="wide")

# --- GESTION DYNAMIQUE DES CHEMINS ---
base_dir = os.getcwd()
current_file_path = os.path.join(base_dir, "patrimoine.csv")
image_dir = os.path.join(base_dir, "image")
logo_path = os.path.join(base_dir, "RAMANANDRAIBE EXPORTATION S.A MAROANTSETRA.png")

# Sécurité : Création du dossier image s'il manque
if not os.path.exists(image_dir):
    os.makedirs(image_dir)

# Liste stricte des colonnes attendues
cols = ["N° Matricule (Etiquetage)", "Type", "Désignation", "Identification", "Nombre", "Localisation", "Détenteur", "Observations", "Image"]

# --- FONCTION DE CORRECTION DES EXTENSIONS D'IMAGES ---
def corriger_chemin_image(chemin_csv):
    """
    Transforme dynamiquement l'extension .jpeg du CSV en .jpg
    pour correspondre aux fichiers réels stockés sur GitHub.
    """
    if pd.isna(chemin_csv) or not isinstance(chemin_csv, str) or chemin_csv.strip() == "":
        return ""
    
    # Récupérer uniquement le nom du fichier (ex: balance de precision TZ.jpeg)
    nom_fichier = os.path.basename(chemin_csv).strip()
    
    # Remplacement de l'extension pour correspondre aux fichiers .jpg physiques
    if nom_fichier.lower().endswith(".jpeg"):
        nom_fichier = nom_fichier[:-5] + ".jpg"
    elif nom_fichier.lower().endswith(".png"):
        nom_fichier = nom_fichier[:-4] + ".jpg"
        
    return f"image/{nom_fichier}"

# --- CHARGEMENT ET NETTOYAGE DES DONNÉES ---
@st.cache_data
def charger_donnees():
    if os.path.exists(current_file_path):
        try:
            # Lecture brute avec le séparateur point-virgule
            df = pd.read_csv(current_file_path, sep=";", encoding="latin-1")
            
            # Suppression radicale des colonnes fantômes générées par Excel (, ,)
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Nettoyage des espaces blancs dans les en-têtes
            df.columns = df.columns.str.strip()
            
            # Vérification et injection des colonnes manquantes si nécessaire
            for col in cols:
                if col not in df.columns:
                    df[col] = ""
            
            # Application de l'ordre strict des colonnes
            df = df[cols]
            return df
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier CSV : {e}")
            return pd.DataFrame(columns=cols)
    else:
        return pd.DataFrame(columns=cols)

# Initialisation des états de session Streamlit
if "data_df" not in st.session_state:
    st.session_state.data_df = charger_donnees()

if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

# --- FONCTION DE SAUVEGARDE ---
def sauvegarder():
    try:
        # Exportation propre sans les index et au format attendu
        st.session_state.data_df.to_csv(current_file_path, sep=";", index=False, encoding="latin-1")
        st.success("💾 Modifications enregistrées dans `patrimoine.csv` !")
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")

# --- INTERFACE GRAPHIQUE ---
col_logo, col_titre = st.columns([0.15, 0.85])

with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.warning("⚠️ Logo absent")

with col_titre:
    st.title("📦 Gestion de Patrimoine - Version Web Interactive")
    st.subheader("RAMANANDRAIBE EXPORTATION SA Maroantsetra")

st.markdown("---")

# --- TABLEAU DE VISUALISATION ---
st.header("🔍 Consultation du Répertoire")
recherche = st.text_input("🔍 Rechercher (Désignation, Localisation, Détenteur, Matricule) :")

df_affiche = st.session_state.data_df.copy()
if recherche:
    masque = (
        df_affiche["Désignation"].astype(str).str.contains(recherche, case=False, na=False) |
        df_affiche["Localisation"].astype(str).str.contains(recherche, case=False, na=False) |
        df_affiche["Détenteur"].astype(str).str.contains(recherche, case=False, na=False) |
        df_affiche["N° Matricule (Etiquetage)"].astype(str).str.contains(recherche, case=False, na=False)
    )
    df_affiche = df_affiche[masque]

event = st.dataframe(
    df_affiche,
    use_container_width=True,
    hide_index=False,
    on_select="rerun",
    selection_mode="single-row"
)

# Gestion de la sélection de ligne
if event and "rows" in event.selection and len(event.selection["rows"]) > 0:
    index_affiche = event.selection["rows"][0]
    index_global = df_affiche.index[index_affiche]
    st.session_state.selected_index = index_global
    
    for col in cols:
        st.session_state[f"input_{col}"] = st.session_state.data_df.at[index_global, col]
else:
    if st.session_state.selected_index is not None:
        st.session_state.selected_index = None
        for col in cols:
            if f"input_{col}" in st.session_state:
                st.session_state[f"input_{col}"] = ""

st.markdown("---")

# --- FORMULAIRE ET APERÇU PHOTO ---
st.header("📝 Fiche de Détail et Modifications")
col_form, col_img_preview = st.columns([0.6, 0.4])

with col_form:
    st.write("### Informations sur l'actif")
    form_data = {}
    
    for col in cols:
        if col != "Image":
            valeur_defaut = str(st.session_state.get(f"input_{col}", ""))
            if col == "Nombre":
                try:
                    valeur_defaut = int(float(valeur_defaut)) if valeur_defaut.strip() != "" else 1
                except:
                    valeur_defaut = 1
                form_data[col] = st.number_input(f"{col} :", value=valeur_defaut, step=1)
            else:
                form_data[col] = st.text_input(f"{col} :", value=valeur_defaut)

    # Champ Image
    chemin_image_actuel = str(st.session_state.get("input_Image", ""))
    form_data["Image"] = st.text_input("Chemin de l'image (CSV) :", value=chemin_image_actuel)
    
    uploaded_file = st.file_uploader("🖼️ Remplacer la photo :", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        nouveau_chemin_local = os.path.join(image_dir, uploaded_file.name)
        with open(nouveau_chemin_local, "wb") as f:
            f.write(uploaded_file.getbuffer())
        form_data["Image"] = f"image/{uploaded_file.name}"
        st.info(f"✨ Nouvelle image prête : `image/{uploaded_file.name}`")

with col_img_preview:
    st.write("### 🖼️ Aperçu Visuel")
    if st.session_state.selected_index is not None:
        img_path_brut = st.session_state.data_df.at[st.session_state.selected_index, "Image"]
        img_path_relatif = corriger_chemin_image(img_path_brut)
        
        if img_path_relatif and os.path.exists(img_path_relatif):
            st.image(img_path_relatif, caption=f"Matricule : {form_data['N° Matricule (Etiquetage)']}", use_container_width=True)
        elif img_path_relatif:
            st.error(f"⚠️ Fiche trouvée mais image manquante sur GitHub.")
            st.info(f"Nom de fichier recherché : `{img_path_relatif}`")
        else:
            st.warning("⚠️ Aucun lien d'image.")
    else:
        st.info("💡 Sélectionnez un actif dans le tableau ci-dessus pour charger sa photo.")

# --- BOUTONS D'ACTIONS ---
st.markdown("### Actions")
col_b1, col_b2, col_b3 = st.columns(3)

with col_b1:
    if st.button("➕ Ajouter comme nouvel actif", use_container_width=True):
        if form_data["N° Matricule (Etiquetage)"].strip() == "":
            st.error("N° Matricule requis.")
        else:
            nouvelle_ligne = pd.DataFrame([form_data])
            st.session_state.data_df = pd.concat([st.session_state.data_df, nouvelle_ligne], ignore_index=True)
            sauvegarder()
            st.rerun()

with col_b2:
    if st.button("💾 Mettre à jour la sélection", use_container_width=True):
        if st.session_state.selected_index is not None:
            for col in cols:
                st.session_state.data_df.at[st.session_state.selected_index, col] = form_data[col]
            sauvegarder()
            st.rerun()

with col_b3:
    if st.button("❌ Supprimer la sélection", use_container_width=True):
        if st.session_state.selected_index is not None:
            st.session_state.data_df = st.session_state.data_df.drop(st.session_state.selected_index).reset_index(drop=True)
            st.session_state.selected_index = None
            for col in cols:
                st.session_state[f"input_{col}"] = ""
            sauvegarder()
            st.rerun()