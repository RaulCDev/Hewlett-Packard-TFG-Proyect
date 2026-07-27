EXAMPLE_VALUES = {"replace-me", "changeme"}


def rapidapi_integration_status(environ):
    value = (environ.get("RAPIDAPI_KEY") or "").strip()
    configured = bool(value) and value.lower() not in EXAMPLE_VALUES
    return {
        "service": "rapidapi",
        "configured": configured,
        "source": "rapidapi" if configured else "fixture",
        "missingCredentials": [] if configured else ["RAPIDAPI_KEY"],
    }


def merge_runtime_source(status, runtime_source):
    merged = dict(status)
    if runtime_source not in {"rapidapi", "fixture"}:
        return merged
    merged["source"] = runtime_source
    if runtime_source == "fixture":
        merged["fallbackReason"] = (
            "live_api_unavailable" if merged["configured"] else "missing_credentials"
        )
    else:
        merged.pop("fallbackReason", None)
    return merged
