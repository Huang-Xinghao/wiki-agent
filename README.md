# WikiAgent

独立的科研知识库 Agent：将论文 PDF 转为有来源证据的 Paper、Idea、Experiment 节点，经过独立模型审核后发布到本地 Markdown Wiki，并提供中英文检索和跨论文关系图谱。

从 [paper_agent](https://github.com/Huang-Xinghao/paper_agent) 的 Wiki 部分拆出，包含拆分时工作目录中的最新修改。安装与运行不依赖原仓库。

## 安装

需要 Python 3.11+；当前发布流程使用 Unix 文件锁，支持 Linux/macOS。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
```

在 `.env` 中填写 `OPENAI_API_KEY`，按需设置 `WIKI_AGENT_MODEL` 和 `OPENAI_BASE_URL`。模型服务需支持 OpenAI Chat Completions、函数调用和图片输入。

PDF 入库需要另行准备 **MinerU** 运行环境、对应模型与 `mineru-kit parse` 命令，该环境也需包含 `pypdfium2` 和 `Pillow`（用于图片分组）。设置 `WIKI_AGENT_MINERU_PYTHON` 为该环境的 Python 路径。主包不会自动安装或下载大型 PDF 解析模型。初始化、词法检索与读取已有 Wiki 不需要 MinerU 或 API 密钥。

## 使用

```bash
wiki-agent --wiki-root ./research-wiki init
wiki-agent --wiki-root ./research-wiki ingest ./papers/example.pdf
wiki-agent --wiki-root ./research-wiki search 'capacity estimation' --strategy lexical
wiki-agent --wiki-root ./research-wiki search '容量估计' --view abstracts
wiki-agent --wiki-root ./research-wiki read literature/papers/example.md
wiki-agent --wiki-root ./research-wiki stats
```

`read` 使用搜索结果返回的真实 `wiki_path`。也可以运行 `python -m wiki_agent`。库路径默认是当前目录下的 `research-wiki`，支持通过 `WIKI_AGENT_WIKI_ROOT` 指定。

默认入库工作目录为 PDF 所在文件夹，草稿、解析缓存、审核记录和回执保存在其 `.wiki-agent/` 中。指定 `--project ./workspace` 时，PDF 必须位于该工作目录内。项目证据可通过 `--project-evidence --source results/metrics.json` 一并归档；`--force` 强制重新处理，`--no-relations` 跳过跨论文关系补充。

Agent 完整读取来源后生成 JSON 草稿，使用独立模型请求核验事实，再经过发布工具检查来源和草稿版本。已审核草稿发生变化后必须重新审核；重复输入可跳过，未完成任务保留草稿供恢复。最多三次独立审核，未解决的事实错误会阻止发布，允许保留的问题写入质量记录。

## 检索与工具

- BM25 词法检索支持中英文，默认返回标题，可选择已有摘要；`read` 读取选中页面的完整 Markdown。
- 可选 E5 ONNX 语义检索融合词法排序，并按已有图谱关系发现相关论文。
- `research-wiki --help` 提供底层建库、节点和索引工具。
- `scripts/wiki_batch.py` 提供可注入模型的 `BatchWikiAgent`，适合已分配 PDF 的批处理与恢复。
- `scripts/visualize_wiki.py --help` 导出可浏览的关系图；`scripts/repair_wiki_node_paths.py --help` 提供旧节点路径迁移。

语义检索配置：

```bash
pip install -e '.[embedding]'
python scripts/setup_wiki_embedding.py --destination ./models/e5 --python "$VIRTUAL_ENV/bin/python"
```

将生成的 `models/e5/runtime.env` 中两个 `WIKI_AGENT_EMBEDDING_*` 配置加入 `.env`。脚本只下载固定版本的编码器和 tokenizer，不修改 Python 环境。ONNX 文件针对 AVX512 VNNI 优化，运行前确认部署机器兼容。

## 开发验证

```bash
python -m pytest -q
python -m build
```

测试使用本地模型与解析器替身，覆盖来源校验、独立审核、发布、断点恢复、引用修复和检索，不调用付费 API。真实 PDF 解析和模型效果需要配置对应服务后验证。

代码使用 `wiki_agent` 包、`WIKI_AGENT_*` 配置和 `.wiki-agent` 状态目录；原 PaperAgent 的 Web UI、研究流程协调器和实验执行器不包含在此仓库中。现有 Wiki Markdown 数据可通过指定库路径使用，旧运行状态没有自动迁移。

仓库仅包含代码、测试和配置示例，论文 PDF、已有知识库、API 密钥与机器本地运行数据不随代码发布。第三方来源见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
