import os
import requests
from bs4 import BeautifulSoup

# ── CONFIG ────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# ── STAP 1: Haal bestaande namen op uit Supabase ──────────────────────
def get_existing_names():
    res = requests.get(
        f"{SUPABASE_URL}/rest/v1/talents?select=naam",
        headers=HEADERS
    )
    data = res.json()
    return {t["naam"].lower().strip() for t in data}

# ── STAP 2: Scrape Best Social 100 ───────────────────────────────────
def scrape_best_social_100():
    try:
        res = requests.get(
            "https://thebestsocialawards.nl/top100/resultaten",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )
        soup = BeautifulSoup(res.text, "html.parser")
        names = []
        for tag in soup.find_all("h4"):
            name = tag.get_text(strip=True)
            if name and len(name) > 2:
                names.append(name)
        return names
    except Exception as e:
        print(f"Best Social 100 fout: {e}")
        return []

# ── STAP 3: Scrape Influencer100 ──────────────────────────────────────
def scrape_influencer100():
    try:
        res = requests.get(
            "https://m100.nl/influencer100-2026/",
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15
        )
        soup = BeautifulSoup(res.text, "html.parser")
        names = []
        for tag in soup.find_all(["h2", "h3", "h4"]):
            name = tag.get_text(strip=True)
            if name and len(name) > 2 and not name.startswith("#"):
                names.append(name)
        return names
    except Exception as e:
        print(f"Influencer100 fout: {e}")
        return []

# ── STAP 4: Voeg nieuwe talenten toe aan Supabase ─────────────────────
def add_talent(naam):
    payload = {
        "naam": naam,
        "categorie": "Deelnemer",
        "categorieen": ["Deelnemer"],
        "genre": "Entertainment",
        "genres": ["Entertainment"],
        "omroepen": [],
        "programmas": []
    }
    res = requests.post(
        f"{SUPABASE_URL}/rest/v1/talents",
        headers=HEADERS,
        json=payload
    )
    return res.status_code in [200, 201]

# ── MAIN ──────────────────────────────────────────────────────────────
def main():
    print("🔍 Bestaande talenten ophalen...")
    existing = get_existing_names()
    print(f"   {len(existing)} talenten gevonden in database")

    print("\n📋 Lijsten scrapen...")
    all_names = set()
    all_names.update(scrape_best_social_100())
    all_names.update(scrape_influencer100())
    print(f"   {len(all_names)} namen gevonden op lijsten")

    new_names = [
        n for n in all_names
        if n.lower().strip() not in existing and len(n) > 2
    ]
    print(f"\n✨ {len(new_names)} nieuwe talenten gevonden")

    added = []
    for naam in new_names:
        ok = add_talent(naam)
        if ok:
            added.append(naam)
            print(f"   ✓ Toegevoegd: {naam}")
        else:
            print(f"   ✗ Mislukt: {naam}")

    print(f"\n✅ Klaar! {len(added)} talenten toegevoegd.")
    if added:
        print("\nNieuwe talenten:")
        for n in added:
            print(f"  - {n}")

if __name__ == "__main__":
    main()
