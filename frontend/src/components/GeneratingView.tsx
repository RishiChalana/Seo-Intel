import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Check, Loader2 } from "lucide-react";
import type { PipelineRequest } from "../lib/types";

// The backend pipeline is synchronous (one POST, ~30-45s, no progress stream),
// so we animate the five real graph stages on estimated timing while the
// request is in flight. The last stage holds in a "running" state until App
// swaps to the results view — we never claim "done" before the data is back.
const STAGES = [
  { title: "Research Extraction", detail: "Fetching top competitor pages" },
  { title: "Index (RAG) Construction", detail: "Embedding pages into vector space" },
  { title: "Keyword Gap Analysis", detail: "Clustering candidate keywords by intent" },
  { title: "Brief Outline Generation", detail: "Grounding structure in retrieved context" },
  { title: "Predictive Scoring", detail: "Computing the deterministic rubric" },
];

// Approximate per-stage dwell (ms). Sums to ~34s; the final stage holds.
const DWELL = [7000, 6000, 9000, 9000, 3000];

interface GeneratingViewProps {
  request: PipelineRequest;
  onCancel: () => void;
}

export function GeneratingView({ request, onCancel }: GeneratingViewProps) {
  const [active, setActive] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const timers: ReturnType<typeof setTimeout>[] = [];
    let elapsed = 0;
    // Advance through stages, but stop at the last one (hold until unmount).
    for (let i = 1; i < STAGES.length; i++) {
      elapsed += DWELL[i - 1];
      timers.push(
        setTimeout(() => {
          if (!cancelled) setActive(i);
        }, elapsed),
      );
    }
    return () => {
      cancelled = true;
      timers.forEach(clearTimeout);
    };
  }, []);

  return (
    <div className="mx-auto flex max-w-xl flex-col px-4 pt-20 pb-24">
      <div className="rounded-xl border border-outline-variant bg-white p-8 shadow-module md:p-12">
        <h1 className="text-center font-heading text-3xl font-bold text-on-surface">
          Pipeline Execution
        </h1>
        <p className="mt-2 text-center text-secondary">
          Analyzing{" "}
          <span className="font-medium text-on-surface">“{request.topic}”</span>{" "}
          across {request.max_competitors} competitors
        </p>

        <div className="mt-10 space-y-1">
          {STAGES.map((stage, i) => {
            const done = i < active;
            const running = i === active;
            return (
              <div key={stage.title} className="flex gap-4">
                {/* Icon + connector rail */}
                <div className="flex flex-col items-center">
                  <StageIcon done={done} running={running} />
                  {i < STAGES.length - 1 && (
                    <div
                      className={`w-0.5 flex-1 ${done ? "bg-primary-container" : "bg-surface-variant"}`}
                    />
                  )}
                </div>
                {/* Text */}
                <div className={`pb-8 ${running ? "" : ""}`}>
                  <h3
                    className={`font-heading text-lg font-semibold ${
                      done
                        ? "text-on-surface"
                        : running
                          ? "text-primary"
                          : "text-secondary/50"
                    }`}
                  >
                    {stage.title}
                  </h3>
                  <p
                    className={`text-sm ${running ? "text-secondary" : "text-secondary/50"}`}
                  >
                    {stage.detail}
                    {running ? "…" : ""}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-2 border-t border-surface-variant pt-6 text-center">
          <button
            onClick={onCancel}
            className="text-sm font-medium text-error transition-opacity hover:opacity-70"
          >
            Cancel Execution
          </button>
        </div>
      </div>
    </div>
  );
}

function StageIcon({ done, running }: { done: boolean; running: boolean }) {
  if (done) {
    return (
      <motion.div
        initial={{ scale: 0.6 }}
        animate={{ scale: 1 }}
        className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-container text-white"
      >
        <Check size={18} strokeWidth={3} />
      </motion.div>
    );
  }
  if (running) {
    return (
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-fixed/50 text-primary">
        <Loader2 size={18} className="animate-spin" />
      </div>
    );
  }
  return (
    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-surface-container">
      <div className="h-2 w-2 rounded-full bg-outline/40" />
    </div>
  );
}
