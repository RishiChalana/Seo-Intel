import { PlusCircle, Radar } from "lucide-react";

export function ContentGaps({ gaps }: { gaps: string[] }) {
  if (gaps.length === 0) return null;
  return (
    <div className="rounded-lg border border-l-4 border-outline-variant border-l-surface-tint bg-white p-6 shadow-module">
      <h3 className="mb-2 flex items-center gap-2 font-heading text-xl font-semibold text-on-surface">
        <Radar size={20} className="text-surface-tint" /> Content Gaps
      </h3>
      <p className="mb-4 text-sm text-secondary">
        Topics the outline covers that a naive brief would miss — your
        competitive differentiators.
      </p>
      <ul className="space-y-2.5 text-sm text-on-surface">
        {gaps.map((gap) => (
          <li key={gap} className="flex items-start gap-2">
            <PlusCircle size={17} className="mt-0.5 shrink-0 text-surface-tint" />
            <span>{gap}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
