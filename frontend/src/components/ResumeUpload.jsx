import React, { useState, useRef } from 'react';
import { Upload, FileText, Check, Loader2, Sparkles } from 'lucide-react';
import { uploadResumeFile, parseResumeText } from '../api/client';

const SAMPLES = [
  {
    name: 'Alex Mercer',
    role: 'AI / Machine Learning Engineer',
    label: 'Sample: AI/ML Engineer',
    rawText: `Alex Mercer | AI Engineer | Skills: PyTorch, Transformers, Backpropagation, Decision Trees, SVM, Q-Learning, RAG, ChromaDB, Docker, Cross-Validation`
  },
  {
    name: 'Jordan Hayes',
    role: 'Backend Engineer',
    label: 'Sample: Backend Engineer',
    rawText: `Jordan Hayes | Backend Engineer | Skills: Python, FastAPI, AsyncIO, PostgreSQL, Redis, Cache-Aside, Kafka, Sharding, Consistent Hashing, Docker`
  },
  {
    name: 'Priya Sharma',
    role: 'Data Scientist',
    label: 'Sample: Data Scientist',
    rawText: `Priya Sharma | Data Scientist | Skills: Scikit-Learn Pipelines, ColumnTransformer, Pandas, SMOTE, Class Imbalance, XGBoost, Model Drift, PSI`
  }
];

export default function ResumeUpload({ parsedResume, onResumeParsed, onSelectRoleForSample }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileUpload = async (file) => {
    if (!file) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await uploadResumeFile(file);
      onResumeParsed(response);
    } catch (err) {
      setError(err.message || 'Error processing resume');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSampleSelect = async (sample) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await parseResumeText(
        sample.rawText, 
        sample.name, 
        `${sample.name.toLowerCase().replace(' ', '.')}@example.com`, 
        `${sample.name.toLowerCase().replace(' ', '_')}.txt`
      );
      onResumeParsed(response);
      if (onSelectRoleForSample) {
        onSelectRoleForSample(sample.role);
      }
    } catch (err) {
      setError(err.message || 'Error parsing sample');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-xs font-bold uppercase tracking-wider text-palette-plum">
            2. Upload Resume
          </label>
          <div className="flex items-center gap-1.5 text-xs text-palette-plum">
            <span>Quick fill:</span>
            {SAMPLES.map((s, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSampleSelect(s)}
                className="px-2 py-0.5 rounded bg-white hover:bg-palette-lilac border border-palette-heather text-[11px] font-semibold text-palette-deep transition-all"
              >
                {s.name.split(' ')[0]}
              </button>
            ))}
          </div>
        </div>

        {/* Dropzone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragging(false);
            if (e.dataTransfer.files?.[0]) handleFileUpload(e.dataTransfer.files[0]);
          }}
          onClick={() => fileInputRef.current?.click()}
          className={`p-6 rounded-xl border-2 border-dashed cursor-pointer text-center transition-all ${
            isDragging
              ? 'border-palette-deep bg-palette-lilac/40'
              : 'border-palette-heather hover:border-palette-mauve bg-white hover:bg-palette-lilac/10'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
          />

          {isLoading ? (
            <div className="flex items-center justify-center gap-2 py-2 text-xs font-semibold text-palette-deep">
              <Loader2 className="w-4 h-4 animate-spin text-palette-deep" />
              <span>Analyzing resume...</span>
            </div>
          ) : parsedResume ? (
            <div className="flex items-center justify-center gap-2 text-xs text-palette-deep font-semibold">
              <Check className="w-4 h-4 text-emerald-600" />
              <span>Loaded: {parsedResume.parsed_data.candidate_name} ({parsedResume.parsed_data.skills.length} skills parsed)</span>
            </div>
          ) : (
            <div className="space-y-1">
              <Upload className="w-5 h-5 mx-auto text-palette-plum" />
              <p className="text-xs font-semibold text-palette-deep">
                Drop your resume here, or <span className="underline text-palette-plum">browse</span>
              </p>
              <p className="text-[10px] text-palette-plum">PDF or TXT format</p>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700">
          {error}
        </div>
      )}

      {/* Extracted Skills Chips */}
      {parsedResume && parsedResume.parsed_data && (
        <div className="p-3 rounded-xl bg-white border border-palette-heather space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-palette-deep">{parsedResume.parsed_data.candidate_name}</span>
            <span className="text-[11px] text-palette-plum font-mono">{parsedResume.parsed_data.skills.length} skills detected</span>
          </div>
          <div className="flex flex-wrap gap-1 max-h-16 overflow-y-auto">
            {parsedResume.parsed_data.skills.map((skill, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 rounded text-[10px] font-mono bg-palette-lilac/70 border border-palette-heather text-palette-deep"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
