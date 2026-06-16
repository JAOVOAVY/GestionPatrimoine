import streamlit as st
import pandas as pd
import os
import csv

# Configuration de la page Streamlit
st.set_page_config(page_title="Gestion de Patrimoine", layout="wide")

st.title("📦 Gestion de Patrimoine - Version Web Interactive")

# --- ADAPTATION POUR LE WEB (Chemins relatifs) ---
base_dir = "."
current_file_path = os.path.join(base_dir, "patrimoine.csv")
image_dir = os.path.join(base_dir, "image")

# Créer le dossier image s'il n'existe pas encore
if not os.path.exists(image_dir):
    os.makedirs(image_dir)

cols = ["N° Matricule (Etiquetage)", "Type", "Désignation", "Identification", "Nombre", "Localisation", "Détenteur", "Observations", "Image"]

# --- INITIALISATION DES CLÉS DE SESSION ---
for col in cols:
    if f"input_{col}" not in st.session_state:
        st.session_state[f"input_{col}"] = ""

if 'selected_index' not in st.session_state:
    st.session_state.selected_index = None

# --- 📁 SÉLECTION DU FICHIER CSV ---
st.subheader("📂 Sélection du fichier de données")
fichier_charge = st.file_uploader("Ouvrir un fichier CSV personnalisé (Optionnel) :", type=["csv"])

if fichier_charge is not None:
    source_csv = fichier_charge
    st.info("📊 Utilisation du fichier CSV téléversé depuis votre appareil.")
else:
    source_csv = current_file_path
    st.info("💻 Chargement automatique depuis le dépôt GitHub.")

# Chargement initial des données
if 'data_df' not in st.session_state or fichier_charge is not None:
    df = pd.DataFrame(columns=cols)
    try:
        if (fichier_charge is not None) or os.path.exists(current_file_path):
            df = pd.read_csv(
                source_csv, 
                sep=";", 
                encoding='latin-1', 
                on_bad_lines='skip', 
                quoting=csv.QUOTE_NONE
            )
            df.columns = [c.replace(',,', '').strip() for c in df.columns]
            for col in cols:
                if col not in df.columns:
                    df[col] = ""
            df = df[cols]
    except Exception as e:
        st.error(f"Erreur de chargement du fichier CSV : {e}")
    
    st.session_state.data_df = df

# --- 1. BARRE DE FILTRES ---
st.subheader("🔍 Filtres de recherche")
col_f1, col_f2 = st.columns(2)

with col_f1:
    types_existants = ["Tous les Types"] + sorted([str(t).strip() for t in st.session_state.data_df["Type"].dropna().unique() if str(t).strip() != ""])
    selected_type = st.selectbox("Filtrer par Type :", types_existants)

with col_f2:
    localisations_existantes = ["Toutes les Localisations"] + sorted([str(l).strip() for l in st.session_state.data_df["Localisation"].dropna().unique() if str(l).strip() != ""])
    selected_loc = st.selectbox("Filtrer par Localisation :", localisations_existantes)

# Application des filtres
filtered_df = st.session_state.data_df.copy()
if selected_type != "Tous les Types":
    filtered_df = filtered_df[filtered_df["Type"].astype(str).str.strip() == selected_type]
if selected_loc != "Toutes les Localisations":
    filtered_df = filtered_df[filtered_df["Localisation"].astype(str).str.strip() == selected_loc]


# --- 🔄 FONCTION DE RAPPEL POUR LE CLIC ---
def maj_selection():
    evenement = st.session_state.evenement_tableau
    if evenement and "rows" in evenement["selection"] and evenement["selection"]["rows"]:
        ligne_affichee_index = evenement["selection"]["rows"][0]
        vraie_ligne = filtered_df.iloc[ligne_affichee_index]
        matricule_clique = str(vraie_ligne["N° Matricule (Etiquetage)"]).strip()
        
        indices_globaux = st.session_state.data_df.index[st.session_state.data_df["N° Matricule (Etiquetage)"].astype(str).str.strip() == matricule_clique].tolist()
        if indices_globaux:
            st.session_state.selected_index = indices_globaux[0]
            for c in cols:
                val = str(st.session_state.data_df.at[st.session_state.selected_index, c]).strip()
                val = val.replace(",,", "").strip()
                st.session_state[f"input_{c}"] = "" if val in ["nan", "None"] else val


# --- INTERACTION : CLIC SUR LE TABLEAU ---
st.write("---")
st.subheader("📋 Récapitulatif des données (Cliquez sur une ligne pour la charger ⬇️)")

st.dataframe(
    filtered_df, 
    use_container_width=True, 
    hide_index=False,
    selection_mode="single-row",
    key="evenement_tableau",      
    on_select=maj_selection       
)


# --- 2. FORMULAIRE ET APERÇU PHOTO ---
st.write("---")
st.subheader("📝 Fiche Élément & Actions")

col_form, col_image = st.columns([0.7, 0.3])

