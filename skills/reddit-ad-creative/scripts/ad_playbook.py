import argparse
import json
from pathlib import Path


LIBRARY_DIR = Path(__file__).resolve().parent.parent / "library"

LIBRARY_FILES = {
    "psychology": ("抓心心理机制库", "psychology_hooks.json"),
    "visual": ("视觉叙事与构图技巧库", "visual_templates.json"),
    "headline": ("标题与文案修辞库", "headline_devices.json"),
    "persuasion": ("切入定位与破防说服库", "persuasion_tactics.json"),
}


def load_libraries() -> dict[str, list[dict]]:
    # 读取四个 JSON 理论卡片库
    return {
        key: json.loads((LIBRARY_DIR / filename).read_text(encoding="utf-8"))
        for key, (_, filename) in LIBRARY_FILES.items()
    }


def build_card_index(libraries: dict[str, list[dict]]) -> dict[str, tuple[str, dict]]:
    # 建立 card_id 到 (所属库名称, 卡片字典) 的全局索引
    index: dict[str, tuple[str, dict]] = {}
    for lib_key, cards in libraries.items():
        for card in cards:
            card_id = card["id"]
            if card_id in index:
                raise ValueError(f"重复的卡片 ID: {card_id}")
            index[card_id] = (lib_key, card)
    return index


def cmd_catalog(args: argparse.Namespace) -> None:
    libraries = load_libraries()
    target_keys = list(LIBRARY_FILES.keys()) if args.library == "all" else [args.library]

    for key in target_keys:
        title, _ = LIBRARY_FILES[key]
        cards = libraries[key]
        print(f"=== {title} ===")
        current_dimension = None
        for card in cards:
            dim = card["dimension_name"]
            if dim != current_dimension:
                current_dimension = dim
                print(f"\n【{current_dimension}】")
            print(f"  - {card['id']} | {card['name']}")
            print(f"    适用场景: {card['when_to_use']}")
        print()


def cmd_show(args: argparse.Namespace) -> None:
    libraries = load_libraries()
    index = build_card_index(libraries)

    selected_cards = []
    for card_id in args.card_ids:
        if card_id not in index:
            raise KeyError(f"未找到卡片 ID: {card_id}。请先运行 catalog 查看有效 ID。")
        _, card = index[card_id]
        selected_cards.append(card)

    if args.json:
        print(json.dumps(selected_cards, ensure_ascii=False, indent=2))
        return

    for card in selected_cards:
        print(f"## [{card['id']}] {card['name']}")
        print(f"- **所属维度**: {card['dimension_name']}")
        print(f"- **理论出处**: {card['source']}")
        print(f"- **一句话摘要**: {card['summary']}")
        print(f"- **何时调用 (when_to_use)**: {card['when_to_use']}")
        print(f"- **底层原理 (principle)**: {card['principle']}")
        print(f"- **画面用法 (visual_usage)**: {card['visual_usage']}")
        print(f"- **文案用法 (copy_usage)**: {card['copy_usage']}")
        print(f"- **误用注意点 (pitfalls)**: {card['pitfalls']}")
        print(f"- **推荐搭配卡片 (pairs_with)**: {', '.join(card['pairs_with'])}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Reddit 广告创意理论卡片检索工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_catalog = subparsers.add_parser("catalog", help="列出理论与技巧卡片的紧凑目录")
    p_catalog.add_argument(
        "--library",
        choices=["all", "psychology", "visual", "headline", "persuasion"],
        default="all",
        help="按需筛选指定技巧库",
    )
    p_catalog.set_defaults(func=cmd_catalog)

    p_show = subparsers.add_parser("show", help="按卡片 ID 展开完整原理、画面用法、文案用法与注意点")
    p_show.add_argument("card_ids", nargs="+", help="要查看的卡片 ID")
    p_show.add_argument("--json", action="store_true", help="以 JSON 格式输出卡片详情")
    p_show.set_defaults(func=cmd_show)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
