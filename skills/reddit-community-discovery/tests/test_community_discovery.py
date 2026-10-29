from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import community_discovery as discovery


class CommunityDiscoveryTests(unittest.TestCase):
    def test_clean_and_parse_unique_names(self):
        subs = discovery.parse_unique(
            ["r/OpenRouter", "/r/openrouter/", "LocalLLaMA, opencode"],
            discovery.clean_subreddit,
        )
        self.assertEqual(subs, ["OpenRouter", "LocalLLaMA", "opencode"])
        with self.assertRaises(ValueError):
            discovery.clean_subreddit("bad name!")
        with self.assertRaises(ValueError):
            discovery.clean_author("[deleted]")

    def test_extract_authors_skips_deleted_and_automod_and_deduplicates(self):
        posts = [
            {"author": "[deleted]"},
            {"author": "AutoModerator"},
            {"author": "alice_dev"},
            {"author": "ALICE_DEV"},
            {"author": "bob-builder"},
            {"author": "carol_ops"},
        ]
        self.assertEqual(
            discovery.extract_authors(posts, limit=2),
            ["alice_dev", "bob-builder"],
        )

    def test_extract_related_subreddits_deduplicates_and_excludes_self(self):
        sidebar = """
        Related communities:
        - r/SmallBusiness
        - /r/Bookkeeping and r/bookkeeping
        - https://www.reddit.com/r/Entrepreneur/wiki/index
        - r/all and r/u_spammer
        """
        related = discovery.extract_related_subreddits(sidebar, exclude=["smallbusiness"])
        self.assertEqual(related, ["Bookkeeping", "Entrepreneur"])

    def test_summarize_overlap_combines_authors_sidebars_and_prefixes(self):
        author_subreddits = {
            "alice": [
                {"subreddit": "openrouter", "count": 6},
                {"subreddit": "opencode", "count": 4},
                {"subreddit": "LocalLLaMA", "count": 10},
                {"subreddit": "gardening", "count": 25},
                {"subreddit": "all", "count": 50},
            ],
            "bob": [
                {"subreddit": "openrouter", "count": 3},
                {"subreddit": "opencode", "count": 5},
                {"subreddit": "codex", "count": 2},
            ],
            "carol": [
                {"subreddit": "opencode", "count": 2},
                {"subreddit": "LocalLLaMA", "count": 3},
            ],
        }
        sidebar_links = {"openrouter": ["LocalLLaMA", "SillyTavernAI"]}
        prefix_matches = [
            {
                "display_name": "LLMDevs",
                "subscribers": 42000,
                "public_description": "Building production apps with LLMs.",
            }
        ]
        result = discovery.summarize_overlap(
            author_subreddits,
            seeds=["r/openrouter"],
            sidebar_links=sidebar_links,
            prefix_matches=prefix_matches,
            min_authors=2,
            limit=10,
        )

        self.assertEqual([item["name"] for item in result["seed_subreddits"]], ["openrouter"])
        self.assertEqual(
            [item["name"] for item in result["discovered"]],
            ["opencode", "LocalLLaMA", "SillyTavernAI", "LLMDevs"],
        )
        by_name = {item["name"]: item for item in result["discovered"]}
        self.assertEqual(by_name["opencode"]["matched_authors"], 3)
        self.assertEqual(by_name["LocalLLaMA"]["sidebar_from"], ["openrouter"])
        self.assertEqual(by_name["SillyTavernAI"]["sidebar_from"], ["openrouter"])

    def test_format_subreddit_peek_reads_live_subscribers_and_sidebar_links(self):
        meta_rows = [
            {
                "display_name": "opencode",
                "title": "OpenCode",
                "description": "Sister subs: r/codex and /r/LocalLLaMA",
                "public_description": "",
            }
        ]
        post_rows = [
            {
                "id": "1abcde",
                "subreddit": "opencode",
                "subreddit_subscribers": 55189,
                "title": "Silent Charges: Failed API Calls Eating Credits",
                "author": "alice_dev",
                "score": 42,
                "num_comments": 19,
                "link_flair_text": "Discussion",
                "created_utc": 1760000000,
                "selftext": "Every time a provider returns 502\n\nwe still get billed.",
                "permalink": "/r/opencode/comments/1abcde/silent_charges/",
            }
        ]
        peek = discovery.format_subreddit_peek("opencode", meta_rows, post_rows)
        self.assertEqual(peek["name"], "opencode")
        self.assertEqual(peek["subscribers"], 55189)
        self.assertEqual(peek["related_subreddits"], ["codex", "LocalLLaMA"])
        self.assertEqual(len(peek["recent_posts"]), 1)
        first = peek["recent_posts"][0]
        self.assertEqual(first["id"], "t3_1abcde")
        self.assertEqual(first["snippet"], "Every time a provider returns 502 we still get billed.")
        self.assertEqual(first["url"], "https://www.reddit.com/r/opencode/comments/1abcde/silent_charges/")

    def test_cli_parser_default_after_and_write_output(self):
        self.assertIsInstance(date.fromisoformat(discovery.default_after_date()), date)
        parser = discovery.build_parser()
        args = parser.parse_args(
            [
                "expand",
                "--seed-subreddit",
                "r/openrouter",
                "--author",
                "u/alice_dev",
                "--prefix",
                "llm",
            ]
        )
        self.assertEqual(args.command, "expand")
        self.assertEqual(args.seed_subreddit, ["r/openrouter"])
        self.assertFalse(args.all_time)

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "nested" / "result.json"
            discovery.write_output(out, {"ok": True})
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), {"ok": True})


if __name__ == "__main__":
    unittest.main()
