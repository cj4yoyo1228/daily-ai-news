import re
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer, util

from src.models.schemas import RawArticle

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_GARBLED_RE = re.compile(r"[^\x00-\x7F\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]+")


def clean_text(text: str) -> str:
    """移除 HTML 標籤、亂碼，並將連續空白壓縮為單一空格。"""
    text = _HTML_TAG_RE.sub("", text)
    text = _GARBLED_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


class ArticleFilter:
    SIMILARITY_THRESHOLD = 0.75

    def __init__(self):
        print("[Dedup] 載入語意模型 all-MiniLM-L6-v2 ...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[Dedup] 模型載入完成")

    def process(self, articles: List[RawArticle]) -> List[RawArticle]:
        """對文章列表進行清洗、語意去重，回傳高純度結果。"""
        if not articles:
            return []

        cleaned_articles: List[RawArticle] = []
        texts: List[str] = []

        for article in articles:
            cleaned_snippet = clean_text(article.content_snippet)
            cleaned_title = clean_text(article.title)

            combined = f"{cleaned_title} {cleaned_snippet}"
            if len(combined) < 30:
                continue

            article.content_snippet = cleaned_snippet
            article.title = cleaned_title
            cleaned_articles.append(article)
            texts.append(combined)

        if not cleaned_articles:
            return []

        print(f"[Dedup] 清洗後剩餘 {len(cleaned_articles)} 篇，開始計算 Embedding ...")
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

        cluster_reps: List[int] = []
        cluster_embs: List[np.ndarray] = []

        for idx, emb in enumerate(embeddings):
            if not cluster_reps:
                cluster_reps.append(idx)
                cluster_embs.append(emb)
                continue

            sims = util.cos_sim(emb, np.array(cluster_embs))[0].numpy()
            best_match = int(np.argmax(sims))
            best_score = float(sims[best_match])

            if best_score > self.SIMILARITY_THRESHOLD:
                rep_idx = cluster_reps[best_match]
                rep_article = cleaned_articles[rep_idx]
                dup_article = cleaned_articles[idx]
                if dup_article.source not in rep_article.similar_sources:
                    rep_article.similar_sources.append(dup_article.source)
            else:
                cluster_reps.append(idx)
                cluster_embs.append(emb)

        result = [cleaned_articles[i] for i in cluster_reps]
        deduped = len(cleaned_articles) - len(result)
        print(f"[Dedup] 去重完成：合併了 {deduped} 篇重複文章，最終保留 {len(result)} 篇")
        return result
