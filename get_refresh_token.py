#!/usr/bin/env python3
"""
À exécuter UNE SEULE FOIS, en local, pour obtenir ton premier refresh_token
Netatmo. Ensuite, il va dans les secrets GitHub Actions et collect.py s'en
sert pour se reconnecter tout seul, indéfiniment.

Usage :
  1. Crée une app sur https://dev.netatmo.com/apps/ (note client_id et client_secret)
  2. Dans les paramètres de l'app, mets une "Redirect URI" quelconque,
     par exemple http://localhost:8080
  3. Lance : python get_refresh_token.py
  4. Suis les instructions affichées.
"""
import urllib.parse
import requests

CLIENT_ID = input("Client ID : ").strip()
CLIENT_SECRET = input("Client secret : ").strip()
REDIRECT_URI = input("Redirect URI (celle configurée sur dev.netatmo.com) : ").strip()

scope = "read_station read_homecoach"
auth_url = "https://api.netatmo.com/oauth2/authorize?" + urllib.parse.urlencode({
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "scope": scope,
    "state": "b3dmeteo",
})

print("\n1. Ouvre cette URL dans ton navigateur, connecte-toi et accepte :")
print(auth_url)
print("\n2. Tu vas être redirigé vers une URL qui ne charge rien (normal),")
print("   du type http://localhost:8080/?state=b3dmeteo&code=XXXXXXX")
print("   Copie juste la valeur de 'code' ci-dessous.\n")

code = input("Code : ").strip()

resp = requests.post("https://api.netatmo.com/oauth2/token", data={
    "grant_type": "authorization_code",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": code,
    "redirect_uri": REDIRECT_URI,
    "scope": scope,
})
resp.raise_for_status()
data = resp.json()

print("\nÇa a marché ! Voici ton refresh_token (à mettre dans le secret GitHub NETATMO_REFRESH_TOKEN) :\n")
print(data["refresh_token"])
