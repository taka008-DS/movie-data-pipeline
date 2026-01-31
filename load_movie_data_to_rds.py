import os
import boto3
import psycopg2
from decimal import Decimal
from boto3.dynamodb.conditions import Attr

REGION = "us-east-1"
DDB_TABLE = "dynamodb"

RDS_HOST = os.getenv("TF_VAR_DB_HOST")  # 例: xxxx.us-east-1.rds.amazonaws.com
RDS_DB   = os.getenv("TF_VAR_DB_NAME")
RDS_USER = os.getenv("TF_VAR_USER_NAME")
RDS_PASS = os.getenv("TF_VAR_PASSWORD")


def scan_all(table, filter_expression=None):
    items = []
    kwargs = {}
    if filter_expression is not None:
        kwargs["FilterExpression"] = filter_expression

    res = table.scan(**kwargs)
    items.extend(res.get("Items", []))
    while "LastEvaluatedKey" in res:
        res = table.scan(ExclusiveStartKey=res["LastEvaluatedKey"], **kwargs)
        items.extend(res.get("Items", []))
    return items


def _to_int(x):
    """Decimal/str/int/None を int or None にする"""
    if x is None:
        return None
    if isinstance(x, Decimal):
        return int(x)
    if isinstance(x, int):
        return x
    if isinstance(x, str) and x.isdigit():
        return int(x)
    return None


def _get_text(d):
    """{'text': '...'} 形式から text を取り出す"""
    if isinstance(d, dict):
        return d.get("text")
    return None


def normalize_movie(item: dict) -> dict:
    """
    DynamoDBのmovie item（サンプルの形）から、RDSに入れる形に整形する
    """
    movie_id = item.get("id")

    title = _get_text(item.get("titleText"))
    original_title = _get_text(item.get("originalTitleText"))

    # releaseYear: {'year': Decimal('2023'), 'endYear': None, ...}
    release_year = None
    ry = item.get("releaseYear")
    if isinstance(ry, dict):
        release_year = _to_int(ry.get("year"))
    else:
        # 念のため別形式にも対応
        release_year = _to_int(ry)

    # titleType: dict（例：{'id': 'tvEpisode', 'text': 'TV Episode', ...}）
    title_type_id = None
    title_type_text = None
    tt = item.get("titleType")
    if isinstance(tt, dict):
        title_type_id = tt.get("id")
        title_type_text = tt.get("text")
    else:
        # もし文字列で入っているケースにも対応
        title_type_text = tt

    # primaryImage: dict（url を取りたい）
    primary_image_url = None
    pi = item.get("primaryImage")
    if isinstance(pi, dict):
        primary_image_url = pi.get("url")

    # genre: サンプルは文字列
    genre = item.get("genre")

    return {
        "movie_id": movie_id,
        "title": title,
        "original_title": original_title,
        "release_year": release_year,
        "title_type_id": title_type_id,
        "title_type_text": title_type_text,
        "genre": genre,
        "primary_image_url": primary_image_url,
    }


def main():
    # 1) DynamoDBからmovies取得
    session = boto3.Session(region_name=REGION)
    ddb = session.resource("dynamodb")
    table = ddb.Table(DDB_TABLE)

    movie_items = scan_all(table, filter_expression=Attr("PK").begins_with("MOVIE#"))
    movies = [normalize_movie(x) for x in movie_items if x.get("id")]

    print("movies fetched:", len(movies))
    print("sample normalized:", movies[:1])

    # 2) RDSへ接続
    if not all([RDS_HOST, RDS_DB, RDS_USER, RDS_PASS]):
        raise RuntimeError("Missing env vars: DB_HOST, DB_NAME, DB_USER, PASSWORD")

    conn = psycopg2.connect(
        host=RDS_HOST,
        database=RDS_DB,
        user=RDS_USER,
        password=RDS_PASS,
        port=5432
    )
    cur = conn.cursor()

    # 3) テーブル作成（サンプルに合わせてカラム増やす）
    cur.execute("""
    CREATE TABLE IF NOT EXISTS movies (
      movie_id TEXT PRIMARY KEY,
      title TEXT,
      original_title TEXT,
      release_year INT,
      title_type_id TEXT,
      title_type_text TEXT,
      genre TEXT,
      primary_image_url TEXT,
      inserted_at TIMESTAMP DEFAULT NOW()
    );
    """)

    # 4) データ投入（UPSERT）
    cur.executemany("""
    INSERT INTO movies (
      movie_id, title, original_title, release_year,
      title_type_id, title_type_text, genre, primary_image_url
    )
    VALUES (
      %(movie_id)s, %(title)s, %(original_title)s, %(release_year)s,
      %(title_type_id)s, %(title_type_text)s, %(genre)s, %(primary_image_url)s
    )
    ON CONFLICT (movie_id)
    DO UPDATE SET
      title = EXCLUDED.title,
      original_title = EXCLUDED.original_title,
      release_year = EXCLUDED.release_year,
      title_type_id = EXCLUDED.title_type_id,
      title_type_text = EXCLUDED.title_type_text,
      genre = EXCLUDED.genre,
      primary_image_url = EXCLUDED.primary_image_url;
    """, movies)

    conn.commit()
    cur.close()
    conn.close()

    print("done: inserted/updated", len(movies), "movies")


if __name__ == "__main__":
    main()