import streamlit as st
import pandas as pd
import os
import csv

# Configuration de la page Streamlit (Doit être la toute première commande Streamlit)
st.set_page_config(page_title="Gestion de Patrimoine", layout="wide")

# --- GESTION DYNAMIQUE DES CHEMINS (LOCAL ET WEB) ---
# os.getcwd() récupère automatiquement le dossier racine du projet (ex: sur GitHub ou sous Windows/WSL2)
base_dir = os.getcwd()
current_file_path = os.path.join(base_dir, "patrimoine.csv")
image_dir = os.path.join(base_dir, "image")
logo_path = os.path.join(base_dir, "RAMANANDRAIBE EXPORTATION S.A MAROANTSETRA.png")

# Créer le dossier image s'il n'existe pas encore (sécurité pour le mode web/local)
if not os.path.exists(image_dir):
    os.makedirs(image_dir)

# --- FONCTION POUR CORRIGER LES CHEMINS DU CSV EN MODE WEB ---
def corriger_chemin_image(chemin_csv):
    """
    Transforme un chemin absolu Windows/WSL (ex: /mnt/c/.../image/photo.png)
    en un chemin relatif propre (ex: image/photo.png) pour que Streamlit Cloud le trouve.
    """
    if pd.isna(chemin_csv) or not isinstance(chemin_csv, str) or chemin_csv.strip() == "":
        return ""
    
    # Si le chemin contient le mot 'image/', on extrait tout ce qui suit
    if "image/" in chemin_csv:
        nom_image = chemin_csv.split("image/")[-1]
        return os.path.join("image", nom_image)
    
    # Si c'est juste le nom du fichier
    return os.path.join("image", os.path.basename(chemin_csv))

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data
def charger_donnees():
    if os.path.exists(current_file_path):
        try:
            # Lecture du fichier CSV avec le délimiteur point-virgule
            df = pd.read_csv(current_file_path, sep=";", encoding="utf-8")
            # Nettoyage des colonnes fantômes si existantes
            df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
            return df
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier CSV : {e}")
            return pd.DataFrame(columns=cols)
    else:
        # Si le fichier n'existe pas, on initialise un DataFrame vide avec les bonnes colonnes
        return pd.DataFrame(columns=cols)

# Définition des colonnes attendues
cols = ["N° Matricule (Etiquetage)", "Type", "Désignation", "Identification", "Nombre", "Localisation", "Détenteur", "Observations", "Image"]

# Initialisation des variables d'état (Session State)
if "data_df" not in st.session_state:
    st.session_state.data_df = charger_donnees()

if "selected_index" not in st.session_state:
    st.session_state.selected_index = None

# Fonction de sauvegarde dans le fichier CSV
def sauvegarder():
    try:
        st.session_state.data_df.to_csv(current_file_path, sep=";", index=False, encoding="utf-8")
        st.success("💾 Modifications enregistrées avec succès dans `patrimoine.csv` !")
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")

# --- EN-TÊTE AVEC LOGO ET TITRE ---
col_logo, col_titre = st.columns([0.15, 0.85])

with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, use_container_width=True)
    else:
        st.warning("⚠️ Logo manquant")

with col_titre:
    st.title("📦 Gestion de Patrimoine - Version Web Interactive")
    st.subheader("RAMANANDRAIBE EXPORTATION SA Maroantsetra")

st.markdown("---")

# --- SECTION CENTRALISÉE : AFFICHAGE ET RECHERCHE ---
st.header("🔍 Consultation du Répertoire")

# Barre de recherche globale
recherche = st.text_input("🔍 Rechercher un matériel (par Désignation, Localisation, Détenteur ou N° Matricule) :")

# Filtrer le DataFrame en fonction de la saisie
df_affiche = st.session_state.data_df.copy()
if recherche:
    masque = (
        df_affiche["Désignation"].astype(str).str.contains(recherche, case=False, na=False) |
        df_affiche["Localisation"].astype(str).str.contains(recherche, case=False, na=False) |
        df_affiche["Détenteur"].astype(str).str.contains(recherche, case=False, na=False) |
        df_affiche["N° Matricule (Etiquetage)"].astype(str).str.contains(recherche, case=False, na=False)
    )
    df_affiche = df_affiche[masque]

# Affichage du tableau principal interactif
st.write("### Liste des actifs sélectionnés :")
event = st.dataframe(
    df_affiche,
    use_container_width=True,
    hide_index=False,
    on_select="rerun",
    selection_mode="single-row"
)

