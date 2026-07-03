import { useState } from "react";
import {
  ArrowRight,
  BarChart3,
  Cpu,
  Search,
  Target,
  Users,
  CircleDollarSign,
  AlertCircle,
} from "lucide-react";
import type { PipelineRequest } from "../lib/types";

interface TopicInputProps {
  onSubmit: (req: PipelineRequest) => void;
  error: string | null;
}

const TRUST_CHIPS = [
  { icon: Cpu, label: "RAG over full competitor pages" },
  { icon: BarChart3, label: "Deterministic scoring" },
  { icon: CircleDollarSign, label: "Token & cost tracked" },
];

export function TopicInput({ onSubmit, error }: TopicInputProps) {
  const [topic, setTopic] = useState("");
  const [competitors, setCompetitors] = useState(3);
  const [audience, setAudience] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (topic.trim().length < 3) return;
    onSubmit({
      topic: topic.trim(),
      max_competitors: competitors,
      target_audience: audience.trim() || null,
    });
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col items-center px-4 pt-16 pb-24 md:pt-24">
      <h1 className="text-center font-heading text-4xl font-bold leading-tight tracking-tight text-brand-deep md:text-5xl">
        Generate a competitor-grounded content brief
      </h1>
      <p className="mt-4 text-center text-lg text-secondary">
        Enter your target topic to begin the AI-driven analysis.
      </p>

      {error && (
        <div className="mt-6 flex w-full items-start gap-2 rounded-lg border border-error-container bg-error-container/40 px-4 py-3 text-sm text-on-error-container">
          <AlertCircle size={18} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="mt-8 w-full rounded-xl border border-outline-variant bg-white p-6 shadow-module md:p-8"
      >
        <label className="mb-2 flex items-center gap-2 text-sm font-medium text-on-surface">
          <Search size={16} className="text-secondary" /> Topic
        </label>
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="email marketing automation"
          autoFocus
          className="mb-6 w-full rounded border border-outline-variant bg-white px-4 py-3 text-on-surface outline-none transition-all placeholder:text-secondary/60 focus:border-primary focus:ring-2 focus:ring-primary/20"
        />

        <label className="mb-2 flex items-center gap-2 text-sm font-medium text-on-surface">
          <Users size={16} className="text-secondary" /> Competitors to analyze
        </label>
        <select
          value={competitors}
          onChange={(e) => setCompetitors(Number(e.target.value))}
          className="mb-6 w-full appearance-none rounded border border-outline-variant bg-white px-4 py-3 text-on-surface outline-none transition-all focus:border-primary focus:ring-2 focus:ring-primary/20"
        >
          {[1, 2, 3, 4, 5, 6, 8, 10].map((n) => (
            <option key={n} value={n}>
              {n} Competitor{n > 1 ? "s" : ""}
              {n === 3 ? " (Recommended)" : ""}
            </option>
          ))}
        </select>

        <label className="mb-2 flex items-center gap-2 text-sm font-medium text-on-surface">
          <Target size={16} className="text-secondary" /> Target audience{" "}
          <span className="font-normal text-secondary">(Optional)</span>
        </label>
        <input
          type="text"
          value={audience}
          onChange={(e) => setAudience(e.target.value)}
          placeholder="e.g., Marketing Managers, B2B SaaS"
          className="mb-6 w-full rounded border border-outline-variant bg-white px-4 py-3 text-on-surface outline-none transition-all placeholder:text-secondary/60 focus:border-primary focus:ring-2 focus:ring-primary/20"
        />

        <button
          type="submit"
          disabled={topic.trim().length < 3}
          className="flex w-full items-center justify-center gap-2 rounded bg-primary py-3.5 font-medium text-white transition-colors hover:bg-brand-deep disabled:cursor-not-allowed disabled:opacity-40"
        >
          Generate Brief <ArrowRight size={18} />
        </button>
      </form>

      <div className="mt-6 flex flex-wrap justify-center gap-3">
        {TRUST_CHIPS.map(({ icon: Icon, label }) => (
          <span
            key={label}
            className="flex items-center gap-1.5 rounded-full bg-primary-fixed/40 px-3 py-1.5 text-sm font-medium text-brand-deep"
          >
            <Icon size={15} /> {label}
          </span>
        ))}
      </div>
    </div>
  );
}
