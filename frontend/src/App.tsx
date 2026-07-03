import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Header } from "./components/Header";
import { TopicInput } from "./components/TopicInput";
import { GeneratingView } from "./components/GeneratingView";
import { Dashboard } from "./components/Dashboard";
import { generateBrief, ApiError } from "./lib/api";
import type { ContentBrief, PipelineRequest } from "./lib/types";

type View = "input" | "generating" | "results";

export default function App() {
  const [view, setView] = useState<View>("input");
  const [brief, setBrief] = useState<ContentBrief | null>(null);
  const [request, setRequest] = useState<PipelineRequest | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(req: PipelineRequest) {
    setError(null);
    setRequest(req);
    setView("generating");
    try {
      const result = await generateBrief(req);
      setBrief(result);
      setView("results");
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Something went wrong.";
      setError(message);
      setView("input");
    }
  }

  function handleReset() {
    setBrief(null);
    setView("input");
  }

  return (
    <div className="min-h-screen bg-surface-paper">
      <Header
        showNav={view === "results"}
        topic={brief?.topic}
        onNewBrief={handleReset}
      />
      <AnimatePresence mode="wait">
        {view === "input" && (
          <motion.main
            key="input"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <TopicInput onSubmit={handleSubmit} error={error} />
          </motion.main>
        )}

        {view === "generating" && request && (
          <motion.main
            key="generating"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            <GeneratingView request={request} onCancel={handleReset} />
          </motion.main>
        )}

        {view === "results" && brief && (
          <motion.main
            key="results"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
          >
            <Dashboard brief={brief} onNewBrief={handleReset} />
          </motion.main>
        )}
      </AnimatePresence>
    </div>
  );
}
