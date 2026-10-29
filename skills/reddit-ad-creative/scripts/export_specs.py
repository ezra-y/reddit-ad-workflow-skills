import argparse
from io import BytesIO
from pathlib import Path
from PIL import Image


PRESETS: dict[str, tuple[int, int, int | None]] = {
    "feed-4x5": (1080, 1350, None),
    "feed-4x3": (1440, 1080, None),
    "feed-1x1": (1080, 1080, None),
    "thumb-4x3": (400, 300, 500 * 1024),
}


def export_image(src_path: Path, dst_path: Path, preset: str, top_bias: float) -> None:
    if not 0.0 <= top_bias <= 1.0:
        raise ValueError(f"top_bias 需在 0.0~1.0 之间，当前为 {top_bias}")
    if not src_path.is_file():
        raise FileNotFoundError(f"源图片不存在: {src_path}")

    target_w, target_h, max_bytes = PRESETS[preset]
    target_ratio = target_w / target_h

    with Image.open(src_path) as raw:
        img = raw.convert("RGB")
        w, h = img.size
        src_ratio = w / h

        # 按目标宽高比计算无变形裁切框
        if src_ratio < target_ratio:
            crop_h = round(w / target_ratio)
            top = round((h - crop_h) * top_bias)
            box = (0, top, w, top + crop_h)
        else:
            crop_w = round(h * target_ratio)
            left = (w - crop_w) // 2
            box = (left, 0, left + crop_w, h)

        resized = img.crop(box).resize((target_w, target_h), Image.Resampling.LANCZOS)

    buf = BytesIO()
    resized.save(buf, format="PNG", optimize=True)
    data = buf.getvalue()

    # 缩略图若超出体积上限则转为 256 色调色板 PNG
    if max_bytes is not None and len(data) > max_bytes:
        buf = BytesIO()
        quantized = resized.quantize(colors=256, method=Image.Quantize.FASTOCTREE)
        quantized.save(buf, format="PNG", optimize=True)
        data = buf.getvalue()
        if len(data) > max_bytes:
            raise ValueError(f"导出文件体积 {len(data)} bytes 超出上限 {max_bytes} bytes")

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_bytes(data)
    print(f"{dst_path}: {w}x{h} crop={box} -> {target_w}x{target_h} ({len(data) / 1024:.1f} KB)")


def main() -> None:
    parser = argparse.ArgumentParser(description="将原始生图按 Reddit 官方规格裁切并导出 PNG")
    parser.add_argument("src", type=Path, help="原始图片路径（如 3:4 或 4:3 JPG）")
    parser.add_argument("dst", type=Path, help="导出目标 PNG 路径")
    parser.add_argument(
        "--preset",
        choices=list(PRESETS.keys()),
        default="feed-4x5",
        help="目标规格预设（默认 feed-4x5 -> 1080x1350）",
    )
    parser.add_argument(
        "--top-bias",
        type=float,
        default=0.5,
        help="纵向裁切重心（0.0 偏上保留顶部，1.0 偏下保留底部，默认 0.5 居中）",
    )
    args = parser.parse_args()
    export_image(args.src, args.dst, args.preset, args.top_bias)


if __name__ == "__main__":
    main()
