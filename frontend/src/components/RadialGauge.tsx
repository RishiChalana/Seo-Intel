// SVG radial gauge, adapted from the Stitch design system's circular-chart.
// value is 0..1; color shifts red -> amber -> green by score band.
interface RadialGaugeProps {
  value: number; // 0..1
  label: string;
  display?: string; // overrides the centered text (e.g. a grade number)
}

function bandColor(value: number): string {
  if (value >= 0.75) return "#006344"; // forest green
  if (value >= 0.5) return "#b8860b"; // amber
  return "#ba1a1a"; // error red
}

export function RadialGauge({ value, label, display }: RadialGaugeProps) {
  const clamped = Math.max(0, Math.min(1, value));
  const pct = Math.round(clamped * 100);
  const color = bandColor(clamped);
  const circumference = 100; // pathLength normalized

  return (
    <div className="flex flex-col items-center">
      <div className="relative h-20 w-20">
        <svg viewBox="0 0 36 36" className="h-20 w-20">
          <circle className="gauge-bg" cx="18" cy="18" r="15.9155" />
          <circle
            className="gauge-ring"
            cx="18"
            cy="18"
            r="15.9155"
            stroke={color}
            pathLength={circumference}
            strokeDasharray={`${pct} ${circumference - pct}`}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-heading text-lg font-bold text-on-surface">
            {display ?? pct}
          </span>
        </div>
      </div>
      <span className="mt-2 text-center text-[11px] font-medium uppercase tracking-wider text-secondary">
        {label}
      </span>
    </div>
  );
}
