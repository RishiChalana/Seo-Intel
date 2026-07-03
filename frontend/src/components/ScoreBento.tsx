import { AlertTriangle, Gauge } from "lucide-react";
import { RadialGauge } from "./RadialGauge";
import type { BriefScore } from "../lib/types";

// Readability is a Flesch-Kincaid grade level, not a 0..1 score. Map it to a
// "goodness" band centered on ~grade 11 (ideal for web long-form) so the gauge
// fill is meaningful, while still displaying the raw grade number.
function readabilityGoodness(grade: number): number {
  return Math.max(0, Math.min(1, 1 - Math.abs(grade - 11) / 11));
}

export function ScoreBento({ score }: { score: BriefScore }) {
  return (
    <div className="rounded-lg border border-outline-variant bg-white p-6 shadow-module">
      <h2 className="mb-6 flex items-center gap-2 font-heading text-xl font-semibold text-on-surface">
        <Gauge size={20} className="text-surface-tint" /> Intelligence Scoring
      </h2>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        <div className="col-span-2 flex items-center justify-center rounded-lg bg-primary-fixed/25 py-2 sm:col-span-1">
          <RadialGauge value={score.overall} label="Overall Score" />
        </div>
        <RadialGauge value={score.keyword_coverage} label="Keyword Coverage" />
        <RadialGauge
          value={score.structure_completeness}
          label="Structure"
        />
        <RadialGauge value={score.eeat_signal_score} label="E-E-A-T Signal" />
        <RadialGauge
          value={readabilityGoodness(score.readability_grade)}
          label="Readability"
          display={score.readability_grade.toFixed(1)}
        />
      </div>

      {score.notes.length > 0 && (
        <div className="mt-5 flex flex-wrap gap-2 border-t border-surface-variant pt-4">
          {score.notes.map((note) => (
            <span
              key={note}
              className="flex items-center gap-1.5 rounded bg-amber/10 px-2.5 py-1 text-xs font-medium text-amber"
            >
              <AlertTriangle size={13} /> {note}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
