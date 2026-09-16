import * as React from "react";

export function Tooltip({ text, children }: { text: string; children: React.ReactNode }) {
  if (!text) return <>{children}</>;

  return (
    <span className="tooltip-wrap">
      {children}
      <span className="tooltip-box">{text}</span>
    </span>
  );
}
