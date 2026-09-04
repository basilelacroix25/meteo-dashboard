# Station météo — B3D

Dashboard temps réel + archive historique pour ta station Netatmo (Salon,
Bureau, Extérieur, Anémomètre, Chambre via le Home Coach).

## Comment ça marche

- `.github/workflows/collect.yml` lance `collect.py` toutes les 15 minutes
  via GitHub Actions.
- `collect.py` interroge l'API Netatmo (`getstationsdata` pour la station +
  modules, `gethomecoachsdata` pour le Coach de la chambre), et ajoute les
  mesures dans `data/history.csv` + `data/latest.json`.
- Le workflow commit et pousse ces fichiers à chaque exécution.
- `index.html` (servi par GitHub Pages) lit ces fichiers et affiche le
  dashboard — cartes temps réel, courbes par période, heatmap calendrier.

## Mise en route

### 1. Créer une app Netatmo
Sur https://dev.netatmo.com/apps/, crée une app. Note le **Client ID** et le
**Client secret**. Ajoute une Redirect URI, par exemple `http://localhost:8080`
(elle n'a pas besoin de répondre à quoi que ce soit).

### 2. Récupérer ton refresh_token (une seule fois, en local)
```
pip install requests
python get_refresh_token.py
```
Suis les instructions à l'écran (ça ouvre une URL Netatmo dans ton
navigateur, tu récupères un `code` dans l'URL de redirection, tu le colles
dans le terminal). Le script te donne ton `refresh_token` à la fin.

### 3. Créer le repo GitHub et ajouter les secrets
Pousse ce dossier vers un nouveau repo GitHub, puis dans
**Settings → Secrets and variables → Actions**, ajoute :
- `NETATMO_CLIENT_ID`
- `NETATMO_CLIENT_SECRET`
- `NETATMO_REFRESH_TOKEN`

### 4. Activer GitHub Pages
**Settings → Pages** → Source : `Deploy from a branch` → branche `main`,
dossier `/ (root)`.

### 5. Lancer une première collecte
Onglet **Actions** du repo → workflow "Collecte météo Netatmo" →
**Run workflow** (pas besoin d'attendre les 15 minutes pour tester).

## Limites actuelles / pistes d'évolution

- Pas encore de rose des vents ni de graphe de pression/bruit dans le
  dashboard — facile à ajouter sur le même modèle que température/CO2.
- `history.csv` grossit indéfiniment (environ 15-20 Mo/an avec 5 modules
  toutes les 15 min) — largement gérable pour GitHub, mais on pourra
  archiver par année si besoin plus tard.
- Le refresh_token Netatmo n'est pas ré-écrit automatiquement après chaque
  utilisation ; en pratique il reste valide très longtemps. Si l'auth finit
  par échouer un jour, il suffit de relancer `get_refresh_token.py`.
