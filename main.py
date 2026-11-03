import json
import csv
import sys
from pathlib import Path

# Folder jisme saari JSON files hain (command line se bhi de sakte ho)
FOLDER = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
OUTPUT_CSV = Path("image_id_category.csv")
OUTPUT_TXT = Path("image_id_category.txt")
FIELDS = ["image_id", "category", "json_file"]


def get_category(data):
    """Category nikalta hai: pehle image_classification.material,
    nahi mila to image_id se (tha_billboard_00067 -> billboard)."""
    material = data.get("image_classification", {}).get("material")
    if material:
        return material

    parts = data.get("image_id", "").split("_")
    return parts[1] if len(parts) >= 3 else ""


def load_done():
    """Pehle se process ho chuki files (json path) aur image_ids ka set."""
    done_files, done_ids = set(), set()
    if OUTPUT_CSV.exists():
        with open(OUTPUT_CSV, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                done_files.add(row["json_file"])
                done_ids.add(row["image_id"])
    return done_files, done_ids


def main():
    done_files, done_ids = load_done()
    print(f"Pehle se done: {len(done_ids)} images")

    new_rows = []
    skipped = 0
    for json_file in sorted(FOLDER.rglob("*.json")):
        rel = str(json_file.relative_to(FOLDER))

        if rel in done_files:  # file open kiye bina skip
            skipped += 1
            continue

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Skip: {json_file} ({e})")
            continue

        image_id = data.get("image_id")
        if not image_id or image_id in done_ids:
            skipped += 1
            continue

        done_ids.add(image_id)
        new_rows.append({"image_id": image_id,
                         "category": get_category(data),
                         "json_file": rel})

    if new_rows:
        write_header = not OUTPUT_CSV.exists()
        with open(OUTPUT_CSV, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            if write_header:
                writer.writeheader()
            writer.writerows(new_rows)

        # txt me sirf id aur category (har line: image_id,category)
        with open(OUTPUT_TXT, "a", encoding="utf-8") as f:
            for r in new_rows:
                f.write(f"{r['image_id']},{r['category']}\n")

        for r in new_rows:
            print(r["image_id"], "->", r["category"])

    print(f"\nNayi process hui: {len(new_rows)} | Skip (pehle se done): {skipped}")


if __name__ == "__main__":
    main()