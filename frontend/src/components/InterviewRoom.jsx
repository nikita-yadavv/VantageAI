import React, { useState } from 'react';
import { Send, CheckCircle2, Loader2, ArrowRight, Zap, Sparkles } from 'lucide-react';
import { submitAnswer } from '../api/client';

const DEMO_ANSWERS = {
  'Decision Trees': "Entropy is defined as -sum(p_i * log2(p_i)), measuring uncertainty in dataset S. Information Gain is the reduction in entropy when partitioning on attribute A: Gain(S, A) = Entropy(S) - sum((|S_v|/|S|) * Entropy(S_v)). C4.5 addresses ID3's bias toward high-cardinality attributes by using Gain Ratio = Gain(S, A) / SplitInformation(S, A) to penalize fragmented splits.",
  'Neural Networks': "Backpropagation calculates loss gradients across layers via the chain rule: dL/dw = (dL/da) * (da/dz) * (dz/dw). Sigmoid suffers from vanishing gradients because its derivative maxes out at 0.25, while ReLU f(x)=max(0,x) maintains a constant gradient of 1 for positive activations, avoiding saturation in deep architectures.",
  'Model Generalization': "The Bias-Variance tradeoff balances underfitting and overfitting: Expected Error = Bias^2 + Variance + Noise. L1 regularization adds lambda*|w| which drives weights to exact zeros producing sparse feature selection, whereas L2 adds lambda*||w||^2 to shrink weights continuously and reduce model variance.",
  'Data Preprocessing': "Data leakage occurs when test set distribution leaks into the training pipeline. Scikit-Learn Pipelines prevent this by ensuring transformations (e.g., StandardScaler) execute fit() strictly on the training folds and only transform() on test folds during cross-validation.",
  'Distributed Caching': "We implement Cache-Aside with Redis: read requests query cache first; on a miss, fetch from DB and write to Redis with a TTL. To prevent cache stampedes on hot keys, we use distributed mutex locks (singleflight) and apply jitter to TTL expirations. On updates, we invalidate the cache key.",
  'Database Sharding': "Sharding horizontally partitions data across multiple database instances using Consistent Hashing on the shard key. Virtual nodes on the hash ring ensure uniform distribution and guarantee that adding or removing a node only requires migrating K/N keys rather than re-indexing the whole cluster.",
  'Attention Mechanisms': "Scaled Dot-Product Attention is computed as softmax((Q * K^T) / sqrt(d_k)) * V. The scaling factor 1/sqrt(d_k) counteracts large dot products in high dimensions that would otherwise push the softmax into vanishing gradient regions with near-zero derivatives."
};

