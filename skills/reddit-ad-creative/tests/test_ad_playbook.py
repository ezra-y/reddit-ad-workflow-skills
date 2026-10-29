from pathlib import Path
import subprocess
import sys

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import ad_playbook

REQUIRED_CARD_FIELDS = (
    "id",
    "category",
    "dimension_name",
    "name",
    "source",
    "summary",
    "when_to_use",
    "principle",
    "visual_usage",
    "copy_usage",
    "pitfalls",
    "pairs_with",
)


def test_libraries_and_cli() -> None:
    # 校验四个 JSON 卡片库字段完整性、跨库引用有效性与 CLI 查询子命令
    libraries = ad_playbook.load_libraries()
    index = ad_playbook.build_card_index(libraries)
    assert index

    for card_id, (_, card) in index.items():
        for field in REQUIRED_CARD_FIELDS:
            assert card.get(field), f"卡片 {card_id} 缺少有效字段 {field}"
        for partner_id in card["pairs_with"]:
            assert partner_id in index, f"卡片 {card_id} 引用了不存在的卡片 ID: {partner_id}"

    res_cat = subprocess.run(
        [sys.executable, str(SKILL_DIR / "scripts" / "ad_playbook.py"), "catalog"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "psych_01_pain_reenactment" in res_cat.stdout
    assert "适用场景:" in res_cat.stdout

    res_show = subprocess.run(
        [
            sys.executable,
            str(SKILL_DIR / "scripts" / "ad_playbook.py"),
            "show",
            "psych_01_pain_reenactment",
            "vis_carrier_01_native_vernacular",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "底层原理 (principle)" in res_show.stdout


if __name__ == "__main__":
    test_libraries_and_cli()
    print("OK")
