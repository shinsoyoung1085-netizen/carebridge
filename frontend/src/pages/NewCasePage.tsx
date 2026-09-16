import * as React from "react";
import { useNavigate } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Attachment, Case, Category } from "../api/types";

const MAX_PHOTOS = 5;

export function NewCasePage() {
  const navigate = useNavigate();
  const [categories, setCategories] = React.useState<Category[]>([]);
  const [categoryId, setCategoryId] = React.useState<number | "">("");
  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [photos, setPhotos] = React.useState<File[]>([]);
  const [previews, setPreviews] = React.useState<string[]>([]);
  const [error, setError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    api.get<Category[]>("/categories").then(setCategories).catch(() => setError("카테고리를 불러오지 못했습니다."));
  }, []);

  React.useEffect(() => {
    const urls = photos.map((f) => URL.createObjectURL(f));
    setPreviews(urls);
    return () => urls.forEach((u) => URL.revokeObjectURL(u));
  }, [photos]);

  function handleFilesSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = Array.from(e.target.files ?? []);
    e.target.value = ""; // 같은 파일 다시 선택 가능하도록 초기화

    const room = MAX_PHOTOS - photos.length;
    if (room <= 0) {
      setError(`사진은 최대 ${MAX_PHOTOS}장까지 첨부할 수 있습니다.`);
      return;
    }
    setError(null);
    setPhotos((prev) => [...prev, ...picked.slice(0, room)]);
  }

  function removePhoto(index: number) {
    setPhotos((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!categoryId) {
      setError("카테고리를 선택해주세요.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const created = await api.post<Case>("/cases", {
        category_id: categoryId,
        title,
        description,
      });

      if (photos.length > 0) {
        try {
          await api.uploadFiles<Attachment[]>(`/cases/${created.id}/attachments`, photos);
        } catch (uploadErr) {
          // 케이스 자체는 등록됐으니, 사진 업로드 실패는 상세 화면에서 안내하고 이동한다.
          console.error(uploadErr);
        }
      }

      navigate(`/cases/${created.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "케이스 등록에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page page-narrow">
      <h1>케이스 등록</h1>
      <p className="page-sub">겪고 있는 문제를 등록하면 관련 사례를 먼저 보여드립니다.</p>

      <form onSubmit={handleSubmit} className="stack-form">
        <label htmlFor="case-category">카테고리</label>
        <select
          id="case-category"
          value={categoryId}
          onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : "")}
          required
        >
          <option value="">선택해주세요</option>
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>

        <label htmlFor="case-title">제목</label>
        <input
          id="case-title"
          maxLength={100}
          placeholder="예: 급여내역 신고 화면에서 저장이 안 돼요"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />

        <label htmlFor="case-description">상세 설명</label>
        <textarea
          id="case-description"
          rows={6}
          maxLength={2000}
          placeholder="문제가 발생한 상황을 자세히 적어주세요"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          required
        />

        <label htmlFor="case-photos">사진 첨부 (선택, 최대 {MAX_PHOTOS}장)</label>
        <div className="photo-picker">
          {previews.map((src, i) => (
            <div key={src} className="photo-thumb">
              <img src={src} alt={`첨부 사진 ${i + 1}`} />
              <button type="button" className="photo-remove" onClick={() => removePhoto(i)} aria-label="사진 제거">
                ×
              </button>
            </div>
          ))}
          {photos.length < MAX_PHOTOS && (
            <button type="button" className="photo-add" onClick={() => fileInputRef.current?.click()}>
              + 사진 추가
            </button>
          )}
        </div>
        <input
          ref={fileInputRef}
          id="case-photos"
          type="file"
          accept="image/png,image/jpeg,image/gif,image/webp"
          multiple
          onChange={handleFilesSelected}
          hidden
        />

        {error && <p className="form-error">{error}</p>}

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? "등록 중..." : "등록"}
        </button>
      </form>
    </div>
  );
}
