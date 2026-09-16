from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Attachment, Case, User
from ..schemas import AttachmentOut

router = APIRouter(tags=["attachments"])

# backend/app/routers/attachments.py -> parents[2] == backend/
UPLOAD_DIR = Path(__file__).resolve().parents[2] / "uploads"

MAX_ATTACHMENTS = 5
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
}


@router.post("/cases/{case_id}/attachments", response_model=list[AttachmentOut], status_code=201)
async def upload_attachments(
    case_id: int,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="요청하신 정보를 찾을 수 없습니다.")
    if case.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")

    if len(case.attachments) + len(files) > MAX_ATTACHMENTS:
        raise HTTPException(
            status_code=400,
            detail=f"사진은 최대 {MAX_ATTACHMENTS}장까지 첨부할 수 있습니다.",
        )

    case_dir = UPLOAD_DIR / str(case_id)
    case_dir.mkdir(parents=True, exist_ok=True)

    created: list[Attachment] = []
    for upload in files:
        if upload.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400, detail="이미지 파일(jpg, png, gif, webp)만 첨부할 수 있습니다."
            )
        contents = await upload.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="파일 하나의 크기는 5MB를 넘을 수 없습니다.")

        ext = ALLOWED_TYPES[upload.content_type]
        stored_name = f"{uuid4().hex}{ext}"
        (case_dir / stored_name).write_bytes(contents)

        attachment = Attachment(
            case_id=case_id,
            file_url=f"/uploads/{case_id}/{stored_name}",
            file_name=upload.filename or stored_name,
        )
        db.add(attachment)
        created.append(attachment)

    db.commit()
    for attachment in created:
        db.refresh(attachment)
    return created
