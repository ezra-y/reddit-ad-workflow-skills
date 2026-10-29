# 阶段二：Reddit 广告规格、生图提示词与导出指南

选定通过「反说明书自检」的创意方向后，进入阶段二生成两套视觉资产：**信息流主图（多个跨风格候选版）**与**独立重新构图的 `4:3` 特写超大字缩略图**。

---

## 一、Reddit 信息流主图规格与安全留白（原则 B1）

| 比例规格 | 标准分辨率 | 导出预设参数（`export_specs.py`） | 适用形态与优势 |
| :--- | :--- | :--- | :--- |
| **`4:5` 竖图（默认推荐）** | **`1080 × 1350 px`** | `--preset feed-4x5` | Reddit 手机端信息流纵向面积最大，阅读冲击力强。 |
| **`4:3` 横图（宽幅规格）** | **`1440 × 1080 px`** | `--preset feed-4x3` | 兼顾桌面端与移动端，适合横向展开的人物场景、桌面现场或宽屏构图。 |
| **`1:1` 方图（紧凑规格）** | **`1080 × 1080 px`** | `--preset feed-1x1` | 适合紧凑单焦点、分格梗图或居中大字视觉。 |

### 内置 `image-generator` 的真实工具边界与留白要点
1. **原生输出特性**：当前环境的 `image-generator` 子智能体原生输出 `3:4` 竖图（`896 × 1200 px` JPG）或 `4:3` 横图（`1200 × 896 px` JPG），文件自动保存在当前调用智能体自身的目录下，且生图子智能体没有终端移动文件或裁切图片的权限。
2. **调用方式**：调用 `image-generator` 时，**只传画面提示词与简短英文图片名**，无需让它转换 PNG 或保存到其他目录。
3. **`3:4` 转 `4:5` 的上下安全留白**：当目标主图为 `4:5` 竖图时，把 `3:4`（偏瘦长）裁切为 `4:5`（偏宽短）会从上下边缘合共裁掉约 `6.7%` 的高度（约 `80 px`）。因此在生图提示词中明确要求：**上下边缘各留出 `10%–12%` 纯净连贯的背景呼吸空间，所有文字与角落小署名统一收在纵向中央 `78%` 安全区域内**。
4. **一键标准导出**：拿到原始 JPG 并完成阶段三选图后，直接运行内置脚本导出精确分辨率 PNG（无需手写切图脚本）：
   ```bash
   python3 scripts/export_specs.py <raw_image.jpg> <final_1080x1350.png> --preset feed-4x5
   # 如需微调上下裁切重心（0.0 偏上保留顶部，1.0 偏下保留底部，默认 0.5 居中）：
   python3 scripts/export_specs.py <raw_image.jpg> <final_1080x1350.png> --preset feed-4x5 --top-bias 0.55
   ```

---

## 二、独立生成 `4:3` 特写超大字缩略图规范（原则 B2）

Reddit 紧凑视图（Compact View / Classic View）与 `old.reddit.com` 的缩略图预览框尺寸极小，直接缩小主图会导致细节糊成一团。

### 制作与导出步骤
- **独立构图重绘**：抽离次要背景与长句，将最具情绪或冲突张力的单一焦点特写放大撑满画幅，搭配**超大加粗的核心短词或关键数字**，调用 `image-generator` 以 `4:3` 横图比例单独生成。
- **一键导出合规缩略图（`400 × 300 px`，$\le 500\text{ KB}$）**：
  ```bash
  python3 scripts/export_specs.py <raw_thumb.jpg> <final_thumb_400x300.png> --preset thumb-4x3
  ```

---

## 三、生图提示词准则与跨候选版开放探索（原则 B3 & B4）

1. **跨候选版真正拉开风格跨度**：
   - 同一个方案并发生成的多个候选版，在**视觉媒介、拍摄视角、光影情绪与排版方式**上大胆拉开差距（例如：一张采用真实人物深夜纪实抓拍，另一张采用大胆排印态度海报或荒诞戏剧微缩现场），摆脱“全是深色卡片或桌面静物”的单一套路。
2. **逐字指定精炼英文文案（Verbatim Copy）**：
   - 图上只放真正必要的点睛短句与核实数字，将需渲染的英文放在双引号内逐字给出，并在提示词末尾注明：`English text only on the image, no extra words or invented numbers.`
3. **自由构图与真实参考图传入**：
   - 把构图动线、字体气质与主次留白交给模型结合画面氛围自然发挥；需要呈现真实品牌图形 Logo 或真实软件界面时，在生图调用中直接传入官方参考图。
4. **人物自然质感与软件细节还原**：
   - 画面出现人物时，神态情绪真实鲜活、衣着自然干净、采用有生活呼吸感的环境光影；出现软件局部时，贴合目标社区日常使用的真实界面外观。

---

## 四、生图提示词轻量骨架参考（按创意形态自由增删）

```text
[Canvas & Safe Margin]
 Portrait 3:4 raw frame designed for clean 4:5 (1080x1350) center crop (or 4:3 landscape).
 Full-bleed scene extending edge-to-edge. Keep ~12% clean background breathing room at the top and bottom edges so all text and focal details sit comfortably inside the central safe zone.

[Scene, Mood & Visual Tension]
 <Describe the human moment, candid reaction, absurdist scene, bold editorial typography, or everyday visual tension — focus on emotion, atmosphere, lighting, and what the image shows BEYOND the words>.

[Verbatim English Copy — Minimal & Exact]
 Render ONLY the following exact English text integrated naturally into the composition:
 - "<EXACT SHORT COPY>"
 (Optional subtle corner signoff if fitting: "<BRAND NAME>")
 English text only on the image, no extra words or invented numbers.
```
