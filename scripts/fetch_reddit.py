"""Pull a fresh, unused story from the configured subreddits."""
import json
import logging
import os

import praw

import config

logger = logging.getLogger(__name__)


def _load_used_ids() -> set:
    path = config.STATE_DIR / "used_posts.json"
    if not path.exists():
        return set()
    return set(json.loads(path.read_text(encoding="utf-8")))


def _mark_used(post_id: str) -> None:
    config.STATE_DIR.mkdir(parents=True, exist_ok=True)
    path = config.STATE_DIR / "used_posts.json"
    used = _load_used_ids()
    used.add(post_id)
    path.write_text(json.dumps(sorted(used)), encoding="utf-8")


def _client() -> praw.Reddit:
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=config.REDDIT_USER_AGENT,
    )


def fetch_story() -> dict:
    """Return the first eligible, previously-unused post as a dict, or raise if none found."""
    reddit = _client()
    used_ids = _load_used_ids()

    for subreddit_name in config.SUBREDDITS:
        subreddit = reddit.subreddit(subreddit_name)
        if config.POST_SORT == "top":
            listing = subreddit.top(time_filter=config.POST_TIME_FILTER, limit=config.POSTS_TO_FETCH_PER_RUN)
        elif config.POST_SORT == "new":
            listing = subreddit.new(limit=config.POSTS_TO_FETCH_PER_RUN)
        else:
            listing = subreddit.hot(limit=config.POSTS_TO_FETCH_PER_RUN)

        for post in listing:
            if post.id in used_ids:
                continue
            if post.stickied or post.over_18:
                continue
            body = (post.selftext or "").strip()
            if not (config.MIN_BODY_CHARS <= len(body) <= config.MAX_BODY_CHARS):
                continue
            if post.score < config.MIN_UPVOTES:
                continue

            logger.info("Selected r/%s post %s (%d upvotes): %s", subreddit_name, post.id, post.score, post.title)
            _mark_used(post.id)
            return {
                "id": post.id,
                "subreddit": subreddit_name,
                "title": post.title,
                "body": body,
                "author": str(post.author) if post.author else "[deleted]",
                "score": post.score,
                "url": f"https://reddit.com{post.permalink}",
            }

    raise RuntimeError(
        "No eligible unused post found across configured subreddits. "
        "Try lowering MIN_UPVOTES/MIN_BODY_CHARS or adding more subreddits in config.py."
    )
