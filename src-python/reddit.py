"""
Reach out to the Reddit API, and get the first page of results from
r/aww. Filter out posts without readily available images or videos,
and return a random result.
"""

import json
import random
import urllib.request

REDDIT_URL = "https://www.reddit.com/r/aww/hot.json"
USER_AGENT = "awwbot:vercel-python:v1.0.0"


def get_cute_url():
    request = urllib.request.Request(
        REDDIT_URL,
        headers={"User-Agent": USER_AGENT},
    )

    with urllib.request.urlopen(request, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))

    posts = []
    for post in data.get("data", {}).get("children", []):
        post_data = post.get("data", {})
        if post_data.get("is_gallery"):
            continue
        url = (
            (post_data.get("media") or {}).get("reddit_video", {}).get("fallback_url")
            or (post_data.get("secure_media") or {})
            .get("reddit_video", {})
            .get("fallback_url")
            or post_data.get("url")
        )
        if url:
            posts.append(url)

    if not posts:
        return None

    return random.choice(posts)
