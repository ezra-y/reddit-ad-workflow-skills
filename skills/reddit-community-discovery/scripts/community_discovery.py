import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = "https://arctic-shift.photon-reddit.com/api"
IGNORED_AUTHORS = {"", "[deleted]", "[removed]", "automoderator"}
IGNORED_SUBREDDITS = {"all", "popular", "random", "friends", "mod"}
REMOVED_MARKERS = {"[removed]", "[deleted]"}
SUBREDDIT_LINK_RE = re.compile(r"(?<![A-Za-z0-9_])/?r/([A-Za-z0-9_]{2,21})\b")


def clean_subreddit(value):
    name = str(value).strip().removeprefix("/r/").removeprefix("r/").strip("/")
    if not name or not name.isascii() or not all(ch.isalnum() or ch == "_" for ch in name):
        raise ValueError(f"无效的社区名称：{value}")
    return name


def clean_author(value):
    name = str(value).strip().removeprefix("/u/").removeprefix("u/").strip("/")
    if not name or name.lower() in IGNORED_AUTHORS:
        raise ValueError(f"无效的 Reddit 作者名：{value}")
    if not name.isascii() or not all(ch.isalnum() or ch in "_-" for ch in name):
        raise ValueError(f"无效的 Reddit 作者名：{value}")
    return name


def clean_keyword(value):
    word = str(value).strip()
    if not word:
        raise ValueError("关键词不能为空")
    return word


def parse_unique(values, cleaner):
    seen = {}
    for raw in values or ():
        for part in str(raw).split(","):
            if part.strip():
                cleaned = cleaner(part)
                seen.setdefault(cleaned.lower(), cleaned)
    return list(seen.values())


