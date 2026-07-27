import os

from flask import Flask, jsonify, request
from flask_cors import cross_origin
from pymongo import MongoClient

try:
    from .normalization import normalize_game
except ImportError:
    from normalization import normalize_game


app = Flask(__name__)
client = MongoClient(
    os.getenv(
        "MONGO_URI",
        "mongodb://gameshop:gameshop-development-password@mongo:27017/",
    )
)
db = client["projectCDS"]
collection = db["juegos"]
integration_status_collection = db["integration_status"]


@cross_origin()
@app.route("/save_games", methods=["POST"])
def guardar_juegos():
    games = request.get_json()
    if not isinstance(games, list):
        return jsonify(
            {"success": False, "message": "Se esperaba una lista de juegos."}
        ), 400

    inserted = 0
    skipped = 0
    source = None
    for game in games:
        normalized = normalize_game(game)
        if normalized is None:
            skipped += 1
            continue
        if normalized.get("dataSource") in {"rapidapi", "fixture"}:
            source = normalized["dataSource"]
        result = collection.update_one(
            {"appId": normalized["appId"]},
            {"$setOnInsert": normalized},
            upsert=True,
        )
        if result.upserted_id is not None:
            inserted += 1
        else:
            skipped += 1

    if source:
        integration_status_collection.update_one(
            {"service": "rapidapi"},
            {"$set": {"source": source}},
            upsert=True,
        )

    return jsonify(
        {
            "success": True,
            "received": len(games),
            "inserted": inserted,
            "skipped": skipped,
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=False, port=4002, host="0.0.0.0")
