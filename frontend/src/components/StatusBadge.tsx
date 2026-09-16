import type { CaseStatus, MatchStatus, SessionStatus } from "../api/types";

type Status = CaseStatus | MatchStatus | SessionStatus;

const TONE: Record<string, "neutral" | "info" | "warn" | "success"> = {
  등록: "neutral",
  매칭요청: "info",
  상담중: "info",
  해결: "success",
  요청: "info",
  수락: "success",
  거절: "neutral",
  대기: "neutral",
  진행중: "info",
  완료: "success",
};

export function StatusBadge({ status }: { status: Status }) {
  const tone = TONE[status] ?? "neutral";
  return <span className={`badge badge-${tone}`}>{status}</span>;
}
