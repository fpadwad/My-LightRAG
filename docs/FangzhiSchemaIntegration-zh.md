> 当前状态（2026-11-21）：已停用下文介绍的方志研究适配模式。当前使用用户提供的 `lightrag/prompt.py`，配置为 `FANGZHI_SCHEMA_ENABLED=false`。下文保留为先前方案的说明，不代表当前启用状态。

> 当前网页、启动方式及全部交付改动见 [本地改动与交付说明](LocalCustomization-zh.md)。

# 方志实体、关系与中文抽取规则接入

本目录已接入研究 Schema v1.0：13 类实体、30 种内容关系及 7 种派生连接。启用后，现有文档上传/文本入库流程会使用 `prompts/fangzhi/schema.md` 与 `extraction_prompt.md`，不再把研究 JSON 直接当作通用抽取 JSON。

## 使用

1. 在项目根目录打开终端，运行 `python -m lightrag.api.lightrag_server`；也可运行根目录的 `启动方志LightRAG.cmd`。须使用已安装项目依赖的 Python。
2. 首次运行前确认 `.env` 的大模型和向量模型连接可用。项目若尚未构建 WebUI，需先按项目 README 构建；提示词接入不等于 WebUI 已构建完成。
3. 在新的工作区中上传少量真实文献进行人工核对。此接入不会自动修改或重抽已入库的旧资料。
4. 如需书名、版本和来源地域，先编辑 `prompts/fangzhi/source_metadata.json`。键必须与上传后 chunk 的 `file_path` 完全一致，通常可在界面的文档路径中查看。只按完整值匹配，不以相同文件名猜测来源。

配置示例：

```json
{
  "某县志.txt": {
    "book_title": "某县志",
    "edition": "用户已核实的版本说明",
    "source_region": "用户已核实的来源地域",
    "locator": null,
    "bibliographic_information": null,
    "existing_entities": []
  }
}
```

版本不详须填 null，不填写示例文字。没有元数据时仍可抽取，但直接来源为 null，并要求模型输出待核说明；程序不会根据文件名推断版本，也不会把标题地域当作实际适用地域。页码必须由用户提供；自动 locator 仅表示内部文本块，不是原书页码。长文跨块的指代不能自动解决，初期宜按独立章节或记述拆分后导入。

## 实际处理流程

- 中文规范与提示词全文随每块请求传给配置的大模型。块编号包含工作区、文档和文本块身份的稳定摘要。
- 先校验类型、端点方向、引用、对称配偶顺序、局部身份、肯否、记录范围和证据摘句，再允许进入图谱流程。失败会显示文档处理错误，不默默省略不兼容字段；不合格的新响应不会写入抽取缓存。
- 完整研究 JSON、原文、输入元数据和配置指纹另存于当前 `WORKING_DIR/fangzhi_records/<工作区摘要>/`。相同结果重复处理不重复存档，不同结果保留不同快照。这些文件含研究材料，应按本地资料管理。
- 入 LightRAG 的节点保留完整 ID。每条内容关系转为独立 `RelationAssertion` 检索节点；主体、客体与原文支持分别连接，描述保留关系方向、肯否和限定。研究类型与工程断言节点有所区别。
- 7 种结构连接由 records 字段生成。无向存储下相同端点的工程连接会汇集角色关键词和描述；完整原始结构以研究 JSON 为准。
- 不生成将“否定/存疑”改成肯定事实的内容直连边。检索回答仍应回查文献记载和原文，不能把所有断言当已证实史实。
- 研究模式关闭普通增量补抽，避免补抽响应缺少原记录或冲突 ID。请求、Schema 和提示词变化都会改变抽取提示内容，使用原有缓存机制区分。

## 开关与路径

```dotenv
FANGZHI_SCHEMA_ENABLED=true
FANGZHI_DATASET_ID=FZ001
ENTITY_EXTRACTION_USE_JSON=true
SUMMARY_LANGUAGE=Chinese
```

默认规则目录为本项目 `prompts/fangzhi`；可通过 `FANGZHI_PROFILE_DIR` 指向另一绝对目录，但该目录必须包含 schema.md、extraction_prompt.md、source_metadata.json。运行时也可用 `FANGZHI_SCHEMA_ENABLED=false` 恢复原抽取流程；已有研究缓存仍可解析重建，不做数据迁移或删除。

`.env`、source_metadata.json 和本次备份均不应提交 GitHub。规则正文和词表可提交。备份目录记录在 `fangzhi-integration-report.json`；恢复前先核对后来是否有其他修改，不直接批量覆盖。

## 验证边界

配套演示是虚构文本，自动测试使用模拟模型，不证明真实模型准确率。真实试抽还需检查：同名对象不误合并、来源地域不冒充适用地域、否定与存疑分开保存、原文证据逐字可追溯。若调用方后续修改 Schema 类型或关系表，须同步更新 `lightrag/extraction/fangzhi_vocabulary.json` 并重跑测试。
