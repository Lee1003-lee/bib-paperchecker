# Paper-BibChecker · 纯前端 JS 版（web-static）

在**浏览器本地**运行的 BibTeX 引用核验版本：上传 `.bib`（可选 `.tex`），
逐条核对引用是否对应真实文献。所有计算在访问者自己的浏览器里完成，
**不经过任何服务器**——因此免费、可无限多人同时使用、无需部署后端。

## 与完整版（Python / FastAPI）的区别

| | 纯前端 JS 版（本目录） | 完整 Python 版 |
| --- | --- | --- |
| 运行位置 | 访问者浏览器 | 服务器 |
| 数据源 | **仅 OpenAlex + Crossref**（浏览器可跨域的两个源） | 18 个（含 arXiv、DBLP、各会议官网等） |
| 托管 | GitHub Pages（免费、无限并发） | 需要一台在线服务器 |
| 最新论文 / 会议官网核对 | 较弱（缺官方源，判定偏保守） | 强 |

核心检查逻辑（解析、标题/作者相似度、四类分类）是从 Python 版 **1:1 移植**
的，对 OpenAlex/Crossref 能覆盖的条目，结论与完整版一致（见 `tests/`）。

## 本地预览

必须用 HTTP 服务打开（ES module 不能用 `file://`）：

```bash
cd web-static
python -m http.server 8080
# 打开 http://localhost:8080
```

用仓库根目录的 `examples/example_ref.bib` 试跑。

## 目录结构

```
web-static/
  index.html          # 单页 UI（改编自 web/index.html，改为调用本地引擎）
  src/
    latex.js          # LaTeX 重音解码 + 文本归一化
    similarity.js     # difflib.SequenceMatcher 等价实现 + 标题/年份相似度
    parser.js         # BibTeX / LaTeX 引用键解析
    models.js         # BibEntry 派生属性（authors/year/doi/arxiv_id）
    authors.js        # 作者比对与相似度
    checker.js        # 候选评分、字段比对、四类分类
    providers.js      # OpenAlex + Crossref 查询与解析
    engine.js         # 检查编排 + 并发调度 + 第二层兜底钩子
  tests/
    run-tests.html    # 浏览器内一致性测试（与 Python 黄金数据比对）
    gen_classify_ref.py  # 重新生成分类黄金数据的脚本
    _*.json           # Python 导出的黄金参考数据
```

## 一致性测试

```bash
cd web-static
python -m http.server 8080
# 打开 http://localhost:8080/tests/run-tests.html
```

黄金数据由 Python 端生成（`tests/gen_classify_ref.py` 等），页面在浏览器里
用同样输入跑 JS 引擎并逐字段比对，全部应显示通过。

## 部署到 GitHub Pages

仓库已带 `.github/workflows/deploy-pages.yml`：push 到 `main` 且改动了
`web-static/` 时自动构建发布。首次需在 **仓库 Settings → Pages → Source**
选 **"GitHub Actions"**。之后访问 `https://<用户名>.github.io/<仓库名>/`。

## 第二层兜底（预留，未启用）

`engine.js` 的 `checkAll` 接受一个可选 `fallback(entry, key)` 回调：当纯前端
判定为 `unconfirmed` 时，可把该条目转交给完整 Python 后端复查，用少量后端
负载补回会议官网等源的能力。当前 UI 未接入，属后续工作。
