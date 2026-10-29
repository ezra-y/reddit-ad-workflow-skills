# 批量导入与素材包

从当前账户下载模板或导出目标广告，保留原件。按模板填写字段、枚举、时间及层级关系，用 `csv` 标准库或成熟表格工具读写，编号按文本保存。

## 层级与编号

- **新建**：按模板填写或留空编号，使用临时编号关联新建父子对象，检查每个引用都有对应父行。
- **修改**：使用真实平台编号；无关行移除或设置 `Results=IGNORE`（忽略）。
- **向已有组添加创意**：系列与广告组字段只保留对应编号，其他父级配置留空，以保留已有设置。
- **复用帖子**：核对原帖内容与字段可编辑性；需要不同内容时创建新帖子。

这些规则来自 [Reddit 批量导入说明](https://business.reddithelp.com/s/article/Build-and-edit-with-bulk-import)，核验于 2026-10-29；执行时以当前模板与界面为准。

## 素材打包

复用同套 `ad-campaign-archive` 中的 [package_assets.py](../../ad-campaign-archive/scripts/package_assets.py)。使用实际脚本绝对路径：

```bash
python3 /实际目录/ad-campaign-archive/scripts/package_assets.py \
  --csv /本次任务/投放配置.csv \
  --assets-dir /本次任务/最终素材 \
  --output /本次任务/投放包.zip
```

默认读取 `Media file name` 和 `Thumbnail file name`，每格引用一个本地文件，含扩展名。脚本检查引用和文件，将 CSV 与去重后的素材平铺打包到新 ZIP；它要求目标文件尚不存在。

其他素材列通过重复 `--media-column` 指定，轮播传入全部相关列。纯文本广告、多文件表达式或远端媒体格式按平台方式处理。重新打开 ZIP 核对文件与引用。

## 后台导入

按当前入口分别上传 CSV 和媒体，或使用明确支持的 ZIP 入口。区分上传解析、检查页面、最终保存和启用的实际作用。

检查逐项处理结果。模板未支持的版位、自定义受众等字段在后台补齐，并对照确认方案重新读取核对。
