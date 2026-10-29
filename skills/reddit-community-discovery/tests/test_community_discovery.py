from datetime import date
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import community_discovery as discovery


class CommunityDiscoveryTests(unittest.TestCase):
    def test_clean_and_parse_unique_names(self):
        subs = discovery.parse_unique(
            ["r/OpenRouter", "/r/openrouter/", "LocalLLaMA, opencode"],
            discovery.clean_subreddit,
        )
        self.assertEqual(subs, ["OpenRouter", "LocalLLaMA", "opencode"])
        keywords = discovery.parse_unique(["writing, draft", "Writing"], discovery.clean_keyword)
        self.assertEqual(keywords, ["writing", "draft"])
        with self.assertRaises(ValueError):
            discovery.clean_subreddit("bad name!")
        with self.assertRaises(ValueError):
            discovery.clean_author("[deleted]")
        with self.assertRaises(ValueError):
            discovery.clean_keyword("   ")

    def test_extract_authors_filters_removed_and_ranks_by_discussion(self):
        posts = [
            {"author": "[deleted]", "num_comments": 20, "selftext": "hello"},
            {"author": "AutoModerator", "num_comments": 15, "selftext": "pinned"},
            {"author": "spam_bot", "num_comments": 10, "selftext": "[removed]"},
            {"author": "mod_nuked", "num_comments": 1, "removed_by_category": "moderator"},
            {"author": "promo_poster", "num_comments": 0, "selftext": "check out my app"},
            {"author": "bob-builder", "num_comments": 4, "score": 10, "selftext": "real question"},
            {
                "author": "alice_dev",
                "num_comments": 18,
                "score": 30,
                "removed_by_category": "automod_filtered",
                "selftext": "deep workflow",
            },
            {"author": "ALICE_DEV", "num_comments": 6, "score": 5, "selftext": "followup"},
        ]
        self.assertEqual(
            discovery.extract_authors(posts, limit=3, min_comments=2),
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

    def test_format_subreddit_peek_filters_removed_keywords_and_ranks_posts(self):
        meta_rows = [
            {
                "display_name": "ClaudeAI",
                "title": "ClaudeAI",
                "description": "Sister subs: r/PromptEngineering and /r/LocalLLaMA",
                "public_description": "",
                "subscribers": 900000,
            }
        ]
        latest_rows = [
            {
                "id": "1newest",
                "subreddit": "ClaudeAI",
                "subreddit_subscribers": 1235752,
                "title": "Brand new post",
                "selftext": "[removed]",
            }
        ]
        post_rows = [
            {
                "id": "1removed",
                "subreddit": "ClaudeAI",
                "title": "Spam writing tool",
                "author": "spammer",
                "score": 1,
                "num_comments": 0,
                "selftext": "[removed]",
            },
            {
                "id": "1coding",
                "subreddit": "ClaudeAI",
                "title": "Claude Code terminal shortcut",
                "author": "dev_one",
                "score": 50,
                "num_comments": 22,
                "selftext": "Avoid overwriting config files.",
            },
            {
                "id": "1low",
                "subreddit": "ClaudeAI",
                "title": "Quick writing prompt question",
                "author": "writer_a",
                "score": 3,
                "num_comments": 4,
                "created_utc": 1760000000,
                "selftext": "How do you structure outlines?",
            },
            {
                "id": "1high",
                "subreddit": "ClaudeAI",
                "title": "Response style feels jarring for prose",
                "author": "writer_b",
                "score": 25,
                "num_comments": 35,
                "link_flair_text": "Discussion",
                "created_utc": 1760003600,
                "selftext": "My long-form writing workflow\n\nneeds less corporate tone.",
                "permalink": "/r/ClaudeAI/comments/1high/response_style_feels_jarring/",
            },
        ]
        peek = discovery.format_subreddit_peek(
            "ClaudeAI",
            meta_rows,
            post_rows,
            latest_rows=latest_rows,
            keywords=["writing", "prose"],
            max_posts=5,
        )
        self.assertEqual(peek["name"], "ClaudeAI")
        self.assertEqual(peek["subscribers"], 1235752)
        self.assertEqual(peek["sampled_count"], 4)
        self.assertEqual(peek["surviving_count"], 3)
        self.assertEqual(peek["discussed_count"], 3)
        self.assertEqual(peek["matched_count"], 2)
        self.assertEqual(peek["related_subreddits"], ["PromptEngineering", "LocalLLaMA"])
        self.assertEqual([p["id"] for p in peek["recent_posts"]], ["t3_1high", "t3_1low"])
        first = peek["recent_posts"][0]
        self.assertEqual(first["snippet"], "My long-form writing workflow needs less corporate tone.")
        self.assertEqual(first["url"], "https://www.reddit.com/r/ClaudeAI/comments/1high/response_style_feels_jarring/")

    def test_cli_parser_default_after_and_write_output(self):
        self.assertIsInstance(date.fromisoformat(discovery.default_after_date()), date)
        parser = discovery.build_parser()
        expand_args = parser.parse_args(
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
        self.assertEqual(expand_args.command, "expand")
        self.assertEqual(expand_args.seed_subreddit, ["r/openrouter"])
        self.assertEqual(expand_args.settle_days, 3)
        self.assertFalse(expand_args.all_time)

        peek_args = parser.parse_args(
            [
                "peek",
                "--subreddit",
                "ClaudeAI",
                "--keyword",
                "writing",
                "--sample-pool",
                "80",
            ]
        )
        self.assertEqual(peek_args.keyword, ["writing"])
        self.assertEqual(peek_args.sample_pool, 80)

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "nested" / "result.json"
            discovery.write_output(out, {"ok": True})
            self.assertEqual(json.loads(out.read_text(encoding="utf-8")), {"ok": True})


if __name__ == "__main__":
    unittest.main()
