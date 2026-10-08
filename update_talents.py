import os
import csv
import requests

# ── CONFIG ────────────────────────────────────────────────────────────
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

CSV_FILE = "nieuwe_talenten.csv"  # Zet dit bestand in de root van je repo

# ── Haal bestaande namen op uit Supabase ──────────────────────────────
def get_existing_names():
    res = requests.get(
        f"{SUPABASE_URL}/rest/v1/talents?select=naam&limit=10000",
        headers=HEADERS
    )
    data = res.json()
    return {t["naam"].lower().strip() for t in data}

# ── Lees CSV ──────────────────────────────────────────────────────────
def read_csv():
    if not os.path.exists(CSV_FILE):
        print(f"⚠️  {CSV_FILE} niet gevonden in repo — niets te importeren.")
        return []

    talents = []
    with open(CSV_FILE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = [h.lower() for h in reader.fieldnames]

        for row in reader:
            # Normaliseer kolomnamen
            row_lower = {k.lower(): v for k, v in row.items()}

            naam = row_lower.get("naam", "").strip()
            if not naam:
                continue

            categorie = row_lower.get("categorie", "Deelnemer").strip() or "Deelnemer"

            genres_raw = row_lower.get("genres", row_lower.get("genre", "Entertainment"))
            genres = [g.strip() for g in genres_raw.split(",") if g.strip()]
            if not genres:
                genres = ["Entertainment"]

            ig_url = row_lower.get("instagram url", row_lower.get("instagram_url", "")).strip()
            tt_url = row_lower.get("tiktok url", row_lower.get("tiktok_url", "")).strip()

            talents.append({
                "naam": naam,
                "categorie": categorie,
                "categorieen": [categorie],
                "genre": genres[0],
                "genres": genres,
                "instagram_url": ig_url,
                "tiktok_url": tt_url,
                "omroepen": [],
                "programmas": []
            })

    return talents

# ── Voeg talent toe aan Supabase ──────────────────────────────────────
def add_talent(talent):
    res = requests.post(
        f"{SUPABASE_URL}/rest/v1/talents",
        headers=HEADERS,
        json=talent
    )
    return res.status_code in [200, 201]

# ── MAIN ──────────────────────────────────────────────────────────────
def main():
    print("🔍 Bestaande talenten ophalen...")
    existing = get_existing_names()
    print(f"   {len(existing)} talenten in database")

    print(f"\n📂 {CSV_FILE} inlezen...")
    talents = read_csv()
    print(f"   {len(talents)} rijen gevonden in CSV")

    new_talents = [t for t in talents if t["naam"].lower().strip() not in existing]
    print(f"\n✨ {len(new_talents)} nieuwe talenten (nog niet in database)")

    added = []
    skipped = []
    for t in new_talents:
        ok = add_talent(t)
        if ok:
            added.append(t["naam"])
            print(f"   ✓ {t['naam']}")
        else:
            skipped.append(t["naam"])
            print(f"   ✗ Mislukt: {t['naam']}")

    print(f"\n✅ Klaar! {len(added)} toegevoegd, {len(skipped)} mislukt.")

if __name__ == "__main__":
    main()
