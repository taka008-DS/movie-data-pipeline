import json
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

REGION = "ap-northeast-1"
PROFILE = "default"   # ← movie などにしているなら変更
TABLE_NAME = "dynamodb"
DATA_PATH = Path(__file__).resolve().parent / "data.json"

def iter_items_with_keys(data: dict):
    """data.json の各カテゴリを DynamoDB Item 形式（PK/SK付き）に変換して順に返す"""
    # movies
    for m in data.get("movies", []):
        # m は dict 前提
        movie_id = m.get("id")
        if not movie_id:
            continue
        item = dict(m)  # 元データを壊さない
        item["PK"] = f"MOVIE#{movie_id}"
        item["SK"] = f"MOVIE#{movie_id}"
        yield item

    # actors
    for a in data.get("actors", []):
        nconst = a.get("nconst")
        if not nconst:
            continue
        item = dict(a)
        item["PK"] = f"ACTOR#{nconst}"
        item["SK"] = f"ACTOR#{nconst}"
        yield item

    # genres (None除外)
    genres = data.get("genres", [])
    if isinstance(genres, list):
        for g in genres:
            if g is None:
                continue
            if not isinstance(g, str):
                continue
            yield {
                "PK": "META#GENRE",
                "SK": f"GENRE#{g}",
                "value": g
            }

    # titleTypes (None除外)
    title_types = data.get("titleTypes", [])
    if isinstance(title_types, list):
        for t in title_types:
            if t is None:
                continue
            if not isinstance(t, str):
                continue
            yield {
                "PK": "META#TITLETYPE",
                "SK": f"TITLETYPE#{t}",
                "value": t
            }

def batch_write_all(table, items_iter):
    """
    batch_writer は内部で 25件単位 + リトライをいい感じにやってくれる。
    なので自前 chunks は不要で、iterをそのまま流し込めばOK。
    """
    count = 0
    with table.batch_writer() as batch:
        for item in items_iter:
            batch.put_item(Item=item)
            count += 1
            if count % 500 == 0:
                print(f"written: {count}")
    return count

def main():
    # 1) load json
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    # 2) boto3 session/table
    session = boto3.Session(profile_name=PROFILE, region_name=REGION)
    dynamodb = session.resource("dynamodb")
    table = dynamodb.Table(TABLE_NAME)

    # 3) write
    total = batch_write_all(table, iter_items_with_keys(data))
    print(f"done. total written = {total}")

    # 4) query check examples
    print("\n[Query check examples]")

    # (a) genre一覧が取れるか
    try:
        res = table.query(
            KeyConditionExpression=Key("PK").eq("META#GENRE")
        )
        print("META#GENRE items:", res.get("Count"))
        # 最初の数件だけ表示
        for it in res.get("Items", [])[:5]:
            print(it)
    except ClientError as e:
        print("query META#GENRE failed:", e)

    # (b) actors を1件取れるか（例：先頭の nconst を使う）
    actors = data.get("actors", [])
    if actors:
        nconst = actors[0].get("nconst")
        if nconst:
            pk = f"ACTOR#{nconst}"
            res = table.query(
                KeyConditionExpression=Key("PK").eq(pk)
            )
            print(f"Query {pk} count:", res.get("Count"))
            for it in res.get("Items", [])[:1]:
                print(it)

    # (c) movies を1件取れるか（例：先頭の id を使う）
    movies = data.get("movies", [])
    if movies:
        mid = movies[0].get("id")
        if mid:
            pk = f"MOVIE#{mid}"
            res = table.query(
                KeyConditionExpression=Key("PK").eq(pk)
            )
            print(f"Query {pk} count:", res.get("Count"))
            for it in res.get("Items", [])[:1]:
                print(it)

if __name__ == "__main__":
    main()