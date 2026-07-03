import { Cpu } from "lucide-react";
import { GlowCard } from "./GlowCard";
import type { TokenUsage } from "../lib/types";

// Maps a raw step label (the response-schema class name from the backend) to a
// human-readable pipeline stage.
const STEP_LABELS: Record<string, string> = {
  _ClusterLabelResponse: "Keyword Clustering",
  ContentOutline: "Outline Generation",
};

function prettyStep(label: string): string {
  return STEP_LABELS[label] ?? label;
}

const STEP_COLORS = ["#006344", "#86d7b0", "#b8860b", "#6f7a72"];

export function TelemetryCard({ usage }: { usage: TokenUsage }) {
  const maxStepTokens = Math.max(1, ...usage.by_step.map((s) => s.total_tokens));

  return (
    <GlowCard className="p-6">
      {/* faint tech motif */}
      <Cpu
        size={120}
        className="pointer-events-none absolute -right-4 -top-4 text-primary opacity-[0.04]"
      />
      <h3 className="mb-4 text-sm font-medium uppercase tracking-widest text-secondary">
        Run Telemetry
      </h3>

      <div className="mb-4 flex items-baseline gap-2">
        <span className="font-heading text-4xl font-bold text-on-surface">
          ${usage.estimated_cost_usd.toFixed(4)}
        </span>
        <span className="text-sm text-secondary">est. cost</span>
      </div>

      <div className="space-y-2.5 border-t border-surface-variant py-4 text-sm">
        <Row label="Model" value={usage.model || "—"} />
        <Row label="LLM calls" value={usage.total_calls.toString()} />
        <Row label="Input tokens" value={usage.prompt_tokens.toLocaleString()} />
        <Row
          label="Output tokens"
          value={usage.completion_tokens.toLocaleString()}
        />
        <Row
          label="Total tokens"
          value={usage.total_tokens.toLocaleString()}
          bold
        />
      </div>

      {usage.by_step.length > 0 && (
        <div className="border-t border-surface-variant pt-4">
          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-secondary">
            Cost by stage
          </p>
          <div className="space-y-3">
            {usage.by_step.map((step, i) => (
              <div key={step.label}>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="text-on-surface">
                    {prettyStep(step.label)}
                    <span className="text-secondary"> · {step.calls}×</span>
                  </span>
                  <span className="font-medium text-on-surface">
                    ${step.estimated_cost_usd.toFixed(4)}
                  </span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-surface-container">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${(step.total_tokens / maxStepTokens) * 100}%`,
                      backgroundColor: STEP_COLORS[i % STEP_COLORS.length],
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </GlowCard>
  );
}

function Row({
  label,
  value,
  bold,
}: {
  label: string;
  value: string;
  bold?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-secondary">{label}</span>
      <span
        className={`text-on-surface ${bold ? "font-bold" : "font-medium"}`}
      >
        {value}
      </span>
    </div>
  );
}