# Traitement de la sélection d'une ligne
if event and "rows" in event.selection and len(event.selection["rows"]) > 0:
    index_affiche = event.selection["rows"][0]
    # Retrouver l'index d'origine dans le dataframe global
    index_global = df_affiche.index[index_affiche]
    st.session_state.selected_index = index_global
    
    # Remplir les inputs automatiquement avec la ligne sélectionnée
    for col in cols:
        st.session_state[f"input_{col}"] = st.session_state.data_df.at[index_global, col]
else:
    # Si aucune ligne n'est sélectionnée, on réinitialise (sauf si on est en train de taper un nouvel élément)
    if st.session_state.selected_index is not None:
        st.session_state.selected_index = None
        for col in cols:
            if f"input_{col}" in st.session_state:
                st.session_state[f"input_{col}"] = ""

st.markdown("---")

# --- ZONE FORMULAIRE : ÉDITION / AJOUT / VISUALISATION ---
st.header("📝 Fiche de Détail et Modifications")

col_form, col_img_preview = st.columns([0.6, 0.4])

with col_form:
    st.write("### Informations de l'actif")
    
    # Formulaire d'édition dynamique
    form_data = {}
    for col in cols:
        if col != "Image":  # On traite l'image séparément
            valeur_defaut = str(st.session_state.get(f"input_{col}", ""))
            # Gestion spécifique pour le champ Nombre (doit être un entier)
            if col == "Nombre":
                try:
                    valeur_defaut = int(float(valeur_defaut)) if valeur_defaut.strip() != "" else 1
                except:
                    valeur_defaut = 1
                form_data[col] = st.number_input(f"{col} :", value=valeur_defaut, step=1)
            else:
                form_data[col] = st.text_input(f"{col} :", value=valeur_defaut)

    # Gestion de l'image (Saisie du chemin ou upload)
    chemin_image_actuel = str(st.session_state.get("input_Image", ""))
    form_data["Image"] = st.text_input("Chemin de l'image (relatif, ex: image/moniteur.png) :", value=chemin_image_actuel)
    
    uploaded_file = st.file_uploader("🖼️ Remplacer l'image en téléchargeant un fichier :", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        # Enregistrer le fichier téléversé directement dans le sous-dossier 'image'
        nouveau_chemin_local = os.path.join(image_dir, uploaded_file.name)
        with open(nouveau_chemin_local, "wb") as f:
            f.write(uploaded_file.getbuffer())
        form_data["Image"] = f"image/{uploaded_file.name}"
        st.info(f"✨ Nouvelle image stockée temporairement : `image/{uploaded_file.name}`")

with col_img_preview:
    st.write("### 🖼️ Aperçu Visuel")
    if st.session_state.selected_index is not None:
        # Récupération et correction du chemin de l'image pour le web
        img_path_brut = st.session_state.data_df.at[st.session_state.selected_index, "Image"]
        img_path_relatif = corriger_chemin_image(img_path_brut)
        img_path_absolu = os.path.join(base_dir, img_path_relatif) if img_path_relatif else ""
        
        if img_path_absolu and os.path.exists(img_path_absolu):
            st.image(img_path_absolu, caption=f"Matricule : {form_data['N° Matricule (Etiquetage)']}", use_container_width=True)
        elif img_path_relatif and os.path.exists(os.path.join(base_dir, img_path_relatif)):
            st.image(os.path.join(base_dir, img_path_relatif), caption=f"Matricule : {form_data['N° Matricule (Etiquetage)']}", use_container_width=True)
        else:
            st.warning("⚠️ Aucune image trouvée pour cet élément ou chemin invalide.")
            st.info(f"Chemin recherché : `{img_path_relatif if img_path_relatif else 'Aucun'}`")
    else:
        st.info("💡 Sélectionnez une ligne dans le tableau ci-dessus pour afficher sa photo.")

# --- BARRE D'ACTIONS (BOUTONS) ---
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
            st.error("Veuillez d'abord sélectionner une ligne dans le tableau pour la modifier.")

with col_b3:
    if st.button("❌ Supprimer l'actif sélectionné", use_container_width=True):
        if st.session_state.selected_index is not None:
            st.session_state.data_df = st.session_state.data_df.drop(st.session_state.selected_index).reset_index(drop=True)
            st.session_state.selected_index = None
            # Réinitialiser les champs
            for col in cols:
                st.session_state[f"input_{col}"] = ""
            sauvegarder()
            st.rerun()
        else:
            st.error("Veuillez d'abord sélectionner une ligne dans le tableau pour la supprimer.")

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
                st.success(f"🖨️ Fiche créée au format texte sous : `{print_path}`")
            except Exception as e:
                st.error(f"Erreur d'impression : {e}")
        else:
            st.error("Sélectionnez d'abord un actif à imprimer.")