def request_data(endpoint, params):
    clean_params = {key: value for key, value in params.items() if value is not None and value != ""}
    url = f"{API}{endpoint}?{urlencode(clean_params)}"
    request = Request(url, headers={"User-Agent": "reddit-community-discovery/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Arctic Shift 请求失败 (HTTP {exc.code}) {url} -> {detail}") from exc
    data = payload.get("data")
    if not isinstance(data, list):
        raise RuntimeError(f"Arctic Shift 返回异常 {url} -> {payload}")
    return data


def is_removed_record(record):
    title = str(record.get("title") or "").strip().lower()
    if "[ removed" in title or title in REMOVED_MARKERS:
        return True
    for field in ("selftext", "body"):
        if field in record and str(record.get(field) or "").strip().lower() in REMOVED_MARKERS:
            return True
    # Arctic Shift 二次抓取已过审正文后仍可能残留 automod_filtered，仅对无正文且低互动帖参考该字段
    has_text = bool(str(record.get("selftext") or record.get("body") or "").strip())
    if not has_text and record.get("removed_by_category") and int(record.get("num_comments") or 0) <= 2:
        return True
    return False


def extract_authors(records, *, limit=None, min_comments=0):
    # 跳过已被删除的内容与机器人，按评论互动数优先提取真实参与讨论的作者
    candidates = [
        row
        for row in records
        if not is_removed_record(row)
        and int(row.get("num_comments") or 0) >= min_comments
    ]
    if min_comments > 0:
        candidates.sort(
            key=lambda row: (int(row.get("num_comments") or 0), int(row.get("score") or 0)),
            reverse=True,
        )
    seen = {}
    for row in candidates:
        author = str(row.get("author") or "").strip()
        if not author or author.lower() in IGNORED_AUTHORS:
            continue
        seen.setdefault(author.lower(), author)
        if limit is not None and len(seen) >= limit:
            break
    return list(seen.values())


def extract_related_subreddits(*texts, exclude=()):
    # 从社区侧边栏 description 与简介中提取版主整理的关联 r/ 社区
    excluded = {clean_subreddit(name).lower() for name in exclude} | IGNORED_SUBREDDITS
    seen = {}
    for text in texts:
        for match in SUBREDDIT_LINK_RE.finditer(str(text or "")):
            sub = match.group(1)
            key = sub.lower()
            if key in excluded or key.startswith("u_"):
                continue
            seen.setdefault(key, sub)
    return list(seen.values())


def summarize_overlap(
    author_subreddits,
    *,
    seeds=(),
    sidebar_links=None,
    prefix_matches=(),
    min_authors=2,
    limit=20,
):
    seed_keys = {clean_subreddit(name).lower() for name in seeds}
    buckets = {}

    def ensure_bucket(sub):
        key = sub.lower()
        return key, buckets.setdefault(
            key,
            {
                "name": sub,
                "authors": [],
                "interaction_total": 0,
                "sidebar_from": [],
                "prefix_matched": False,
                "subscribers": None,
                "public_description": "",
            },
        )

    for author, rows in author_subreddits.items():
        seen_in_author = set()
        for row in rows:
            sub = str(row.get("subreddit") or "").strip()
            if not sub or sub.lower() in IGNORED_SUBREDDITS or sub.lower().startswith("u_"):
                continue
            key, bucket = ensure_bucket(sub)
            if key in seen_in_author:
                continue
            seen_in_author.add(key)
            bucket["authors"].append(author)
            bucket["interaction_total"] += int(row.get("count") or 0)

    for seed_name, related_list in (sidebar_links or {}).items():
        for sub in related_list:
            _, bucket = ensure_bucket(sub)
            if seed_name not in bucket["sidebar_from"]:
                bucket["sidebar_from"].append(seed_name)

    for meta in prefix_matches:
        sub = str(meta.get("display_name") or meta.get("subreddit") or "").strip()
        if not sub or sub.lower() in IGNORED_SUBREDDITS:
            continue
        _, bucket = ensure_bucket(sub)
        bucket["name"] = sub
        bucket["prefix_matched"] = True
        if meta.get("subscribers") is not None:
            bucket["subscribers"] = int(meta["subscribers"])
        if meta.get("public_description"):
            bucket["public_description"] = str(meta["public_description"]).strip()

    discovered = []
    seed_hits = []
    for key, bucket in buckets.items():
        entry = {
            "name": bucket["name"],
            "url": f"https://www.reddit.com/r/{bucket['name']}/",
            "matched_authors": len(bucket["authors"]),
            "authors": bucket["authors"],
            "interaction_total": bucket["interaction_total"],
            "sidebar_from": bucket["sidebar_from"],
            "prefix_matched": bucket["prefix_matched"],
            "subscribers": bucket["subscribers"],
            "public_description": bucket["public_description"],
        }
        if key in seed_keys:
            seed_hits.append(entry)
            continue
        if entry["matched_authors"] >= min_authors or entry["sidebar_from"] or entry["prefix_matched"]:
            discovered.append(entry)

    sort_key = lambda item: (
        -item["matched_authors"],
        -len(item["sidebar_from"]),
        -item["interaction_total"],
        not item["prefix_matched"],
        -(item["subscribers"] or 0),
        item["name"].lower(),
    )
    discovered.sort(key=sort_key)
    seed_hits.sort(key=sort_key)
    return {
        "queried_authors": list(author_subreddits.keys()),
        "seed_subreddits": seed_hits,
        "discovered": discovered[:limit],
    }


def collapse_text(text, max_chars=240):
    compact = " ".join(str(text or "").split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip() + "…"


def post_url(post, subreddit):
    permalink = str(post.get("permalink") or "").strip()
    if permalink.startswith("http://") or permalink.startswith("https://"):
        return permalink
    if permalink:
        return "https://www.reddit.com" + (permalink if permalink.startswith("/") else "/" + permalink)
    post_id = str(post.get("id") or "").removeprefix("t3_")
    return f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/"


def matches_keywords(post, keywords):
    if not keywords:
        return True
    haystack = f"{post.get('title') or ''}\n{post.get('selftext') or ''}"
    return any(re.search(rf"\b{re.escape(word)}\b", haystack, re.IGNORECASE) for word in keywords)


def format_subreddit_peek(
    requested_name,
    meta_rows,
    post_rows,
    *,
    latest_rows=(),
    keywords=(),
    max_posts=5,
):
    meta = meta_rows[0] if meta_rows else {}
    all_posts = list(latest_rows) + list(post_rows)
    name = (
        str(all_posts[0]["subreddit"]).strip()
        if all_posts and all_posts[0].get("subreddit")
        else str(meta.get("display_name") or requested_name).strip()
    )
    # 新建社区可能尚未进入 subreddits 索引，优先读取最新帖子携带的实时订阅人数
    subscribers = next(
        (
            int(post["subreddit_subscribers"])
            for post in all_posts
            if post.get("subreddit_subscribers") is not None
        ),
        int(meta["subscribers"]) if meta.get("subscribers") is not None else None,
    )
    related_subreddits = extract_related_subreddits(
        meta.get("description"),
        meta.get("public_description"),
        exclude=[name],
    )
    surviving = [post for post in post_rows if not is_removed_record(post)]
    discussed_count = sum(1 for post in surviving if int(post.get("num_comments") or 0) >= 2)
    matched = [post for post in surviving if matches_keywords(post, keywords)]
    matched.sort(
        key=lambda post: (int(post.get("num_comments") or 0), int(post.get("score") or 0)),
        reverse=True,
    )

    recent_posts = []
    for post in matched[:max_posts]:
        created_utc = post.get("created_utc")
        created_at = (
            datetime.fromtimestamp(int(created_utc), tz=timezone.utc).isoformat()
            if created_utc is not None
            else None
        )
        raw_id = str(post.get("id") or "").removeprefix("t3_")
        recent_posts.append(
            {
                "id": f"t3_{raw_id}" if raw_id else "",
                "title": str(post.get("title") or "").strip(),
                "author": str(post.get("author") or "").strip(),
                "score": post.get("score"),
                "num_comments": post.get("num_comments"),
                "flair": str(post.get("link_flair_text") or "").strip(),
                "created_at": created_at,
                "snippet": collapse_text(post.get("selftext") or ""),
                "url": post_url(post, name),
            }
        )
    return {
        "name": name,
        "url": f"https://www.reddit.com/r/{name}/",
        "title": str(meta.get("title") or "").strip(),
        "public_description": str(meta.get("public_description") or "").strip(),
        "subscribers": subscribers,
        "sampled_count": len(post_rows),
        "surviving_count": len(surviving),
        "discussed_count": discussed_count,
        "matched_count": len(matched),
        "related_subreddits": related_subreddits,
        "recent_posts": recent_posts,
    }


def write_output(out_path, payload):
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if out_path:
        target = Path(out_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


def days_ago_date(days):
    return (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()


def default_after_date(days=180):
    return days_ago_date(days)


def run_expand(args):
    seeds = parse_unique(args.seed_subreddit, clean_subreddit)
    authors = parse_unique(args.author, clean_author)
    prefixes = parse_unique(args.prefix, clean_subreddit)
    if not seeds and not authors and not prefixes:
        raise ValueError("请至少提供 --seed-subreddit、--author 或 --prefix 之一")
    if not 1 <= args.seed_posts <= 100:
        raise ValueError("--seed-posts 必须在 1 到 100 之间")

    settled_before = days_ago_date(args.settle_days) if args.settle_days > 0 else None
    author_pool = {author.lower(): author for author in authors}
    sidebar_links = {}
    for sub in seeds:
        meta_rows = request_data("/subreddits/search", {"subreddit": sub, "limit": 1})
        if meta_rows:
            sidebar_links[sub] = extract_related_subreddits(
                meta_rows[0].get("description"),
                meta_rows[0].get("public_description"),
                exclude=[sub],
            )
        posts = request_data(
            "/posts/search",
            {"subreddit": sub, "before": settled_before, "limit": args.seed_posts, "sort": "desc"},
        )
        seed_authors = extract_authors(posts, limit=args.authors_per_seed, min_comments=2)
        if len(seed_authors) < args.authors_per_seed:
            comments = request_data(
                "/comments/search",
                {"subreddit": sub, "before": settled_before, "limit": args.seed_posts, "sort": "desc"},
            )
            for commenter in extract_authors(comments, limit=args.authors_per_seed):
                if commenter.lower() not in {name.lower() for name in seed_authors}:
                    seed_authors.append(commenter)
                if len(seed_authors) >= args.authors_per_seed:
                    break
        for author in seed_authors:
            author_pool.setdefault(author.lower(), author)

    # 默认限定近期窗口，聚焦当前活跃社区并避免高发帖老账号触发归档接口超时
    after = None if args.all_time else (args.after or default_after_date())
    all_authors = list(author_pool.values())
    author_subreddits = {}
    for author in all_authors:
        params = {"author": author, "limit": 50}
        if after:
            params["after"] = after
        author_subreddits[author] = request_data("/users/interactions/subreddits", params)

    prefix_matches = []
    for prefix in prefixes:
        prefix_matches.extend(
            request_data(
                "/subreddits/search",
                {"subreddit_prefix": prefix.lower(), "limit": args.prefix_limit},
            )
        )

    min_authors = args.min_authors if args.min_authors is not None else (2 if len(all_authors) >= 2 else 1)
    result = summarize_overlap(
        author_subreddits,
        seeds=seeds,
        sidebar_links=sidebar_links,
        prefix_matches=prefix_matches,
        min_authors=min_authors,
        limit=args.limit,
    )
    result["after"] = after
    return result


def run_peek(args):
    subreddits = parse_unique(args.subreddit, clean_subreddit)
    keywords = parse_unique(args.keyword, clean_keyword)
    if not subreddits:
        raise ValueError("请至少提供一个 --subreddit")
    if not 1 <= args.sample_pool <= 100:
        raise ValueError("--sample-pool 必须在 1 到 100 之间")

    settled_before = days_ago_date(args.settle_days) if args.settle_days > 0 else None
    items = []
    for sub in subreddits:
        meta_rows = request_data("/subreddits/search", {"subreddit": sub, "limit": 1})
        latest_rows = (
            request_data("/posts/search", {"subreddit": sub, "limit": 1, "sort": "desc"})
            if settled_before
            else []
        )
        post_rows = request_data(
            "/posts/search",
            {"subreddit": sub, "before": settled_before, "limit": args.sample_pool, "sort": "desc"},
        )
        items.append(
            format_subreddit_peek(
                sub,
                meta_rows,
                post_rows,
                latest_rows=latest_rows,
                keywords=keywords,
                max_posts=args.posts,
            )
        )
    return {"subreddits": items}


def build_parser():
    parser = argparse.ArgumentParser(description="按目标人群活跃足迹、侧边栏关联与近期真帖发现 Reddit 社区")
    subparsers = parser.add_subparsers(dest="command", required=True)

    expand = subparsers.add_parser("expand", help="顺着目标作者或种子社区发现共同活跃与侧边栏关联社区")
    expand.add_argument("--seed-subreddit", action="append", default=[], help="已知种子社区（可重复传入）")
    expand.add_argument("--author", action="append", default=[], help="聊过目标场景的真实作者（可重复传入）")
    expand.add_argument("--prefix", action="append", default=[], help="按社区名称前缀补充搜索（可重复传入）")
    expand.add_argument("--after", help="只统计该日期之后的作者活跃足迹（YYYY-MM-DD，默认近半年）")
    expand.add_argument("--all-time", action="store_true", help="统计全历史作者活跃足迹")
    expand.add_argument("--settle-days", type=int, default=3, help="跳过最近几天的未沉淀新帖以排除秒删与零互动帖")
    expand.add_argument("--seed-posts", type=int, default=50, help="每个种子社区抽样的近期帖子与评论数（1-100）")
    expand.add_argument("--authors-per-seed", type=int, default=12, help="每个种子社区最多提取的独立活跃作者数")
    expand.add_argument("--prefix-limit", type=int, default=15, help="每个前缀最多返回的社区数")
    expand.add_argument("--min-authors", type=int, default=None, help="至少多少位目标作者共同活跃才保留")
    expand.add_argument("--limit", type=int, default=20, help="最多返回的候选社区数")
    expand.add_argument("--out", help="输出 JSON 文件路径（省略则直接打印）")

    peek = subparsers.add_parser("peek", help="快速查看候选社区简介、侧边栏关联社区、订阅规模与高互动代表帖")
    peek.add_argument("--subreddit", action="append", required=True, help="候选社区名称（可重复传入）")
    peek.add_argument("--keyword", action="append", default=[], help="本地筛选帖子标题与正文的关键词（可重复传入）")
    peek.add_argument("--posts", type=int, default=5, help="每个社区返回的高互动代表帖条数")
    peek.add_argument("--sample-pool", type=int, default=60, help="每个社区按时间索引抽样的近期帖子池大小（1-100）")
    peek.add_argument("--settle-days", type=int, default=3, help="往前留出几天沉淀期以统计真实评论互动（设为 0 则看最新帖）")
    peek.add_argument("--out", help="输出 JSON 文件路径（省略则直接打印）")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    payload = run_expand(args) if args.command == "expand" else run_peek(args)
    write_output(args.out, payload)


if __name__ == "__main__":
    main()
