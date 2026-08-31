import React from 'react';
import { ShieldCheck, Award } from 'lucide-react';

export const Navbar = ({ activeScreen }) => {
  return (
    <header className="h-14 border-b border-[#1B2333] bg-[#0A0E17] px-5 flex items-center justify-between sticky top-0 z-30 select-none">
      {/* Brand Anchor */}
      <div className="flex items-center gap-3">
        <div className="w-7 h-7 rounded-md bg-blue-600 flex items-center justify-center font-bold text-white text-xs font-mono shrink-0">
          R
        </div>
        <div className="flex items-baseline gap-2">
          <span className="font-bold text-slate-100 tracking-tight text-sm">REVIVE</span>
          <span className="text-xs text-slate-400 font-normal">
            Revenue Recovery
          </span>
        </div>
      </div>

      {/* Right Metadata */}
      <div className="flex items-center gap-2.5">
        <div className="flex items-center gap-1.5 text-xs text-slate-300 bg-[#0F1624] border border-[#1B2436] px-2.5 py-1 rounded-md transition-colors duration-150">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
          <span>Guardrails Active</span>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 bg-[#0F1624] border border-[#1B2436] px-2.5 py-1 rounded-md font-mono transition-colors duration-150">
          <Award className="w-3.5 h-3.5 text-blue-400 shrink-0" />
          <span>Razorpay AI Builder &apos;26</span>
        </div>
      </div>
    </header>
  );
};
