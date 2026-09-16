export type UserRole = "staff" | "expert" | "admin";
export type UserStatus = "active" | "suspended";
export type CaseStatus = "등록" | "매칭요청" | "상담중" | "해결";
export type MatchStatus = "요청" | "수락" | "거절";
export type SessionStatus = "대기" | "진행중" | "완료";

export interface User {
  id: number;
  role: UserRole;
  name: string;
  nickname: string | null;
  email: string;
  org_name: string | null;
  status: UserStatus;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  description: string | null;
}

export interface Expert {
  id: number;
  name: string;
  nickname: string | null;
  temperature: number;
  review_count: number;
}

export interface Attachment {
  id: number;
  file_url: string;
  file_name: string;
  uploaded_at: string;
}

export interface SolutionSummary {
  id: number;
  title: string;
  view_count: number;
}

export interface Case {
  id: number;
  requester_id: number;
  category: Category;
  title: string;
  description: string;
  status: CaseStatus;
  created_at: string;
  resolved_at: string | null;
  attachments: Attachment[];
  related_solutions: SolutionSummary[];
  has_solution: boolean;
  active_match_id: number | null;
}

export interface Solution {
  id: number;
  category: Category;
  source_case_id: number | null;
  title: string;
  content: string;
  is_published: boolean;
  view_count: number;
  created_by: number;
  created_at: string;
}

export interface Match {
  id: number;
  case_id: number;
  case_title: string;
  case_description: string;
  expert_id: number;
  expert_display_name: string;
  status: MatchStatus;
  requested_at: string;
  responded_at: string | null;
  session_id: number | null;
}

export interface ConsultSession {
  id: number;
  match_id: number;
  case_id: number;
  expert_id: number;
  requester_id: number;
  remote_tool: string | null;
  access_code: string | null;
  status: SessionStatus;
  memo: string | null;
  started_at: string | null;
  ended_at: string | null;
}

export interface Review {
  id: number;
  session_id: number;
  rater_id: number;
  rating: number;
  comment: string | null;
  created_at: string;
}

export interface ChatResponse {
  answer: string;
  sources: string[];
}
