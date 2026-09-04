#!/usr/bin/env python3
"""
Collecte les relevés Netatmo (Station Météo + Home Coach) et les archive
dans data/history.csv (une ligne par mesure) + data/latest.json (dernier
instantané, utilisé pour l'affichage temps réel du dashboard).

Variables d'environnement attendues :
  NETATMO_CLIENT_ID
  NETATMO_CLIENT_SECRET
  NETATMO_REFRESH_TOKEN
"""
import csv
import json
import os
import sys
from datetime import datetime, timezone

import requests

TOKEN_URL = "https://api.netatmo.com/oauth2/token"
STATION_URL = "https://api.netatmo.com/api/getstationsdata"
HOMECOACH_URL = "https://api.netatmo.com/api/gethomecoachsdata"

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
HISTORY_CSV = os.path.join(DATA_DIR, "history.csv")
LATEST_JSON = os.path.join(DATA_DIR, "latest.json")

# Types de données qu'on retrouve dans dashboard_data selon les modules
METRIC_KEYS = [
    "Temperature", "Humidity", "CO2", "Noise", "Pressure",
    "WindStrength", "WindAngle", "GustStrength", "GustAngle", "Rain",
    "health_idx",
]


def get_access_token():
    client_id = os.environ["NETATMO_CLIENT_ID"]
    client_secret = os.environ["NETATMO_CLIENT_SECRET"]
    refresh_token = os.environ["NETATMO_REFRESH_TOKEN"]
    resp = requests.post(TOKEN_URL, data={
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    return payload["access_token"]


def fetch(url, token):
    resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=20)
    resp.raise_for_status()
    return resp.json()["body"]


def extract_rows(module_id, module_name, dashboard_data, ts_fallback):
    """Transforme dashboard_data d'un module en lignes plates (une par métrique)."""
    rows = []
    ts = dashboard_data.get("time_utc", ts_fallback)
    for key in METRIC_KEYS:
        if key in dashboard_data:
            rows.append({
                "timestamp_utc": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                "module": module_name,
                "metric": key,
                "value": dashboard_data[key],
            })
    return rows


def collect_station(token, all_rows, latest):
    body = fetch(STATION_URL, token)
    for device in body.get("devices", []):
        base_name = device.get("module_name") or "Séjour"
        # Le module de base (indoor #1) mesure temp/hum/CO2/bruit/pression
        rows = extract_rows(device["_id"], base_name, device.get("dashboard_data", {}),
                             device.get("last_status_store", 0))
        all_rows.extend(rows)
        for r in rows:
            latest[r["module"]] = latest.get(r["module"], {})
            latest[r["module"]][r["metric"]] = r["value"]
        # Modules additionnels (indoor #2, extérieur, anémomètre...)
        for module in device.get("modules", []):
            name = module.get("module_name", module["_id"])
            rows = extract_rows(module["_id"], name, module.get("dashboard_data", {}),
                                 module.get("last_message", 0))
            all_rows.extend(rows)
            for r in rows:
                latest[r["module"]] = latest.get(r["module"], {})
                latest[r["module"]][r["metric"]] = r["value"]


def collect_homecoach(token, all_rows, latest):
    body = fetch(HOMECOACH_URL, token)
    for device in body.get("devices", []):
        name = device.get("station_name") or device.get("module_name") or "Chambre"
        rows = extract_rows(device["_id"], name, device.get("dashboard_data", {}),
                             device.get("last_status_store", 0))
        all_rows.extend(rows)
        for r in rows:
            latest[r["module"]] = latest.get(r["module"], {})
            latest[r["module"]][r["metric"]] = r["value"]


def append_csv(rows):
    os.makedirs(DATA_DIR, exist_ok=True)
    file_exists = os.path.isfile(HISTORY_CSV)
    with open(HISTORY_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp_utc", "module", "metric", "value"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def write_latest(latest):
    os.makedirs(DATA_DIR, exist_ok=True)
    payload = {
        "updated_utc": datetime.now(timezone.utc).isoformat(),
        "rooms": latest,
    }
    with open(LATEST_JSON, "w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    try:
        token = get_access_token()
    except Exception as exc:
        print(f"Erreur d'authentification Netatmo : {exc}", file=sys.stderr)
        sys.exit(1)

    all_rows = []
    latest = {}

    try:
        collect_station(token, all_rows, latest)
    except Exception as exc:
        print(f"Erreur getstationsdata : {exc}", file=sys.stderr)

    try:
        collect_homecoach(token, all_rows, latest)
    except Exception as exc:
        print(f"Erreur gethomecoachsdata : {exc}", file=sys.stderr)

    if not all_rows:
        print("Aucune donnée récupérée, on ne touche pas aux fichiers.", file=sys.stderr)
        sys.exit(1)

    append_csv(all_rows)
    write_latest(latest)
    print(f"{len(all_rows)} mesures enregistrées.")


if __name__ == "__main__":
    main()
