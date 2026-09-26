"""
REQ-NFN-004: 케이스·상담세션·사례 데이터 1일 1회 백업.

pg_dump로 cases/consult_sessions/solution_archive 3개 테이블을 매일 새벽
백업하고, 7일 지난 백업 파일은 자동으로 정리한다. APScheduler가 백엔드
프로세스 안에서 스케줄을 돌리므로 별도 cron 설정 없이 `uvicorn`만
띄워두면 동작한다.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy.engine import make_url

from .database import DATABASE_URL

BACKUP_DIR = Path(__file__).resolve().parents[1] / "backups"
BACKUP_TABLES = ["cases", "consult_sessions", "solution_archive"]
RETENTION_DAYS = 7

logger = logging.getLogger("carebridge.backup")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(BACKUP_DIR / "backup.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


def _pg_dump_command(output_path: Path) -> list[str]:
    """DATABASE_URL을 파싱해 pg_dump 커맨드를 구성한다.

    호스트·유저가 비어있으면 로컬 소켓/peer 인증(지금 개발 환경)을 그대로
    쓰도록 해당 플래그를 생략한다.
    """
    url = make_url(DATABASE_URL)

    cmd = ["pg_dump", "--no-owner", "--no-privileges"]
    if url.host:
        cmd += ["-h", url.host]
    if url.port:
        cmd += ["-p", str(url.port)]
    if url.username:
        cmd += ["-U", url.username]
    for table in BACKUP_TABLES:
        cmd += ["-t", table]
    cmd += ["-f", str(output_path), url.database]
    return cmd


def _prune_old_backups() -> int:
    """RETENTION_DAYS보다 오래된 백업 파일을 지우고 삭제 개수를 반환한다."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    removed = 0
    for path in BACKUP_DIR.glob("backup_*.sql"):
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff:
            path.unlink()
            removed += 1
            logger.info("7일 지난 백업 삭제: %s", path.name)
    return removed


def run_backup() -> Path:
    """백업 1회 실행. 성공하면 생성된 파일 경로를 반환하고, 실패하면 예외를 던진다."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    if shutil.which("pg_dump") is None:
        # 이 프로젝트 환경(Homebrew)에서는 PATH에 없을 수 있어 직접 경로도 시도한다.
        homebrew_pg_dump = "/opt/homebrew/opt/postgresql@17/bin/pg_dump"
        if Path(homebrew_pg_dump).exists():
            os.environ["PATH"] = f"/opt/homebrew/opt/postgresql@17/bin:{os.environ.get('PATH', '')}"
        else:
            logger.error("백업 실패: pg_dump 실행 파일을 찾을 수 없습니다.")
            raise RuntimeError("pg_dump를 찾을 수 없습니다.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = BACKUP_DIR / f"backup_{timestamp}.sql"
    cmd = _pg_dump_command(output_path)

    try:
        # 원격 DB는 비밀번호 인증이라 pg_dump에 PGPASSWORD로 넘겨준다(커맨드라인에 노출하지 않음).
        env = os.environ.copy()
        password = make_url(DATABASE_URL).password
        if password:
            env["PGPASSWORD"] = password
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300, env=env)
    except subprocess.CalledProcessError as exc:
        logger.error("백업 실패 (pg_dump 종료코드 %s): %s", exc.returncode, exc.stderr)
        raise
    except subprocess.TimeoutExpired:
        logger.error("백업 실패: pg_dump 실행이 5분을 초과해 중단했습니다.")
        raise

    size_kb = output_path.stat().st_size / 1024
    logger.info(
        "백업 성공: %s (%.1fKB, 테이블: %s)",
        output_path.name,
        size_kb,
        ", ".join(BACKUP_TABLES),
    )

    removed = _prune_old_backups()
    if removed:
        logger.info("보관기간(%d일) 초과 백업 %d개 정리 완료", RETENTION_DAYS, removed)

    return output_path


def start_backup_scheduler():
    """앱 시작 시 호출: 매일 새벽 3시에 run_backup을 실행하는 스케줄러를 띄운다."""
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = BackgroundScheduler(timezone="Asia/Seoul")

    def _job():
        try:
            run_backup()
        except Exception:  # noqa: BLE001 — 스케줄러 잡 안에서는 예외를 삼키고 로그만 남긴다
            logger.exception("정기 백업 작업 중 예외 발생")

    scheduler.add_job(_job, CronTrigger(hour=3, minute=0), id="daily_backup", replace_existing=True)
    scheduler.start()
    logger.info("백업 스케줄러 시작 — 매일 03:00(Asia/Seoul)에 실행됩니다.")
    return scheduler
