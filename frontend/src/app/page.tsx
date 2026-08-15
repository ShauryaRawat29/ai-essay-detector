"use client";

import { useState } from "react";
import { analyzeEssay } from "@/lib/api";
import type {
  AnalysisResult,
  EvidenceValue,
  SentenceEvidence,
  SignalEvidence,
} from "@/lib/types";

const MAX_CHARS = 10000;

const STRENGTH_COLOR: Record<EvidenceValue, string> = {
  low: "#3b82f6",
  medium: "#f59e0b",
  high: "#ea580c",
  uncertain: "#8b5cf6",
};

const STRENGTH_LABEL: Record<EvidenceValue, string> = {
  low: "Typical",
  medium: "Moderate signal",
  high: "Strong signal",
  uncertain: "Uncertain",
};

function strengthTint(strength: EvidenceValue): string {
  const rgb: Record<EvidenceValue, string> = {
    low: "59,130,246",
    medium: "245,158,11",
    high: "234,88,12",
    uncertain: "139,92,246",
  };
  return `rgba(${rgb[strength]},0.14)`;
}

export default function Home() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const words = text.trim() ? text.trim().split(/\s+/).length : 0;

  async function handleAnalyze() {
    if (!text.trim() || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await analyzeEssay(text);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
          AI Essay Detector
        </h1>
        <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">
          Evidence-based analysis of machine-like writing signals, sentence by
          sentence. This tool reports measured signals and uncertainty — it does
          not claim to prove whether text was written by an AI.
        </p>
      </header>

      <section aria-label="Essay input">
        <label htmlFor="essay" className="text-sm font-medium text-zinc-700 dark:text-zinc-300">
          Paste an admissions essay
        </label>
        <textarea
          id="essay"
          value={text}
          onChange={(e) => setText(e.target.value.slice(0, MAX_CHARS))}
          placeholder="Paste your essay here…"
          className="mt-2 min-h-64 w-full rounded-lg border border-zinc-300 bg-zinc-50 p-3 text-sm text-zinc-900 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100"
        />
        <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-zinc-500">
            {words} words · {text.length}/{MAX_CHARS} characters
          </p>
          <button
            onClick={handleAnalyze}
            disabled={loading || !text.trim()}
            className="rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            {loading ? "Analyzing… (first run loads the language model)" : "Analyze"}
          </button>
        </div>
      </section>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-950 dark:text-red-300"
        >
          {error}
        </div>
      )}

      {result && <Results result={result} />}
    </main>
  );
}

function Results({ result }: { result: AnalysisResult }) {
  return (
    <section aria-label="Analysis results" className="flex flex-col gap-6">
      <SummaryCard result={result} />
      <SentenceView sentences={result.sentences} />
      <LimitationsNotice limitations={result.limitations} />
    </section>
  );
}

function SummaryCard({ result }: { result: AnalysisResult }) {
  const { summary } = result;
  return (
    <div className="rounded-lg border border-zinc-200 p-5 dark:border-zinc-700">
      <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
        Machine-like signals detected in {summary.signal_sentences} of{" "}
        {summary.sentence_count} sentences
      </h2>
      <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Count label="Strong signal" value={summary.high} strength="high" />
        <Count label="Moderate signal" value={summary.medium} strength="medium" />
        <Count label="Typical" value={summary.low} strength="low" />
        <Count label="Uncertain" value={summary.uncertain} strength="uncertain" />
      </dl>
      <p className="mt-4 text-xs text-zinc-500 dark:text-zinc-400">
        {result.essay_word_count} words · {result.essay_token_count} tokens ·
        length bucket “{result.length_bucket}” (baseline bucket “
        {result.baseline_bucket}”) · features f{result.feature_version} ·
        baselines v{result.baselines_version}
      </p>
    </div>
  );
}

function Count({
  label,
  value,
  strength,
}: {
  label: string;
  value: number;
  strength: EvidenceValue;
}) {
  return (
    <div className="rounded bg-zinc-50 p-3 dark:bg-zinc-800">
      <dt className="text-xs text-zinc-500 dark:text-zinc-400">{label}</dt>
      <dd
        className="mt-1 text-2xl font-semibold"
        style={{ color: STRENGTH_COLOR[strength] }}
      >
        {value}
      </dd>
    </div>
  );
}

