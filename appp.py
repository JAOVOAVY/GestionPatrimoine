import streamlit as st
import pandas as pd
import os
import csv

# Configuration de la page Streamlit (Doit obligatoirement être la première commande)
st.set_page_config(page_title="Gestion de Patrimoine", layout="wide")

# --- GESTION DYNAMIQUE DES CHEMINS (LOCAL ET WEB) ---
base_dir = os.getcwd()
current_file_path = os.path.join(base_dir, "patrimoine.csv")
image_dir = os.path.join(base_dir, "image")
logo_path = os.path.join(base_dir, "RAMANANDRAIBE EXPORTATION S.A MAROANTSETRA.png")

# Sécurité : Créer le dossier image s'il n'existe pas
if not os.path.exists(image_dir):
    os.makedirs(image_dir)

# Liste exacte et ordonnée des colonnes requises par l'application
cols = ["N° Matricule (Etiquetage)", "Type", "Désignation", "Identification", "Nombre", "Localisation", "Détenteur", "Observations", "Image"]

# --- FONCTION DE CORRECTION ET DE CONVERSION DES IMAGES ---
def corriger_chemin_image(chemin_csv):
    """
    Nettoie le chemin du CSV et force l'extension en .jpg 
    pour correspondre aux fichiers réels du dossier image.
    """
    if pd.isna(chemin_csv) or not isinstance(chemin_csv, str) or chemin_csv.strip() == "":
        return ""
    
    # Extraction du nom brut du fichier (ex: balance de precision TZ.jpeg -> balance de precision TZ.jpeg)
    nom_fichier = os.path.basename(chemin_csv)
    
    # Remplacement de l'extension pour correspondre aux fichiers .jpg réels du dossier image
    if nom_fichier.lower().endswith(".jpeg"):
        nom_fichier = nom_fichier[:-5] + ".jpg"
    elif nom_fichier.lower().endswith(".png"):
        nom_fichier = nom_fichier[:-4] + ".jpg"
        
    return f"image/{nom_fichier}"

# --- CHARGEMENT ET NETTOYAGE SÉCURISÉ DES DONNÉES ---
@st.cache_data
def charger_donnees():
    if os.path.exists(current_file_path):
        try:
            # Lecture du fichier CSV avec l'encodage 'latin-1'
            df = pd.read_csv(current_file_path, sep=";", encoding="latin-1")
            
            # Nettoyage des colonnes fantômes générées par Excel
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            
            # Nettoyage des espaces cachés dans les en-têtes
            df.columns = df.columns.str.strip()
            
            # Sécurité anti-KeyError
            for col in cols:
                if col not in df.columns:
                    df[col] = ""
            
            df = df[cols]
            return df
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier CSV : {e}")
            return pd.DataFrame(columns=cols)
    else:
        return pd.DataFrame(columns=cols)

# Initialisation des variables de session Streamlit
if "data_df" not in st.session_state:
    st.session_state.data_df = charger_donnees()

if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

# --- FONCTION DE SAUVEGARDE ---
def sauvegarder():
    try:
        st.session_state.data_df.to_csv(current_file_path, sep=";", index=False, encoding="latin-1")
        st.success("💾 Modifications enregistrées avec succès dans `patrimoine.csv` !")
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")

# --- INTERFACE GRAPHIQUE : EN-TÊTE ---
col_logo, col_titre = st.columns([0.15, 0.85])

with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.warning("⚠️ Logo introuvable")

with col_titre:
    st.title("📦 Gestion de Patrimoine - Version Web Interactive")
    st.subheader("RAMANANDRAIBE EXPORTATION SA Maroantsetra")

st.markdown("---")

# --- SECTION DE RECHERCHE ET AFFICHAGE TABLEAU ---
st.header("🔍 Consultation du Répertoire")

recherche = st.text_input("🔍 Rechercher un matériel (Désignation, Localisation, Détenteur, Matricule) :")

# Filtrage dynamique des données selon la recherche
df_affiche = st.session_state.data_df.copy()
if recherche:
    masque = (
        df_affiche["Désignation"].astype(str).str.contains(recherche, case=False, na=False) |
        df_affiche["Localisation"].astype(str).str.contains(recherche, case=False, na=False) |
        df_affiche["Détenteur"].astype(str).str.contains(recherche, case=False, na=False) |
        df_affiche["N° Matricule (Etiquetage)"].astype(str).str.contains(recherche, case=False, na=False)
    )
    df_affiche = df_affiche[masque]

