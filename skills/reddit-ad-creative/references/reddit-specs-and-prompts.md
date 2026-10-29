# 阶段二：Reddit 广告规格、生图提示词与缩略图制作指南

在阶段一选定要出图的创意方向后，进入阶段二。本阶段遵循【原则表 B：Reddit 规格与生图原则】，输出两套视觉资产：**信息流主图（多个差异化开放构图候选版）**与**独立重新构图的 `4:3` 超大字缩略图**。

---

## 一、Reddit 信息流主图比例与满画幅构图规范（原则 B1）

根据广告画面的内容形态，主图采用以下标准比例：

| 比例规格 | 标准分辨率 | 适用内容形态与投放优势 |
| :--- | :--- | :--- |
| **`4:5` 竖图（官方首推默认规格）** | **`1080 × 1350 px`** | **Reddit 官方首选推荐主力规格**，在手机端信息流占据最大纵向屏幕面积，上下排布空间充裕、转化表现最佳。 |
| **`4:3` 横图（跨端宽幅规格）** | **`1440 × 1080 px`** | **桌面端与手机端兼顾的宽幅规格**，适合左右并列桌面场景或宽屏终端界面，且与 `4:3` 缩略图同比例。 |
| **`1:1` 方图（分格叙事规格）** | **`1080 × 1080 px`**（或 `1200 × 1200 px`） | **分格叙事与紧凑单焦点规格**。 |

### 画面内部构图与安全区要求
- **满画幅原生场景（Full-Bleed Scene Composition）**：画面本身就是一个直接铺满画布的完整场景（真实场景摄影、原生软件界面、社区分格叙事插画或大字平面视觉），主文案自然融入场景或留白空间。
- **安全区与留白要求**：画面中的核心视觉焦点与主文案保持在画幅中央安全区域内，四周留出干净呼吸空间，避开画幅边缘裁切与平台底栏遮挡，品牌署名克制地融入画面角落。

### 零解码直觉、视觉戏眼与跨候选版多样性原则
在 Reddit 信息流快速滑动中，画面设计遵循以下底层视觉规律：
1. **零解码直觉与视觉戏眼（Instant Grasp & Visual Hook）**
   - 画面主体可自由采用真实软件环境、社区原生分格叙事、生活同构比喻或具象物理道具，受众凭日常常识或社区直觉即可第一眼看懂因果关系；由画面自身的动作与反差演完核心冲突，图内文字保持短促点睛。
2. **跨候选版彻底差异化（Cross-Candidate Visual Diversity）**
   - 同一条广告并发生成的多个候选版，在**画风媒介、叙事角度与版式结构**上彻底拉开差距，为阶段三提供真正不同风格的择优空间。

---

## 二、独立生成 `4:3` 特写超大字缩略图规范（原则 B2）

Reddit 的紧凑视图（Compact View / Classic View）以及 `old.reddit.com` 拥有大量高粘性硬核用户。在这些视图下，缩略图仅被渲染为极小尺寸的预览框。

### 规格与构图要求
- **比例规格**：**`4:3` 横图（`1440 × 1080 px` 或导出 `400 × 300 px`，文件体积 $\le 500\text{ KB}$）**。
- **核心视觉主体特写放大 + 撑满画幅的超大粗体字**：
  - 去除主图里的前因铺垫、副标题与次要细节；
  - **把主图中最具冲突感的单一视觉主体特写放大到占满画幅**；
  - 压上**精炼短促的超大加粗核心英文短语与关键数字，饱满撑起画幅核心区域**，确保在紧凑视图极小尺寸下依然第一眼看清图案与大字。

---

## 三、调用生图模型 API 的提示词准则（原则 B3 & B4）

### 1. 逐字给出画面英文文案（Verbatim Copy）
- 调用图像生成 API 时，将需要渲染在图片上的英文文案用双引号逐字列出，并在提示词末尾说明：**「English text only on the image, no extra words or invented numbers.」**

### 2. 开放排版自由度与 API 并发生成
- **锁定什么**：锁定核心视觉主体与因果/对比关系、材质光影基调、画面英文文案。
- **放开什么**：不在提示词里用死板的像素坐标限制模型的具体排版角度，允许模型在干净留白的前提下自由探索最具张力的构图、字体搭配与主次比例。
- **并发生成**：每条广告通过 API 并发生成多个不同构图与媒介探索方向的主图候选版，进入阶段三择优录取。

### 3. 品牌克制署名与真实图形 Logo 参考图传入
- **文字署名位置**：品牌名称在画面角落或底部安全边距内作为克制、体面的小署名出现。
- **真实图形 Logo 传入**：当画面需要印上品牌真实图形 Logo 或还原真实软件界面时，**直接在生图 API 的参考图参数中传入官方 Logo PNG 或真实界面素材**。

### 4. 真人形象整洁度与社区原生界面还原
- **人物形象标准**：画面出现真人时，人物气质贴合目标社区受众，设定为面部清爽干净、衣着整洁得体的日常形象，采用柔和真实的自然光线或环境光。
- **软件界面还原标准**：当画软件界面切片时，提示词精确描述目标软件真实的主题配色、布局结构、图标与系统原生状态样式。

---

## 四、生图提示词结构参考

```text
[Format & Full-Bleed Composition]
 Aspect ratio: <4:5 portrait (1080x1350) default | 4:3 landscape (1440x1080) | 1:1 square (1080x1080)>.
 Full-bleed edge-to-edge visual scene filling the entire canvas naturally. Keep core focal points and text inside the central safe zone with clean breathing room at the edges.

[Core Visual Hook & Scene]
 Core visual subject: <Describe the visual action, contrast, analogy, or interface twist that conveys the point at a single glance, along with coherent style and lighting>.

[Verbatim English Typography — Exact Text Only]
 Render ONLY the following exact English strings cleanly and legibly (concise, punchy hierarchy):
 - Primary Copy: "<EXACT HEADLINE>"
 - Optional Secondary / Proof Copy: "<EXACT PROOF TEXT>"
 - Subtle Corner Signoff: "<BRAND NAME>"
 English text only on the image, no extra words or invented numbers.
```
