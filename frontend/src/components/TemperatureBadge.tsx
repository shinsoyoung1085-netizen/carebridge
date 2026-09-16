export function TemperatureBadge({ value }: { value: number }) {
  const tone = value >= 50 ? "hot" : value >= 36.5 ? "warm" : "cool";
  return (
    <span className={`temp-badge temp-${tone}`}>
      🌡️ {value.toFixed(1)}°C
    </span>
  );
}