st.write("### Liste des actifs :")
event = st.dataframe(
    df_affiche,
    use_container_width=True,
    hide_index=False,
    on_select="rerun",
    selection_mode="single-row"
)

# Traitement de la sélection d'une ligne dans le tableau
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

# --- FORMULAIRE D'ÉDITION ET APERÇU ---
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

    # Zone de gestion de l'image
    chemin_image_actuel = str(st.session_state.get("input_Image", ""))
    form_data["Image"] = st.text_input("Chemin de l'image (ex: image/moniteur.jpeg) :", value=chemin_image_actuel)
    
    uploaded_file = st.file_uploader("🖼️ Remplacer l'image en téléchargeant un fichier :", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        nouveau_chemin_local = os.path.join(image_dir, uploaded_file.name)
        with open(nouveau_chemin_local, "wb") as f:
            f.write(uploaded_file.getbuffer())
        form_data["Image"] = f"image/{uploaded_file.name}"
        st.info(f"✨ Image enregistrée : `image/{uploaded_file.name}`")

with col_img_preview:
    st.write("### 🖼️ Aperçu Visuel")
    if st.session_state.selected_index is not None:
        # On récupère le chemin brut du CSV
        img_path_brut = st.session_state.data_df.at[st.session_state.selected_index, "Image"]
        # On applique la transformation intelligente (.jpeg -> .jpg)
        img_path_relatif = corriger_chemin_image(img_path_brut)
        
        if img_path_relatif:
            try:
                st.image(img_path_relatif, caption=f"Matricule : {form_data['N° Matricule (Etiquetage)']}", use_container_width=True)
            except Exception as e:
                st.error("⚠️ Image introuvable ou extension incorrecte.")
                st.info(f"Fichier recherché sur GitHub : `{img_path_relatif}`")
        else:
            st.warning("⚠️ Aucun chemin d'image renseigné pour cet actif.")
    else:
        st.info("💡 Sélectionnez une ligne dans le tableau pour afficher sa photo et ses informations.")

# --- BARRE DE BOUTONS D'ACTION ---
st.markdown("### Actions disponibles")
col_b1, col_b2, col_b3, col_b4 = st.columns(4)

with col_b1:
    if st.button("➕ Ajouter comme nouvel actif", use_container_width=True):
        if form_data["N° Matricule (Etiquetage)"].strip() == "":
            st.error("Le N° Matricule est obligatoire pour ajouter un nouvel actif.")
        else:
            nouvelle_ligne = pd.DataFrame([form_data])
            st.session_state.data_df = pd.concat([st.session_state.data_df, nouvelle_ligne], ignore_index=True)
            sauvegarder()
            st.rerun()

with col_b2:
    if st.button("💾 Mettre à jour l'actif sélectionné", use_container_width=True):
        if st.session_state.selected_index is not None:
            for col in cols:
                st.session_state.data_df.at[st.session_state.selected_index, col] = form_data[col]
            sauvegarder()
            st.rerun()
        else:
            st.error("Sélectionnez d'abord un actif dans le tableau.")

with col_b3:
    if st.button("❌ Supprimer l'actif sélectionné", use_container_width=True):
        if st.session_state.selected_index is not None:
            st.session_state.data_df = st.session_state.data_df.drop(st.session_state.selected_index).reset_index(drop=True)
            st.session_state.selected_index = None
            for col in cols:
                st.session_state[f"input_{col}"] = ""
            sauvegarder()
            st.rerun()
        else:
            st.error("Sélectionnez d'abord un actif à supprimer.")

with col_b4:
    if st.button("🖨️ Imprimer la fiche (Texte)", use_container_width=True):
        if st.session_state.selected_index is not None:
            print_path = os.path.join(base_dir, "impression_patrimoine.txt")
            try:
                with open(print_path, "w", encoding="utf-8") as f:
                    f.write("=========================================\n")
                    f.write("       FICHE DE COMPTABILISATION        \n")
                    f.write("=========================================\n\n")
                    for col in cols:
                        f.write(f"{col} : {st.session_state.data_df.at[st.session_state.selected_index, col]}\n")
                    f.write("\n=========================================\n")
                st.success(f"🖨️ Fiche créée avec succès sous : `{print_path}`")
            except Exception as e:
                st.error(f"Erreur d'impression : {e}")
        else:
            st.error("Sélectionnez un actif à imprimer.")