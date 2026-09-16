import * as React from "react";

interface StarRatingProps {
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}

export function StarRating({ value, onChange, disabled }: StarRatingProps) {
  const [hover, setHover] = React.useState<number | null>(null);
  const display = hover ?? value;

  return (
    <div className="star-rating" role="radiogroup" aria-label="평점" onMouseLeave={() => setHover(null)}>
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          type="button"
          role="radio"
          aria-checked={value === n}
          aria-label={`${n}점`}
          className="star-btn"
          disabled={disabled}
          onMouseEnter={() => setHover(n)}
          onClick={() => onChange(n)}
        >
          {n <= display ? "★" : "☆"}
        </button>
      ))}
      <span className="star-value">{value}점</span>
    </div>
  );
}
