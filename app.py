from itertools import islice
from typing import Tuple

from duckduckgo_search import DDGS
from flask import Flask, jsonify, request

app = Flask(__name__)


def _extract_query_and_limit() -> Tuple[str, int]:
    """
    Extract query string and max_results from GET/POST.
    Defaults: q="", max_results=10.
    """
    if request.method == "POST":
        keywords = request.form.get("q", "") or ""
        max_results = int(request.form.get("max_results", 10))
    else:
        keywords = request.args.get("q", "") or ""
        max_results = int(request.args.get("max_results", 10))
    return keywords, max_results


def _search_ddg(kind: str, keywords: str, max_results: int):
    """
    Run a DuckDuckGo search of a given kind and return at most max_results.
    kind: text | answers | images | videos
    """
    results = []
    with DDGS() as ddgs:
        if kind == "text":
            gen = ddgs.text(keywords, safesearch="Off", timelimit="y", backend="lite")
        elif kind == "answers":
            gen = ddgs.answers(keywords)
        elif kind == "images":
            gen = ddgs.images(keywords, safesearch="Off", timelimit=None)
        elif kind == "videos":
            gen = ddgs.videos(keywords, safesearch="Off", timelimit=None, resolution="high")
        else:
            raise ValueError(f"Unsupported search kind: {kind}")

        for r in islice(gen, max_results):
            results.append(r)

    return results


@app.route("/", methods=["GET"])
def root():
    """
    Simple service description for OpenClaw ecosystem.
    """
    return jsonify(
        {
            "name": "openclaw-search-proxy",
            "description": "Search proxy API for OpenClaw skills, powered by DuckDuckGo.",
            "endpoints": {
                "text": "/v1/search/text",
                "answers": "/v1/search/answers",
                "images": "/v1/search/images",
                "videos": "/v1/search/videos",
            },
            "legacy_endpoints": ["/search", "/searchAnswers", "/searchImages", "/searchVideos"],
        }
    )


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/v1/search/text", methods=["GET", "POST"])
def search_text():
    keywords, max_results = _extract_query_and_limit()
    results = _search_ddg("text", keywords, max_results)
    return jsonify({"query": keywords, "type": "text", "results": results})


@app.route("/v1/search/answers", methods=["GET", "POST"])
def search_answers():
    keywords, max_results = _extract_query_and_limit()
    results = _search_ddg("answers", keywords, max_results)
    return jsonify({"query": keywords, "type": "answers", "results": results})


@app.route("/v1/search/images", methods=["GET", "POST"])
def search_images():
    keywords, max_results = _extract_query_and_limit()
    results = _search_ddg("images", keywords, max_results)
    return jsonify({"query": keywords, "type": "images", "results": results})


@app.route("/v1/search/videos", methods=["GET", "POST"])
def search_videos():
    keywords, max_results = _extract_query_and_limit()
    results = _search_ddg("videos", keywords, max_results)
    return jsonify({"query": keywords, "type": "videos", "results": results})


# Backwards-compatible legacy routes
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
    app.run(host="0.0.0.0", port=8000)
