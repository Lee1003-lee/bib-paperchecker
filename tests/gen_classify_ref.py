"""生成分类流水线的黄金测试数据。
用固定候选（不联网）喂给 Python 的 _finish_check，导出输入与输出；
JS 端用同样输入跑 finishCheck，逐条比对 status/score/reasons。
"""
import io
import json
import sys

sys.path.insert(0, ".")

from bibchecker.models import BibEntry, Candidate as ModelCandidate
from bibchecker.checker import _finish_check


def entry_from(fields):
    return BibEntry(key=fields.get("key", "k"), entry_type=fields.get("type", "article"),
                    fields={k: v for k, v in fields.items() if k not in ("key", "type")})


def cand_from(d):
    return ModelCandidate(
        source=d.get("source", ""), title=d.get("title", ""),
        authors=list(d.get("authors", [])), year=d.get("year"),
        venue=d.get("venue", ""), url=d.get("url", ""),
        identifier=d.get("identifier", ""), raw=dict(d.get("raw", {})),
    )


# 覆盖各分类分支的场景。
CASES = [
    {
        "name": "doi-exact-match-validated",
        "entry": {"title": "Attention Is All You Need", "author": "Ashish Vaswani and Noam Shazeer",
                  "year": "2017", "doi": "10.5555/3295222.3295349"},
        "identifier": [{"source": "crossref", "title": "Attention Is All You Need",
                        "authors": ["Ashish Vaswani", "Noam Shazeer"], "year": 2017,
                        "identifier": "10.5555/3295222.3295349", "raw": {"doi": "10.5555/3295222.3295349"}}],
        "discovery": [],
        "scalars": {"completed": 1, "no_match_sources": 0, "authoritative_misses": 0, "identifier_success": True},
    },
    {
        "name": "doi-points-elsewhere-title-search-finds-target",
        "entry": {"title": "Deep Residual Learning for Image Recognition",
                  "author": "Kaiming He and Xiangyu Zhang", "year": "2016", "doi": "10.1109/CVPR.2016.90"},
        "identifier": [{"source": "crossref", "title": "A Completely Different Paper",
                        "authors": ["Someone Else"], "year": 2010,
                        "identifier": "10.1109/CVPR.2016.90", "raw": {"doi": "10.1109/CVPR.2016.90"}}],
        "discovery": [{"source": "openalex", "title": "Deep Residual Learning for Image Recognition",
                       "authors": ["Kaiming He", "Xiangyu Zhang"], "year": 2016,
                       "identifier": "10.1109/cvpr.2016.90", "raw": {"doi": "10.1109/cvpr.2016.90"}}],
        "scalars": {"completed": 2, "no_match_sources": 0, "authoritative_misses": 0, "identifier_success": True},
    },
    {
        "name": "title-only-discovery-validated",
        "entry": {"title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
                  "author": "Jacob Devlin and Ming-Wei Chang and Kenton Lee and Kristina Toutanova", "year": "2019"},
        "identifier": [],
        "discovery": [{"source": "openalex",
                       "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
                       "authors": ["Jacob Devlin", "Ming-Wei Chang", "Kenton Lee", "Kristina Toutanova"],
                       "year": 2019, "venue": "NAACL"}],
        "scalars": {"completed": 2, "no_match_sources": 0, "authoritative_misses": 0, "identifier_success": False},
    },
    {
        "name": "title-mismatch-authors-wrong-needs-review-or-unconfirmed",
        "entry": {"title": "Generative Adversarial Networks", "author": "Ian Goodfellow and Jean Pouget-Abadie",
                  "year": "2014"},
        "identifier": [],
        "discovery": [{"source": "openalex", "title": "Generative Adversarial Networks",
                       "authors": ["Completely Different", "Author Names"], "year": 2014}],
        "scalars": {"completed": 2, "no_match_sources": 0, "authoritative_misses": 0, "identifier_success": False},
    },
    {
        "name": "no-candidates-specific-title-hallucination",
        "entry": {"title": "Quantum Entanglement Assisted Neural Architecture Search for Photonic Circuits",
                  "author": "Alice Nobody and Bob Nobody and Carol Nobody", "year": "2021"},
        "identifier": [],
        "discovery": [],
        "scalars": {"completed": 3, "no_match_sources": 3, "authoritative_misses": 0, "identifier_success": False},
    },
    {
        "name": "no-candidates-few-sources-unconfirmed",
        "entry": {"title": "Some Very Specific Long Title About Learning Systems And Networks",
                  "author": "X Y", "year": "2020"},
        "identifier": [],
        "discovery": [],
        "scalars": {"completed": 1, "no_match_sources": 1, "authoritative_misses": 0, "identifier_success": False},
    },
    {
        "name": "arxiv-match-with-year-diff-needs-review",
        "entry": {"title": "Denoising Diffusion Probabilistic Models", "author": "Jonathan Ho and Ajay Jain",
                  "year": "2020", "eprint": "2006.11239"},
        "identifier": [{"source": "openalex", "title": "Denoising Diffusion Probabilistic Models",
                        "authors": ["Jonathan Ho", "Ajay Jain"], "year": 2021,
                        "identifier": "2006.11239", "raw": {"arxiv_id": "2006.11239"}}],
        "discovery": [],
        "scalars": {"completed": 1, "no_match_sources": 0, "authoritative_misses": 0, "identifier_success": True},
    },
]

out = []
for case in CASES:
    entry = entry_from(case["entry"])
    ident = [cand_from(c) for c in case["identifier"]]
    disc = [cand_from(c) for c in case["discovery"]]
    s = case["scalars"]
    result = _finish_check(
        entry=entry, provider_count=2, identifier_candidates=ident,
        discovery_candidates=disc, provider_errors={}, completed=s["completed"],
        no_match_sources=s["no_match_sources"], authoritative_misses=s["authoritative_misses"],
        identifier_success=s["identifier_success"],
    )
    out.append({
        "name": case["name"],
        "input": {"entry": case["entry"], "identifier": case["identifier"],
                  "discovery": case["discovery"], "scalars": s},
        "expected": {"status": result.status, "score": round(result.score, 6),
                     "reasons": result.reasons},
    })

with io.open("web-static/tests/_classifyref.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("cases:", len(out))
for o in out:
    print(f"  {o['name']}: {o['expected']['status']} ({o['expected']['score']})")
