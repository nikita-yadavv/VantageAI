import React, { useState } from 'react';
import { ArrowRight, Loader2, AlertCircle, Sparkles } from 'lucide-react';
import Navbar from './components/Navbar';
import RoleSelector from './components/RoleSelector';
import ResumeUpload from './components/ResumeUpload';
import InterviewRoom from './components/InterviewRoom';
import EvaluationReport from './components/EvaluationReport';
import { startInterviewSession } from './api/client';

export default function App() {
  const [stage, setStage] = useState('setup'); // 'setup', 'interview', 'report'
  const [selectedRole, setSelectedRole] = useState('AI / Machine Learning Engineer');
  const [difficulty, setDifficulty] = useState('intermediate');
  const [parsedResume, setParsedResume] = useState(null);
  
  const [sessionData, setSessionData] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [completedSessionId, setCompletedSessionId] = useState(null);
  
  const [isStarting, setIsStarting] = useState(false);
  const [error, setError] = useState(null);

  const handleStart = async () => {
    if (!parsedResume || !parsedResume.resume_id) {
      setError('Please upload a resume or select a sample candidate to continue.');
      return;
    }

    setIsStarting(true);
    setError(null);

    try {
      const session = await startInterviewSession(
        parsedResume.resume_id,
        selectedRole,
        difficulty,
        5
      );
      setSessionData(session);
      setCurrentQuestion(session.current_question);
      setStage('interview');
    } catch (err) {
      setError(err.message || 'Failed to start interview session');
    } finally {
      setIsStarting(false);
    }
  };

  const handleReset = () => {
    setStage('setup');
    setSessionData(null);
    setCurrentQuestion(null);
    setCompletedSessionId(null);
    setError(null);
  };

  return (
    <div className="min-h-screen flex flex-col text-palette-deep font-sans relative">
      {/* Ambient Animated Glass Mesh Background */}
      <div className="ambient-bg">
        <div className="ambient-orb orb-1" />
        <div className="ambient-orb orb-2" />
        <div className="ambient-orb orb-3" />
      </div>

      <Navbar onReset={handleReset} currentStage={stage} />

      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-8 relative z-10">
        
        {/* STAGE 1: SETUP */}
        {stage === 'setup' && (
          <div className="space-y-6 animate-fade-in">
            {/* Clean Hero */}
            <div className="text-center max-w-xl mx-auto space-y-1.5 pt-2 pb-4">
              <div className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-white/70 backdrop-blur-md border border-palette-heather text-palette-deep text-[11px] font-mono font-medium shadow-sm mb-1">
                <Sparkles className="w-3 h-3 text-palette-plum" />
                <span>Adaptive Technical Screening</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-palette-deep tracking-tight font-display">
                AI Technical Interview Screening
              </h1>
              <p className="text-xs sm:text-sm text-palette-plum">
                Select a target role and upload your resume to begin your adaptive technical assessment.
              </p>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-rose-50/90 backdrop-blur-md border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Glass Boxed Layout */}
            <div className="p-6 sm:p-8 rounded-3xl glass-panel space-y-6">
              <RoleSelector
                selectedRole={selectedRole}
                onSelectRole={setSelectedRole}
                difficulty={difficulty}
                onSelectDifficulty={setDifficulty}
              />

              <div className="pt-2 border-t border-palette-heather/60">
                <ResumeUpload
                  parsedResume={parsedResume}
                  onResumeParsed={(data) => { setParsedResume(data); setError(null); }}
                  onSelectRoleForSample={(role) => setSelectedRole(role)}
                />
              </div>

              <div className="pt-3 border-t border-palette-heather/60 flex items-center justify-between">
                <p className="text-xs text-palette-plum font-medium">
                  {parsedResume ? `Ready for ${parsedResume.parsed_data.candidate_name}` : 'Upload resume to continue'}
                </p>
                <button
                  type="button"
                  onClick={handleStart}
                  disabled={!parsedResume || isStarting}
                  className={`px-6 py-2.5 rounded-xl font-bold text-xs flex items-center gap-2 transition-all shadow-md ${
                    !parsedResume || isStarting
                      ? 'bg-palette-heather/60 text-palette-plum cursor-not-allowed border border-palette-heather/80'
                      : 'bg-[#2F2433] hover:bg-[#48374E] text-white shadow-palette-deep/20 hover:shadow-lg transform active:scale-95'
                  }`}
                >
                  {isStarting ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin text-white" />
                      <span className="text-white">Preparing Interview...</span>
                    </>
                  ) : (
                    <>
                      <span className={!parsedResume ? 'text-palette-plum' : 'text-white'}>Start Interview</span>
                      <ArrowRight className={`w-3.5 h-3.5 ${!parsedResume ? 'text-palette-plum' : 'text-[#D7C9DB]'}`} />
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* STAGE 2: INTERVIEW */}
        {stage === 'interview' && sessionData && currentQuestion && (
          <InterviewRoom
            sessionData={sessionData}
            currentQuestion={currentQuestion}
            onQuestionCompleted={(q) => setCurrentQuestion(q)}
            onSessionFinished={(id) => { setCompletedSessionId(id); setStage('report'); }}
          />
        )}

        {/* STAGE 3: REPORT */}
        {stage === 'report' && completedSessionId && (
          <EvaluationReport
            sessionId={completedSessionId}
            onRestart={handleReset}
          />
        )}
      </main>

      <footer className="border-t border-palette-heather/50 py-4 text-center text-[11px] text-palette-plum font-mono relative z-10 bg-white/40 backdrop-blur-sm">
        <p>VantageAI • Adaptive Technical Screening</p>
      </footer>
    </div>
  );
}
