import React from 'react';

export const MetricCard = ({ title, value, subtitle, icon: Icon, trend, trendLabel, highlight = false, badge }) => {
  return (
    <div className={`p-4 rounded-lg border transition-colors duration-150 flex flex-col justify-between ${
      highlight 
        ? 'bg-[#0F1626] border-[#1E2E48] hover:border-[#273B5C]' 
        : 'bg-[#0D121D] border-[#192233] hover:border-[#222E42]'
    }`}>
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-[12px] font-medium text-slate-400 tracking-wide">{title}</span>
          <div className="flex items-center gap-1.5">
            {badge && (
              <span className="px-1.5 py-0.5 text-[10px] font-mono rounded bg-[#151E2E] text-slate-400 border border-[#202C42]">
                {badge}
              </span>
            )}
            {Icon && (
              <div className="w-6 h-6 rounded bg-[#131A29] border border-[#1E283D] flex items-center justify-center text-slate-400">
                <Icon className="w-3.5 h-3.5" />
              </div>
            )}
          </div>
        </div>

        <div className="text-2xl font-bold tracking-tight text-slate-100 font-mono mb-1">
          {value}
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] mt-2 pt-2 border-t border-[#161F30]/60">
        {subtitle && <span className="text-slate-500 truncate mr-2">{subtitle}</span>}
        {trend !== undefined && trend !== null && (
          <span className={`font-mono shrink-0 ${String(trend).startsWith('+') ? 'text-emerald-400' : 'text-slate-400'}`}>
            {trend} {trendLabel && <span className="text-slate-500 font-sans">({trendLabel})</span>}
          </span>
        )}
      </div>
    </div>
  );
};
