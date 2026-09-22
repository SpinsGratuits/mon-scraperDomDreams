import json
from datetime import datetime, date
import cloudscraper
from bs4 import BeautifulSoup
import re

# 1. URL du site cible
url = "https://gamewave.fr/domino-dreams/domino-dreams-liens-pieces-gratuites-free-coins/"

# Création d'un scraper qui imite un navigateur Chrome sur Windows
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})

try:
    response = scraper.get(url)
    status_code = response.status_code
    html_text = response.text
except Exception as e:
    status_code = 500
    html_text = ""
    print(f"Erreur lors du contournement du blocage : {e}")

if status_code == 200:
    soup = BeautifulSoup(html_text, "html.parser")
    date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_du_jour = date.today().strftime("%d/%m/%Y")
    
    # Liste qui contiendra nos dictionnaires d'objets JSON
    json_data = []
    
    # 2. Scanner TOUS les liens hypertextes de la page
    all_links = soup.find_all("a", href=True)
    
    for link in all_links:
        href = link["href"]
        
        # Cibler n'importe quel lien contenant join.domino-dreams.com ou les redirections
        if "join.domino-dreams.com" in href or "stg.fyi" in href:
            # Récupérer en priorité la ligne du tableau HTML pour un contexte parfait
            parent_tr = link.find_parent('tr')
            if parent_tr:
                parent_text = parent_tr.get_text(separator=" ").strip()
            else:
                parent_text = link.find_parent().get_text(separator=" ").strip() if link.find_parent() else ""
                if len(parent_text) < 15 and link.find_parent().find_parent():
                    parent_text = link.find_parent().find_parent().get_text(separator=" ").strip()
            
            clean_text = " ".join(parent_text.split())
            
            # --- EXTRACTION DE LA DATE ---
            date_match = re.search(r'\d{2}/\d{2}/\d{4}', clean_text)
            if date_match:
                date_evenement = date_match.group(0)
            else:
                date_courte_match = re.search(r'\b\d{2}/\d{2}\b', clean_text)
                date_evenement = f"{date_courte_match.group(0)}/{date.today().year}" if date_courte_match else date_du_jour
            
            # --- EXTRACTION DE L'HEURE ---
            # Intercepte des formats comme "20:10", "14h10"
            heure_match = re.search(r'\b\d{1,2}[h:]\d{2}\b', clean_text, re.IGNORECASE)
            if heure_match:
                # Standardisation automatique (ex: 9h10 -> 09:10)
                heure_brute = heure_match.group(0).lower().replace('h', ':')
                if len(heure_brute.split(':')) == 1:
                    heure_brute = "0" + heure_brute
                heure_evenement = heure_brute
            else:
                heure_evenement = "00:00"  # Valeur par défaut si absente
            
            # --- EXTRACTION DE LA RÉCOMPENSE (Pièces / Coins) ---
            # Recherche des motifs numériques suivis de pièces/coins (ex: "2X Pièces gratuites")
            recompense_match = re.search(r'\b\d+X?\s*(?:Pièces|pieces|Coins|coins|Bonus)[\s\w]*', clean_text, re.IGNORECASE)
            if recompense_match:
                type_recompense = recompense_match.group(0).strip()
            else:
                type_recompense = "2X Pièces gratuites"  # Valeur par défaut constatée sur la page
                
            # Nettoyage des chaînes résiduelles de l'élément cliquable
            type_recompense = re.sub(r'\s*Récupérer$', '', type_recompense, flags=re.IGNORECASE).strip()
            
            # Éviter les doublons
            if not any(item["lienurl"] == href for item in json_data):
                json_data.append({
                    "date_scraping": date_now, 
                    "date": date_evenement, 
                    "heure": heure_evenement,
                    "recompense": type_recompense, 
                    "lienurl": href
                })

    # 3. Écriture du fichier JSON
    filename = "scrapdominodreams.json"
    
    if not json_data:
        json_data.append({
            "date_scraping": date_now,
            "statut": "VIDE",
            "message": "Aucun lien trouvé sur la page. Vérifiez manuellement le site."
        })
        print("Aucun lien extrait.")
    else:
        print(f"Succès total ! {len(json_data)} liens trouvés et sauvegardés malgré la protection.")

    with open(filename, mode="w", encoding="utf-8") as json_file:
        json.dump(json_data, json_file, indent=4, ensure_ascii=False)
            
else:
    print(f"Erreur d'accès réseau (Code {status_code}). Le site bloque toujours.")
