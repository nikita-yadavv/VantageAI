import React from 'react';
import { Sparkles, RotateCcw } from 'lucide-react';

export default function Navbar({ onReset, currentStage }) {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-palette-heather/70 bg-palette-lightest/90 backdrop-blur-md">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-2.5 cursor-pointer" onClick={onReset}>
          <div className="w-8 h-8 rounded-lg bg-palette-deep flex items-center justify-center shadow-sm">
            <Sparkles className="w-4 h-4 text-palette-lightest" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-bold text-lg tracking-tight text-palette-deep font-display">
              Vantage<span className="text-palette-plum font-normal">AI</span>
            </span>
            <span className="text-[10px] uppercase tracking-wider text-palette-plum font-mono font-medium">
              Screening
            </span>
          </div>
        </div>

        {/* Actions */}
        <div>
          {currentStage !== 'setup' && (
            <button
              onClick={onReset}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-palette-lilac/60 hover:bg-palette-heather border border-palette-heather text-palette-deep transition-all"
            >
              <RotateCcw className="w-3.5 h-3.5 text-palette-plum" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
