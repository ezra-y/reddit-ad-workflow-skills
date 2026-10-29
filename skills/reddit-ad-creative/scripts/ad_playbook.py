import argparse
import json
from pathlib import Path


LIBRARY_DIR = Path(__file__).resolve().parent.parent / "library"
MAX_SHOW_CARDS = 6

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
        print(f"[{title}]")
        for card in libraries[key]:
            short_name = card["name"].split("（")[0]
            wtu = card["when_to_use"].rstrip("。").removesuffix("时调用")
            print(f"{card['id']}: {short_name}｜{wtu}")


def cmd_show(args: argparse.Namespace) -> None:
    if len(args.card_ids) > MAX_SHOW_CARDS:
        raise ValueError(
            f"单次最多展开 {MAX_SHOW_CARDS} 张卡片（当前传入 {len(args.card_ids)} 张）。"
            "每个方向只需精选 1~3 张最契合的核心卡，避免套用过多规则磨平创意。"
        )

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
        print(f"- 所属维度: {card['dimension_name']} | 出处: {card['source']}")
        print(f"- 何时调用: {card['when_to_use']}")
        print(f"- 底层原理: {card['principle']}")
        print(f"- 画面启发: {card['visual_usage']}")
        print(f"- 文案启发: {card['copy_usage']}")
        print(f"- 注意事项: {card['pitfalls']}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Reddit 广告创意理论卡片检索工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_catalog = subparsers.add_parser("catalog", help="单屏列出全部理论卡片的名称与适用场景")
    p_catalog.add_argument(
        "--library",
        choices=["all", "psychology", "visual", "headline", "persuasion"],
        default="all",
        help="按需筛选指定技巧库",
    )
    p_catalog.set_defaults(func=cmd_catalog)

    p_show = subparsers.add_parser("show", help="按卡片 ID 展开精选卡片详情（单次最多 6 张）")
    p_show.add_argument("card_ids", nargs="+", help="要查看的卡片 ID（1~6 个）")
    p_show.add_argument("--json", action="store_true", help="以 JSON 格式输出卡片详情")
    p_show.set_defaults(func=cmd_show)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