function SentenceView({ sentences }: { sentences: SentenceEvidence[] }) {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <div className="flex flex-col gap-1.5">
      <h3 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
        Sentence-level evidence
      </h3>
      <p className="text-xs text-zinc-500">
        Tap a sentence to see which measured features deviate from the human
        baseline distribution.
      </p>
      <ol className="flex flex-col gap-1.5">
        {sentences.map((sentence) => (
          <SentenceRow
            key={sentence.index}
            sentence={sentence}
            open={open === sentence.index}
            onToggle={() =>
              setOpen(open === sentence.index ? null : sentence.index)
            }
          />
        ))}
      </ol>
    </div>
  );
}

function SentenceRow({
  sentence,
  open,
  onToggle,
}: {
  sentence: SentenceEvidence;
  open: boolean;
  onToggle: () => void;
}) {
  const flagged = sentence.signal_count > 0;
  return (
    <li className="rounded-lg border border-zinc-200 dark:border-zinc-700">
      <button
        onClick={onToggle}
        aria-expanded={open}
        aria-label={`Sentence ${sentence.index + 1}: ${STRENGTH_LABEL[sentence.evidence_strength]}`}
        className="w-full rounded-lg p-3 text-left transition hover:opacity-90"
        style={{
          backgroundColor: strengthTint(sentence.evidence_strength),
        }}
      >
        <span className="flex items-start gap-2">
          <span
            className="mt-0.5 inline-block h-3 w-3 shrink-0 rounded-full"
            style={{ backgroundColor: STRENGTH_COLOR[sentence.evidence_strength] }}
            aria-hidden
          />
          <span className="flex-1 text-sm text-zinc-800 dark:text-zinc-200">
            {sentence.text}
          </span>
          <span
            className="mt-0.5 shrink-0 rounded px-2 py-0.5 text-[11px] font-medium text-white"
            style={{ backgroundColor: STRENGTH_COLOR[sentence.evidence_strength] }}
          >
            {STRENGTH_LABEL[sentence.evidence_strength]}
            {flagged ? ` · ${sentence.signal_count} signals` : ""}
          </span>
        </span>
      </button>
      {open && <SignalList signals={sentence.signals} summary={sentence.summary} />}
    </li>
  );
}

function SignalList({
  signals,
  summary,
}: {
  signals: SignalEvidence[];
  summary: string;
}) {
  const notable = signals.filter((s) => s.evidence !== "low").slice(0, 5);
  const shown = notable.length > 0 ? notable : signals.slice(0, 3);
  return (
    <div className="border-t border-zinc-200 p-3 dark:border-zinc-700">
      <p className="text-sm text-zinc-700 dark:text-zinc-300">{summary}</p>
      {shown.length === 0 ? (
        <p className="mt-2 text-xs text-zinc-500">
          No features could be compared to a baseline.
        </p>
      ) : (
        <table className="mt-2 w-full text-xs">
          <thead>
            <tr className="text-left text-zinc-500 dark:text-zinc-400">
              <th className="py-1 pr-2 font-medium">Feature</th>
              <th className="py-1 pr-2 font-medium">Measured</th>
              <th className="py-1 pr-2 font-medium">Human baseline</th>
              <th className="py-1 font-medium">Deviation</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((signal) => (
              <tr
                key={signal.feature}
                className="border-t border-zinc-100 dark:border-zinc-800"
              >
                <td className="py-1 pr-2 font-mono text-zinc-700 dark:text-zinc-300">
                  {signal.feature}
                </td>
                <td className="py-1 pr-2 font-mono text-zinc-700 dark:text-zinc-300">
                  {signal.value.toFixed(2)}
                </td>
                <td className="py-1 pr-2 font-mono text-zinc-500 dark:text-zinc-400">
                  {signal.baseline_mean.toFixed(2)} ± {signal.baseline_std.toFixed(2)}
                </td>
                <td
                  className="py-1 font-medium"
                  style={{ color: STRENGTH_COLOR[signal.evidence] }}
                >
                  {signal.z_score === null
                    ? "n/a"
                    : `${signal.z_score >= 0 ? "+" : ""}${signal.z_score.toFixed(1)}σ ${signal.direction}`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function LimitationsNotice({ limitations }: { limitations: string[] }) {
  return (
    <div className="rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950">
      <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-200">
        Limitations
      </h3>
      <ul className="mt-2 flex list-disc flex-col gap-1 pl-5 text-xs text-amber-800 dark:text-amber-300">
        {limitations.map((limit, i) => (
          <li key={i}>{limit}</li>
        ))}
      </ul>
    </div>
  );
}