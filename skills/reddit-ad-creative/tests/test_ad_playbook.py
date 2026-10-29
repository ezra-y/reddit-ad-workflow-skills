from pathlib import Path
import subprocess
import sys
import tempfile
from PIL import Image

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import ad_playbook
import export_specs

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
    assert len(index) == 56, f"预期 56 张卡片，实际 {len(index)}"

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
    assert "vis_carrier_03_human_reaction_moment" in res_cat.stdout
    assert "vis_carrier_04_bold_editorial_typography" in res_cat.stdout
    assert "vis_carrier_05_surreal_cultural_scene" in res_cat.stdout
    assert len(res_cat.stdout.encode("utf-8")) < 9800, "catalog 输出超出单屏免截断字节上限"

    res_show = subprocess.run(
        [
            sys.executable,
            str(SKILL_DIR / "scripts" / "ad_playbook.py"),
            "show",
            "psych_01_pain_reenactment",
            "vis_carrier_03_human_reaction_moment",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "底层原理:" in res_show.stdout

    # 超过 6 张卡时应快速报错阻断贪多
    too_many = list(index.keys())[:7]
    res_over = subprocess.run(
        [sys.executable, str(SKILL_DIR / "scripts" / "ad_playbook.py"), "show", *too_many],
        capture_output=True,
        text=True,
    )
    assert res_over.returncode != 0


def test_export_specs() -> None:
    # 校验 3:4 原始竖图导出 4:5 (1080x1350) 与 4:3 缩略图导出 (400x300, <=500KB)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        raw_portrait = tmp_dir / "raw_3x4.jpg"
        Image.new("RGB", (896, 1200), (24, 28, 36)).save(raw_portrait, format="JPEG")

        out_main = tmp_dir / "main_4x5.png"
        export_specs.export_image(raw_portrait, out_main, "feed-4x5", 0.5)
        with Image.open(out_main) as im:
            assert im.size == (1080, 1350)

        raw_landscape = tmp_dir / "raw_4x3.jpg"
        Image.new("RGB", (1200, 896), (245, 243, 238)).save(raw_landscape, format="JPEG")

        out_thumb = tmp_dir / "thumb_4x3.png"
        export_specs.export_image(raw_landscape, out_thumb, "thumb-4x3", 0.5)
        assert out_thumb.stat().st_size <= 500 * 1024
        with Image.open(out_thumb) as im:
            assert im.size == (400, 300)


if __name__ == "__main__":
    test_libraries_and_cli()
    test_export_specs()
    print("OK")
