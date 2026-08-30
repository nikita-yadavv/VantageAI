import React, { useState, useEffect } from 'react';
import { Award, CheckCircle2, AlertTriangle, Download, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react';
import { getEvaluationReport } from '../api/client';

export default function EvaluationReport({ sessionId, onRestart }) {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedIndex, setExpandedIndex] = useState(null);

  useEffect(() => {
    async function fetchReport() {
      try {
        const data = await getEvaluationReport(sessionId);
        setReport(data);
      } catch (err) {
        setError(err.message || 'Failed to load report');
      } finally {
        setLoading(false);
      }
    }
    fetchReport();
  }, [sessionId]);

  const handleDownloadJSON = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `assessment_report_${sessionId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="max-w-xl mx-auto p-12 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-palette-deep border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs font-semibold text-palette-deep">Generating assessment insights...</p>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-md mx-auto p-6 rounded-2xl bg-white border border-palette-heather text-center space-y-3">
        <p className="text-xs text-rose-600 font-semibold">{error || 'Session report not available'}</p>
        <button
          onClick={onRestart}
          className="px-4 py-2 rounded-xl bg-palette-deep text-xs font-semibold text-palette-lightest"
        >
          Start New Assessment
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fade-in pb-8">
      
      {/* Header Card */}
      <div className="p-6 sm:p-7 rounded-3xl glass-panel flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider text-palette-plum font-semibold">
            Assessment Results
          </span>
          <h1 className="text-xl sm:text-2xl font-bold text-palette-deep font-display mt-0.5">
            {report.candidate_name}
          </h1>
          <p className="text-xs text-palette-plum mt-0.5">
            Role: <span className="font-semibold text-palette-deep">{report.target_role}</span>
          </p>
        </div>

        <div className="flex items-center gap-3 bg-white/80 p-3 rounded-2xl border border-palette-heather/80 shadow-sm backdrop-blur-sm">
          <div className="text-right">
            <div className="text-[10px] font-bold text-palette-plum uppercase font-mono">Score</div>
            <div className="text-2xl font-extrabold text-palette-deep font-mono">
              {report.overall_score}<span className="text-xs text-palette-plum font-normal">/100</span>
            </div>
          </div>
          <div className="h-8 w-px bg-palette-heather"></div>
          <div>
            <div className="text-[10px] font-bold text-palette-plum uppercase font-mono">Rating</div>
            <div className="text-xs font-bold text-palette-deep mt-0.5">
              {report.recommendation}
            </div>
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="p-6 rounded-3xl glass-card space-y-2">
        <h3 className="text-xs font-bold uppercase tracking-wider text-palette-plum font-mono">
          Executive Summary
        </h3>
        <p className="text-xs text-palette-deep leading-relaxed bg-white/70 p-3.5 rounded-xl border border-palette-heather/80">
          {report.executive_summary}
        </p>
      </div>

      {/* Breakdown Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Category Scores */}
        <div className="p-6 rounded-3xl glass-card space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-palette-plum font-mono">
            Topic Breakdown
          </h3>
          <div className="space-y-2.5">
            {Object.entries(report.category_scores).map(([cat, score], idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-medium text-palette-deep">{cat}</span>
                  <span className="font-bold text-palette-deep font-mono">{score}%</span>
                </div>
                <div className="w-full bg-palette-heather/50 rounded-full h-1.5 overflow-hidden">
                  <div className="h-full bg-palette-deep rounded-full" style={{ width: `${score}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Strengths & Growth */}
        <div className="p-6 rounded-3xl glass-card space-y-3">
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-palette-plum font-mono mb-2">
              Key Strengths
            </h3>
            <ul className="space-y-1.5">
              {report.key_strengths.slice(0, 2).map((s, i) => (
                <li key={i} className="text-xs text-palette-deep flex items-start gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-palette-deep mt-1 flex-shrink-0" />
                  <span>{s}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="pt-2 border-t border-palette-heather/60">
            <h3 className="text-xs font-bold uppercase tracking-wider text-palette-plum font-mono mb-2">
              Areas for Improvement
            </h3>
            <ul className="space-y-1.5">
              {report.areas_for_growth.slice(0, 2).map((g, i) => (
                <li key={i} className="text-xs text-palette-deep flex items-start gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-palette-plum mt-1 flex-shrink-0" />
                  <span>{g}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Question Review List */}
      <div className="p-6 rounded-3xl glass-card space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-palette-plum font-mono">
          Questions Review
        </h3>
        <div className="space-y-2.5">
          {report.questions_review.map((q, idx) => {
            const isExp = expandedIndex === idx;
            return (
              <div key={idx} className="rounded-2xl border border-palette-heather/80 overflow-hidden text-xs bg-white/60 backdrop-blur-sm shadow-sm">
                <div
                  onClick={() => setExpandedIndex(isExp ? null : idx)}
                  className="p-3.5 bg-palette-lightest/80 flex items-center justify-between cursor-pointer hover:bg-white/90 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-palette-deep">Q{q.order_index}</span>
                    <span className="font-semibold text-palette-deep">{q.topic}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-palette-deep bg-white border border-palette-heather px-2 py-0.5 rounded shadow-xs">
                      {q.score}/10
                    </span>
                    {isExp ? <ChevronUp className="w-3.5 h-3.5 text-palette-plum" /> : <ChevronDown className="w-3.5 h-3.5 text-palette-plum" />}
                  </div>
                </div>

                {isExp && (
                  <div className="p-4 bg-white/90 space-y-2.5 border-t border-palette-heather/80">
                    <div>
                      <span className="font-bold text-palette-plum block text-[10px] uppercase">Question:</span>
                      <p className="text-palette-deep font-medium mt-0.5">{q.question_text}</p>
                    </div>
                    <div>
                      <span className="font-bold text-palette-plum block text-[10px] uppercase">Your Answer:</span>
                      <p className="text-palette-deep bg-palette-lightest/80 p-2.5 rounded-lg border border-palette-heather/80 mt-0.5">{q.candidate_answer}</p>
                    </div>
                    <div>
                      <span className="font-bold text-palette-plum block text-[10px] uppercase">Feedback:</span>
                      <p className="text-palette-deep mt-0.5">{q.feedback}</p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between pt-2">
        <button
          onClick={onRestart}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-white hover:bg-palette-lilac border border-palette-heather text-palette-deep flex items-center gap-1.5"
        >
          <RotateCcw className="w-3.5 h-3.5 text-palette-plum" />
          <span>New Assessment</span>
        </button>

        <button
          onClick={handleDownloadJSON}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-palette-deep hover:bg-palette-plum text-palette-lightest flex items-center gap-1.5 shadow-sm"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Export JSON</span>
        </button>
      </div>
    </div>
  );
}
