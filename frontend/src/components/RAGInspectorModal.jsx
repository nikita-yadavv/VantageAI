import React, { useState, useEffect } from 'react';
import { X, Search, BookOpen, Layers, CheckCircle2, Loader2, Sparkles } from 'lucide-react';
import { queryRAGInspector, getSupportedRoles } from '../api/client';

export default function RAGInspectorModal({ isOpen, onClose }) {
  const [roles, setRoles] = useState([]);
  const [selectedRole, setSelectedRole] = useState('AI & Machine Learning Systems');
  const [searchQuery, setSearchQuery] = useState('Backpropagation gradient descent activation');
  const [retrievedChunks, setRetrievedChunks] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      getSupportedRoles()
        .then(setRoles)
        .catch(console.error);
      handleSearch('Backpropagation gradient descent activation', 'AI & Machine Learning Systems');
    }
  }, [isOpen]);

  const handleSearch = async (queryToUse, roleToUse) => {
    const q = queryToUse !== undefined ? queryToUse : searchQuery;
    const r = roleToUse !== undefined ? roleToUse : selectedRole;
    if (!q.trim()) return;

    setIsLoading(true);
    try {
      const res = await queryRAGInspector(q, r);
      setRetrievedChunks(res.chunks || []);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-palette-deep/50 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-4xl max-h-[85vh] rounded-2xl bg-white border border-palette-heather shadow-2xl flex flex-col overflow-hidden">
        
        {/* Header */}
        <div className="p-5 border-b border-palette-heather flex items-center justify-between bg-palette-lightest">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-palette-lilac text-palette-deep border border-palette-heather">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-palette-deep flex items-center gap-2 font-display">
                <span>RAG Knowledge Corpus & Chunking Inspector</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-palette-lilac border border-palette-heather text-palette-deep font-semibold">Active Corpus</span>
              </h2>
              <p className="text-xs text-palette-plum">
                Inspect how domain textbook literature is chunked, indexed, and semantically retrieved.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-palette-plum hover:text-palette-deep hover:bg-palette-lilac transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Query Controls */}
        <div className="p-5 border-b border-palette-heather space-y-3 bg-palette-lilac/30">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-1">
              <label className="text-[10px] font-bold text-palette-plum uppercase tracking-wider block mb-1">
                Domain Specialization
              </label>
              <select
                value={selectedRole}
                onChange={(e) => {
                  setSelectedRole(e.target.value);
                  handleSearch(searchQuery, e.target.value);
                }}
                className="w-full p-2.5 rounded-xl bg-white border border-palette-heather text-xs text-palette-deep focus:border-palette-deep font-medium shadow-sm"
              >
                <option value="AI & Machine Learning Systems">AI & Machine Learning Systems</option>
                <option value="Applied Data Science & Predictive ML">Applied Data Science & Predictive ML</option>
                <option value="Distributed Systems & Backend Architecture">Distributed Systems & Backend Architecture</option>
                <option value="Theoretical ML & Statistical Foundations">Theoretical ML & Statistical Foundations</option>
              </select>
            </div>

            <div className="sm:col-span-2">
              <label className="text-[10px] font-bold text-palette-plum uppercase tracking-wider block mb-1">
                Semantic Query / Domain Principles
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="E.g. Caching patterns, Information Gain, Bellman Optimality..."
                  className="flex-1 p-2.5 rounded-xl bg-white border border-palette-heather text-xs text-palette-deep focus:border-palette-deep placeholder-palette-plum/60 shadow-sm"
                />
                <button
                  type="button"
                  onClick={() => handleSearch()}
                  disabled={isLoading}
                  className="px-4 py-2.5 rounded-xl bg-palette-deep hover:bg-palette-plum text-xs font-bold text-palette-lightest flex items-center gap-1.5 shadow-sm disabled:opacity-50 transition-all"
                >
                  {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                  <span>Retrieve</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Retrieval Results List */}
        <div className="p-5 flex-1 overflow-y-auto space-y-3 bg-palette-lightest">
          <div className="flex items-center justify-between text-xs text-palette-plum font-mono">
            <span>Retrieved Chunks ({retrievedChunks.length})</span>
            <span>Sorted by TF-IDF Semantic Relevance</span>
          </div>

          {isLoading ? (
            <div className="py-12 text-center space-y-2">
              <Loader2 className="w-6 h-6 text-palette-deep animate-spin mx-auto" />
              <p className="text-xs text-palette-plum">Scanning vector matrices & computing cosine relevance scores...</p>
            </div>
          ) : retrievedChunks.length === 0 ? (
            <div className="py-8 text-center text-xs text-palette-plum">
              No matching knowledge base chunks found for this query.
            </div>
          ) : (
            retrievedChunks.map((chunk, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl bg-white border border-palette-heather space-y-2 font-mono text-xs shadow-sm"
              >
                <div className="flex items-center justify-between border-b border-palette-heather pb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded-full bg-palette-lilac text-palette-deep border border-palette-heather text-[10px] font-bold">
                      Chunk #{idx + 1}
                    </span>
                    <span className="text-palette-deep font-bold">{chunk.source_book}</span>
                    <span className="text-palette-plum">→</span>
                    <span className="text-palette-plum font-medium">{chunk.chapter_title}</span>
                  </div>
                  <div className="text-[11px] text-palette-deep bg-palette-lilac px-2.5 py-0.5 rounded-full border border-palette-heather font-bold">
                    Score: {chunk.relevance_score}
                  </div>
                </div>

                <p className="text-palette-deep whitespace-pre-wrap leading-relaxed text-[11px] bg-palette-lilac/20 p-3 rounded-lg border border-palette-heather font-sans">
                  {chunk.content}
                </p>

                {chunk.metadata && (
                  <div className="flex items-center gap-4 text-[10px] text-palette-plum pt-1">
                    <span>File: {chunk.metadata.file}</span>
                    <span>Words: {chunk.metadata.word_count}</span>
                    <span>ID: {chunk.chunk_id}</span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-palette-heather bg-white flex items-center justify-between text-xs text-palette-plum">
          <span className="font-medium">Knowledge grounding verified across foundational literature</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-palette-lilac hover:bg-palette-heather text-palette-deep font-semibold"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
}
