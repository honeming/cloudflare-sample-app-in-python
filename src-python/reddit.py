"""
Reach out to the Reddit API, and get the first page of results from
r/aww. Filter out posts without readily available images or videos,
and return a random result.
"""

import json
import random

from js import Object, fetch
from pyodide.ffi import to_js

REDDIT_URL = "https://www.reddit.com/r/aww/hot.json"


async def get_cute_url():
    response = await fetch(
        REDDIT_URL,
        headers=to_js(
            {"User-Agent": "justinbeckwith:awwbot:v1.0.0 (by /u/justinblat)"},
            dict_converter=Object.fromEntries,
        ),
    )

    if not response.ok:
        error_text = f"Error fetching {response.url}: {response.status} {response.statusText}"
        try:
            error = await response.text()
            if error:
                error_text = f"{error_text} \n\n {error}"
        except Exception:
            pass
        raise Exception(error_text)

    data = json.loads(await response.text())
    posts = []
    for post in data["data"]["children"]:
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
