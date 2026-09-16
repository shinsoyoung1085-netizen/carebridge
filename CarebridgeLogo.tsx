import * as React from "react";

export interface CarebridgeLogoProps extends React.SVGProps<SVGSVGElement> {
  /** "Care" 텍스트 색상 — 신뢰감을 주는 딥 블루 계열 */
  careColor?: string;
  /** "bridge" 텍스트 색상 — 신선하고 따뜻한 그린 계열 */
  bridgeColor?: string;
  /** 아치 위 잎사귀 포인트 색상 */
  leafColor?: string;
  /** 아치 심볼의 선 굵기 */
  archStrokeWidth?: number;
  /** 워드마크(텍스트) 노출 여부. false면 아치+잎 심볼만 렌더링 */
  showWordmark?: boolean;
}

/**
 * Carebridge 워드마크 로고.
 *
 * "bridge"의 r·i 위쪽에 다리(Arch)와 잎(Leaf)을 결합한 심볼을 배치했고,
 * 아치 선 자체에 Care(블루) → bridge(그린) 그라데이션을 적용해
 * "두 가치를 잇는다"는 브랜드 의미를 색으로도 표현했다.
 */
export function CarebridgeLogo({
  careColor = "#1B589C",
  bridgeColor = "#42B549",
  leafColor = "#8CC63F",
  archStrokeWidth = 2.5,
  showWordmark = true,
  ...rest
}: CarebridgeLogoProps) {
  const gradientId = React.useId();

  return (
    <svg
      viewBox="0 0 220 70"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Carebridge"
      {...rest}
    >
      <title>Carebridge</title>

      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor={careColor} />
          <stop offset="1" stopColor={bridgeColor} />
        </linearGradient>
      </defs>

      {/* 심볼: 다리(Arch) + 잎(Leaf) — "bridge"의 r·i 위쪽에 배치 */}
      <g transform="translate(106, 3)">
        {/* 아치 본체: Care → bridge 그라데이션 */}
        <path
          d="M4,20 C4,10 10,4 16,4 C22,4 28,10 28,20"
          stroke={`url(#${gradientId})`}
          strokeWidth={archStrokeWidth}
          strokeLinecap="round"
        />
        {/* 교각(피어): 아치가 텍스트에 내려앉는 느낌 */}
        <path
          d="M4,20 L4,24.5"
          stroke={careColor}
          strokeWidth={archStrokeWidth}
          strokeLinecap="round"
        />
        <path
          d="M28,20 L28,24.5"
          stroke={bridgeColor}
          strokeWidth={archStrokeWidth}
          strokeLinecap="round"
        />
        {/* 잎: 아치 정점 위 성장/돌봄 포인트 */}
        <path
          d="M22,2 C26.5,2 28.5,6.2 26.3,10 C24.8,12.6 20.6,11.6 20.3,8.3 C20.1,5.4 20.9,2.6 22,2 Z"
          fill={leafColor}
        />
        <path
          d="M22.4,10.4 L22.4,14"
          stroke={leafColor}
          strokeWidth={1.6}
          strokeLinecap="round"
        />
      </g>

      {/* 워드마크 */}
      {showWordmark && (
        <text
          x="14"
          y="54"
          fontFamily="'Pretendard', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans KR', sans-serif"
          fontWeight={700}
          fontSize="32"
          letterSpacing="-0.01em"
        >
          <tspan fill={careColor}>Care</tspan>
          <tspan fill={bridgeColor}>bridge</tspan>
        </text>
      )}
    </svg>
  );
}

export default CarebridgeLogo;
