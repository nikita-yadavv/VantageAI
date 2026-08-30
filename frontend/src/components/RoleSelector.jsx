import React from 'react';
import { Brain, Server, Database, Sparkles, Check } from 'lucide-react';

const ROLES = [
  { id: 'ai_ml_engineer', title: 'AI / Machine Learning Engineer', icon: Brain },
  { id: 'backend_system_design', title: 'Backend Engineer', icon: Server },
  { id: 'data_science_applied_ml', title: 'Data Scientist', icon: Database },
  { id: 'advanced_theoretical_ml', title: 'Theoretical ML Engineer', icon: Sparkles },
];

export default function RoleSelector({ selectedRole, onSelectRole, difficulty, onSelectDifficulty }) {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-xs font-bold uppercase tracking-wider text-palette-plum mb-2">
          1. Select Role
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
          {ROLES.map((role) => {
            const Icon = role.icon;
            const isSelected = selectedRole === role.title || selectedRole.toLowerCase().includes(role.id.split('_')[0]);

            return (
              <button
                key={role.id}
                type="button"
                onClick={() => onSelectRole(role.title)}
                className={`p-3 rounded-xl text-left border flex items-center justify-between transition-all ${
                  isSelected
                    ? 'bg-[#2F2433] text-white border-[#2F2433] shadow-sm'
                    : 'bg-white/80 text-[#2F2433] border-palette-heather hover:border-palette-mauve hover:bg-white'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon className={`w-4 h-4 ${isSelected ? 'text-[#D7C9DB]' : 'text-palette-plum'}`} />
                  <span className={`text-xs font-semibold ${isSelected ? 'text-white' : 'text-[#2F2433]'}`}>
                    {role.title}
                  </span>
                </div>
                {isSelected && <Check className="w-3.5 h-3.5 text-white" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Difficulty Level */}
      <div className="flex items-center justify-between pt-1">
        <label className="text-xs font-bold uppercase tracking-wider text-palette-plum">
          Level
        </label>
        <div className="flex gap-1.5">
          {['Junior', 'Intermediate', 'Senior'].map((lvl) => {
            const isSel = difficulty.toLowerCase() === lvl.toLowerCase();
            return (
              <button
                key={lvl}
                type="button"
                onClick={() => onSelectDifficulty(lvl.toLowerCase())}
                className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  isSel
                    ? 'bg-[#2F2433] text-white shadow-sm'
                    : 'bg-white/80 text-[#2F2433] border border-palette-heather hover:bg-white'
                }`}
              >
                <span className={isSel ? 'text-white font-bold' : 'text-[#2F2433]'}>{lvl}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
