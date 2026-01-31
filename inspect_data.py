import json
from pathlib import Path

path = Path("data.json")
data = json.loads(path.read_text(encoding="utf-8"))

print(type(data))

# Example: Print the top-level keys if it's a dictionary
if isinstance(data, dict):
    print("Top-level keys:", list(data.keys()))

# Example: Print the number of records for each key if it's a list
for key, value in data.items():
    if isinstance(value, list):
        print(f"{key}: {len(value)} records")
    else:
        print(f"{key}: type={type(value)}")

# Pretty-print a sample record from each key

import pprint

pp = pprint.PrettyPrinter(indent=2, width=120)

for key in data.keys():
    print("\n==============================")
    print(f"{key} sample")
    print("==============================")
    pp.pprint(data[key][1])

# Collect and count keys in dictionaries within lists

from collections import Counter

def collect_keys(items):
    keys = []
    for x in items:
        if isinstance(x, dict):
            keys.extend(x.keys())
    return Counter(keys)

for key in ["movies", "actors", "genres", "titleTypes"]:
    print(f"\n== {key} keys ==")
    counter = collect_keys(data[key])
    for k, v in counter.most_common():
        print(f"{k}: {v}")

# Check uniqueness of certain fields
print("\n[Uniqueness]")
movies = data["movies"]
actors = data["actors"]

print("movies.id unique:", len({m["id"] for m in movies}) == len(movies))
print("actors.nconst unique:", len({a["nconst"] for a in actors}) == len(actors))

# Check relations between movies and actors
print("\n[Relations]")
movie_ids = {m["id"] for m in movies}
known_for = []
for a in actors:
    kft = a.get("knownForTitles")
    if isinstance(kft, list):
        known_for.extend(kft)
    elif isinstance(kft, str):
        known_for.append(kft)

hit = sum(1 for x in known_for if x in movie_ids)
print("knownForTitles matched:", hit, "/", len(known_for))

# Inspect specific fields
for key in ["genres", "titleTypes"]:
    v = data.get(key)
    print(f"\n== {key} ==")
    print("type:", type(v))
    print("len:", len(v) if hasattr(v, "__len__") else None)
    if isinstance(v, list) and v:
        print("first element:", v[0], type(v[0]))

# Print unique values for genres and titleTypes
print("\n== genres unique values ==")
genres_unique = sorted(
    g for g in data["genres"] if g is not None
)

for g in genres_unique:
    print(g)

print("\n== titleTypes unique values ==")
title_types_unique = sorted(
    t for t in data["titleTypes"] if t is not None
)

for t in title_types_unique:
    print(t)