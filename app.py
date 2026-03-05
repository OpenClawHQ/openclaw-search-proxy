import os
from itertools import islice
from typing import Any, Dict, List, Optional, Tuple

from duckduckgo_search import DDGS
from flask import Flask, jsonify, request

app = Flask(__name__)

# -----------------------------
# Config (OpenClaw-friendly)
# -----------------------------

SEARCH_DEFAULT_MAX_RESULTS = int(os.getenv("SEARCH_DEFAULT_MAX_RESULTS", "10"))
SEARCH_MAX_RESULTS_HARD_LIMIT = int(os.getenv("SEARCH_MAX_RESULTS_HARD_LIMIT", "50"))
FREE_SEARCH_PROXY_TOKEN = os.getenv("FREE_SEARCH_PROXY_TOKEN")  # optional shared secret
SERVICE_NAME = "openclaw-free-search-proxy"
SERVICE_VERSION = os.getenv("FREE_SEARCH_PROXY_VERSION", "v1")


def _extract_query_and_limit() -> Tuple[str, int]:
    """
    Extract query string and max_results from GET/POST.
    Applies default and hard limit from environment.
    """
    if request.method == "POST":
        keywords = request.form.get("q", "") or ""
        max_results_raw = request.form.get("max_results")
    else:
        keywords = request.args.get("q", "") or ""
        max_results_raw = request.args.get("max_results")

    try:
        max_results = int(max_results_raw) if max_results_raw is not None else SEARCH_DEFAULT_MAX_RESULTS
    except ValueError:
        max_results = SEARCH_DEFAULT_MAX_RESULTS

    if max_results <= 0:
        max_results = SEARCH_DEFAULT_MAX_RESULTS
    if max_results > SEARCH_MAX_RESULTS_HARD_LIMIT:
        max_results = SEARCH_MAX_RESULTS_HARD_LIMIT

    return keywords.strip(), max_results


def _error(status: int, code: str, message: str):
    """
    Unified error envelope for v1 endpoints.
    """
    return (
        jsonify(
            {
                "ok": False,
                "error": {
                    "code": code,
                    "message": message,
                },
            }
        ),
        status,
    )


def _check_auth() -> Optional[Any]:
    """
    Optional token check for v1 endpoints.

    If FREE_SEARCH_PROXY_TOKEN is set, require X-OpenClaw-Search-Token to match.
    """
    if not FREE_SEARCH_PROXY_TOKEN:
        return None

    token = request.headers.get("X-OpenClaw-Search-Token")
    if token != FREE_SEARCH_PROXY_TOKEN:
        return _error(401, "unauthorized", "Invalid or missing search token.")

    return None


def _search_ddg(kind: str, keywords: str, max_results: int) -> List[Dict[str, Any]]:
    """
    Run a DuckDuckGo search of a given kind and return at most max_results.
    kind: text | answers | images | videos
    """
    results: List[Dict[str, Any]] = []

    if not keywords:
        return results

    with DDGS() as ddgs:
        if kind == "text":
            gen = ddgs.text(keywords, safesearch="Off", timelimit="y", backend="lite")
        elif kind == "answers":
            gen = ddgs.answers(keywords)
        elif kind == "images":
            gen = ddgs.images(keywords, safesearch="Off", timelimit=None)
        elif kind == "videos":
            gen = ddgs.videos(
                keywords,
                safesearch="Off",
                timelimit=None,
                resolution="high",
            )
        else:
            raise ValueError(f"Unsupported search kind: {kind}")

        for r in islice(gen, max_results):
            results.append(r)

    return results


# -----------------------------
# Root & health
# -----------------------------


@app.route("/", methods=["GET"])
def root():
    """
    Simple service description for the OpenClaw ecosystem.
    """
    return jsonify(
        {
            "name": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "description": "Search proxy API for OpenClaw skills, powered by DuckDuckGo.",
            "endpoints": {
                "text": "/v1/search/text",
                "answers": "/v1/search/answers",
                "images": "/v1/search/images",
                "videos": "/v1/search/videos",
            },
            "legacy_endpoints": [
                "/search",
                "/searchAnswers",
                "/searchImages",
                "/searchVideos",
            ],
            "limits": {
                "default_max_results": SEARCH_DEFAULT_MAX_RESULTS,
                "hard_max_results": SEARCH_MAX_RESULTS_HARD_LIMIT,
            },
            "auth": {
                "requires_token": bool(FREE_SEARCH_PROXY_TOKEN),
                "header": "X-OpenClaw-Search-Token",
            },
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


# -----------------------------
# v1 endpoints (recommended)
# -----------------------------


def _handle_v1(kind: str):
    # Optional auth
    auth_error = _check_auth()
    if auth_error is not None:
        return auth_error

    keywords, max_results = _extract_query_and_limit()
    if not keywords:
        return _error(400, "bad_request", "Missing query parameter q.")

    try:
        results = _search_ddg(kind, keywords, max_results)
    except Exception as exc:  # noqa: BLE001
        return _error(502, "upstream_error", f"DuckDuckGo search failed: {exc}")

    return jsonify(
        {
            "ok": True,
            "query": keywords,
            "type": kind,
            "results": results,
            "meta": {
                "max_results": max_results,
            },
        }
    )


@app.route("/v1/search/text", methods=["GET", "POST"])
def search_text():
    return _handle_v1("text")


@app.route("/v1/search/answers", methods=["GET", "POST"])
def search_answers():
    return _handle_v1("answers")


@app.route("/v1/search/images", methods=["GET", "POST"])
def search_images():
    return _handle_v1("images")


@app.route("/v1/search/videos", methods=["GET", "POST"])
def search_videos():
    return _handle_v1("videos")


# -----------------------------
# Legacy endpoints (compat)
# -----------------------------


@app.route("/search", methods=["GET", "POST"])
def search_legacy_text():
    keywords, max_results = _extract_query_and_limit()
    results = _search_ddg("text", keywords, max_results)
    return jsonify({"results": results})


@app.route("/searchAnswers", methods=["GET", "POST"])
def search_legacy_answers():
    keywords, max_results = _extract_query_and_limit()
    results = _search_ddg("answers", keywords, max_results)
    return jsonify({"results": results})


@app.route("/searchImages", methods=["GET", "POST"])
def search_legacy_images():
    keywords, max_results = _extract_query_and_limit()
    results = _search_ddg("images", keywords, max_results)
    return jsonify({"results": results})


@app.route("/searchVideos", methods=["GET", "POST"])
def search_legacy_videos():
    keywords, max_results = _extract_query_and_limit()
    results = _search_ddg("videos", keywords, max_results)
    return jsonify({"results": results})


if __name__ == "__main__":
    # Keep the same as upstream: good for docker / local dev
    app.run(host="0.0.0.0", port=8000)
