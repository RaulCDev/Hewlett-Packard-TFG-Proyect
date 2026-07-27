import re


def normalize_game(game):
    if not isinstance(game, dict) or not game.get("appId") or not game.get("title"):
        return None

    normalized = dict(game)
    review_summary = normalized.get("reviewSummary", "")
    match = re.search(r"(\d+)%", review_summary) if review_summary else None
    normalized["reviewPercentage"] = int(match.group(1)) if match else None
    normalized["appId"] = str(normalized["appId"])
    return normalized