export default function InterviewRoom({ 
  sessionData, 
  currentQuestion, 
  onQuestionCompleted, 
  onSessionFinished 
}) {
  const [answerText, setAnswerText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [lastFeedback, setLastFeedback] = useState(null);

  // Quick fill demo answer
  const handleQuickFill = () => {
    const topic = currentQuestion.topic || '';
    let matchedAnswer = null;
    
    for (const [key, ans] of Object.entries(DEMO_ANSWERS)) {
      if (topic.toLowerCase().includes(key.toLowerCase()) || currentQuestion.question_text.toLowerCase().includes(key.toLowerCase())) {
        matchedAnswer = ans;
        break;
      }
    }

    if (!matchedAnswer) {
      matchedAnswer = `From a foundational and engineering perspective, ${currentQuestion.topic} balances mathematical guarantees with practical scalability. We formulate the objective function, analyze gradient bounds and edge conditions, and structure the implementation to minimize computational overhead while guaranteeing convergence.`;
    }

    setAnswerText(matchedAnswer);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!answerText.trim() || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const feedback = await submitAnswer(sessionData.session_id, currentQuestion.id, answerText);
      setLastFeedback(feedback);
    } catch (err) {
      setError(err.message || 'Failed to submit response');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleNextStep = () => {
    if (!lastFeedback) return;

    if (lastFeedback.is_completed) {
      onSessionFinished(sessionData.session_id);
    } else if (lastFeedback.next_question) {
      setLastFeedback(null);
      setAnswerText('');
      onQuestionCompleted(lastFeedback.next_question);
    }
  };

  const progressPercent = Math.round((currentQuestion.order_index / sessionData.total_questions) * 100);

  return (
    <div className="max-w-3xl mx-auto space-y-5 animate-fade-in">
      
      {/* Progress Header */}
      <div className="flex items-center justify-between text-xs font-semibold text-palette-plum">
        <span>Question {currentQuestion.order_index} of {sessionData.total_questions}</span>
        <span className="font-mono text-palette-deep">{sessionData.target_role}</span>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-palette-heather/50 rounded-full h-1.5 overflow-hidden">
        <div 
          className="bg-palette-deep h-full transition-all duration-300 rounded-full"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Question Card */}
      <div className="p-6 sm:p-8 rounded-3xl glass-panel space-y-5">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/80 border border-palette-heather/80 text-xs font-semibold text-palette-deep shadow-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-palette-plum"></span>
            <span>Topic: {currentQuestion.topic}</span>
          </div>
          <h2 className="text-lg sm:text-xl font-bold text-palette-deep leading-relaxed">
            {currentQuestion.question_text}
          </h2>
        </div>

        {/* Answer Form */}
        <form onSubmit={handleSubmit} className="space-y-4 pt-1">
          {!lastFeedback && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-bold text-palette-deep">
                  Technical Response:
                </label>
                <button
                  type="button"
                  onClick={handleQuickFill}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-white/90 hover:bg-white border border-palette-heather text-xs font-semibold text-palette-deep transition-all shadow-xs hover:border-palette-mauve"
                  title="Insert calibrated response for demo and testing"
                >
                  <Zap className="w-3.5 h-3.5 text-palette-plum" />
                  <span>Quick Fill (Demo/Testing)</span>
                </button>
              </div>

              <textarea
                rows={5}
                disabled={isSubmitting}
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                placeholder="Type your technical response here or click 'Quick Fill (Demo/Testing)'..."
                className="w-full p-4 rounded-2xl glass-input text-palette-deep text-sm leading-relaxed placeholder-palette-plum/60 resize-y transition-all"
              />
            </div>
          )}

          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700">
              {error}
            </div>
          )}

          {/* Feedback Card */}
          {lastFeedback && (
            <div className="p-5 sm:p-6 rounded-2xl bg-white/80 border border-palette-heather/90 space-y-3.5 animate-fade-in shadow-sm backdrop-blur-md">
              <div className="flex items-center justify-between text-xs font-bold text-palette-deep pb-2 border-b border-palette-heather/50">
                <span className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span className="text-sm font-bold text-palette-deep">Evaluation Assessment</span>
                </span>
                <span className="font-mono bg-palette-deep text-palette-lightest px-3 py-1 rounded-full text-xs font-bold shadow-xs">
                  Score: {lastFeedback.score}/10
                </span>
              </div>
              <p className="text-sm text-palette-deep leading-relaxed bg-palette-lightest/80 p-3.5 rounded-xl border border-palette-heather/60">
                {lastFeedback.feedback}
              </p>
              
              <div className="flex justify-end pt-1">
                <button
                  type="button"
                  onClick={handleNextStep}
                  className="px-6 py-2.5 rounded-xl font-bold text-xs bg-palette-deep hover:bg-palette-plum text-palette-lightest flex items-center gap-2 shadow-md shadow-palette-deep/15 transition-all"
                >
                  <span>{lastFeedback.is_completed ? 'View Assessment Results' : 'Next Question'}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-palette-mauve" />
                </button>
              </div>
            </div>
          )}

          {!lastFeedback && (
            <div className="flex justify-end pt-1">
              <button
                type="submit"
                disabled={isSubmitting || !answerText.trim()}
                className="px-5 py-2.5 rounded-xl font-bold text-xs bg-palette-deep hover:bg-palette-plum text-palette-lightest disabled:opacity-40 flex items-center gap-2 transition-all shadow-sm"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Evaluating...</span>
                  </>
                ) : (
                  <>
                    <span>Submit Answer</span>
                    <Send className="w-3.5 h-3.5 text-palette-mauve" />
                  </>
                )}
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