with col_form:
    inputs = {}
    c1, c2 = st.columns(2)
    for i, col in enumerate(cols):
        with c1 if i % 2 == 0 else c2:
            if col == "Image":
                inputs[col] = st.text_input(col, key=f"input_{col}")
                
                fichier_image = st.file_uploader("📸 Choisir une image sur votre appareil :", type=["png", "jpg", "jpeg"], key="upload_image_bouton")
                if fichier_image is not None:
                    # Correction du chemin simulé pour le web (chemin relatif)
                    chemin_simule = f"image/{fichier_image.name}"
                    st.session_state["input_Image"] = chemin_simule
                    inputs[col] = chemin_simule
            else:
                inputs[col] = st.text_input(col, key=f"input_{col}")

with col_image:
    st.write("**📷 Aperçu de la Photo**")
    chemin_image = st.session_state[f"input_Image"].replace(",,", "").strip()
    
    if "upload_image_bouton" in st.session_state and st.session_state.upload_image_bouton is not None:
        st.image(st.session_state.upload_image_bouton, use_container_width=True)
        st.info(f"✨ Nouvelle image sélectionnée : `{st.session_state.upload_image_bouton.name}` (Cliquez sur Modifier ou Ajouter pour l'enregistrer)")
    elif chemin_image and chemin_image.lower() != "nan" and chemin_image != "":
        # Nettoyage des anciens chemins Windows absolus si présents dans le CSV d'origine
        if "gestionpatrimoineandroid" in chemin_image.lower():
            chemin_image = "image/" + os.path.basename(chemin_image)
            
        if os.path.exists(chemin_image) and os.path.isfile(chemin_image):
            try:
                st.image(chemin_image, use_container_width=True)
                st.caption(f"Fichier détecté : `{os.path.basename(chemin_image)}`")
            except Exception as e:
                st.error(f"Erreur d'affichage de l'image : {e}")
        else:
            st.warning("⚠️ Image introuvable dans le dossier du serveur web.")
            st.caption(f"Chemin recherché : `{chemin_image}`")
    else:
        st.info("Aucune image spécifiée.")

# --- BARRE DE BOUTONS D'ACTION ---
st.write(" ")
col_b1, col_b2, col_b3, col_b4 = st.columns(4)

def sauvegarder():
    if fichier_charge is None:
        try:
            st.session_state.data_df.to_csv(current_file_path, index=False, sep=";", encoding='latin-1')
            st.success("💾 Fichier `patrimoine.csv` mis à jour avec succès !")
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde : {e}")
    else:
        st.warning("⚠️ Fichier importé : la modification est stockée temporairement en mémoire.")

def verifier_et_copier_image():
    if "upload_image_bouton" in st.session_state and st.session_state.upload_image_bouton is not None:
        f_img = st.session_state.upload_image_bouton
        destination = os.path.join(image_dir, f_img.name)
        try:
            with open(destination, "wb") as f:
                f.write(f_img.getbuffer())
        except Exception as e:
            st.error(f"Impossible d'enregistrer l'image sur le serveur : {e}")

with col_b1:
    if st.button("➕ Ajouter", type="primary", use_container_width=True):
        matricule = inputs[cols[0]].strip()
        if matricule:
            verifier_et_copier_image()
            nouvelle_ligne = {col: inputs[col].strip() for col in cols}
            st.session_state.data_df = pd.concat([st.session_state.data_df, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
            sauvegarder()
            st.rerun()
        else:
            st.warning("Le N° Matricule est obligatoire pour l'ajout.")

with col_b2:
    if st.button("✏️ Modifier", use_container_width=True):
        if st.session_state.selected_index is not None:
            verifier_et_copier_image()
            for col in cols:
                st.session_state.data_df.at[st.session_state.selected_index, col] = inputs[col].strip()
            sauvegarder()
            st.rerun()
        else:
            st.error("Veuillez d'abord sélectionner une ligne dans le tableau pour la modifier.")

with col_b3:
    if st.button("🗑️ Supprimer", use_container_width=True):
        if st.session_state.selected_index is not None:
            st.session_state.data_df = st.session_state.data_df.drop(st.session_state.selected_index).reset_index(drop=True)
            st.session_state.selected_index = None
            for col in cols:
                st.session_state[f"input_{col}"] = ""
            sauvegarder()
            st.rerun()
        else:
            st.error("Veuillez d'abord sélectionner une ligne dans le tableau pour la supprimer.")

with col_b4:
    if st.button("🖨️ Imprimer la fiche", use_container_width=True):
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
                
                # Permettre le téléchargement direct sur le web au lieu de l'écrire uniquement sur le disque
                with open(print_path, "r", encoding="utf-8") as f:
                    st.download_button(
                        label="📥 Télécharger la fiche imprimée",
                        data=f.read(),
                        file_name="impression_patrimoine.txt",
                        mime="text/plain"
                    )
            except Exception as e:
                st.error(f"Erreur d'impression : {e}")
        else:
            st.error("Sélectionnez d'abord une ligne dans le tableau pour générer sa fiche.")