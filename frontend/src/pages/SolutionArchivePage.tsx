import * as React from "react";
import { api } from "../api/client";
import type { Category, Solution } from "../api/types";

export function SolutionArchivePage() {
  const [categories, setCategories] = React.useState<Category[]>([]);
  const [categoryId, setCategoryId] = React.useState<number | "">("");
  const [keyword, setKeyword] = React.useState("");
  const [results, setResults] = React.useState<Solution[] | null>(null);
  const [expandedId, setExpandedId] = React.useState<number | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    api.get<Category[]>("/categories").then(setCategories).catch(() => {});
  }, []);

  const search = React.useCallback(() => {
    const params = new URLSearchParams();
    if (categoryId) params.set("category_id", String(categoryId));
    if (keyword.trim()) params.set("keyword", keyword.trim());

    api
      .get<Solution[]>(`/solutions?${params.toString()}`)
      .then(setResults)
      .catch(() => setError("검색 결과를 불러오지 못했습니다."));
  }, [categoryId, keyword]);

  React.useEffect(() => {
    search();
  }, [search]);

  async function openDetail(solution: Solution) {
    if (expandedId === solution.id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(solution.id);
    // 상세 조회 API를 호출해 view_count를 반영한다.
    try {
      const detail = await api.get<Solution>(`/solutions/${solution.id}`);
      setResults((prev) => prev?.map((s) => (s.id === detail.id ? detail : s)) ?? prev);
    } catch {
      // 조회수 반영 실패는 무시 — 이미 표시된 내용은 그대로 보여준다.
    }
  }

  return (
    <div className="page">
      <h1>사례 아카이브</h1>
      <p className="page-sub">카테고리와 키워드로 기존 해결 사례를 검색합니다.</p>

      <div className="archive-filters">
        <select value={categoryId} onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : "")}>
          <option value="">전체 카테고리</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <input
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="키워드 검색"
        />
      </div>

      {error && <p className="form-error">{error}</p>}
      {!results && !error && <p className="page-loading">불러오는 중...</p>}
      {results && results.length === 0 && <p className="empty-state">검색 결과가 없습니다.</p>}

      <ul className="solution-list">
        {results?.map((s) => (
          <li key={s.id} className="solution-item">
            <button className="solution-summary" onClick={() => openDetail(s)}>
              <div>
                <div className="case-title">{s.title}</div>
                <div className="case-meta">{s.category.name}</div>
              </div>
              <span className="solution-views">조회 {s.view_count}</span>
            </button>
            {expandedId === s.id && <p className="solution-content">{s.content}</p>}
          </li>
        ))}
      </ul>
    </div>
  );
}
