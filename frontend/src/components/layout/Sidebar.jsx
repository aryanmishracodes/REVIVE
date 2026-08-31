import React from 'react';
import { 
  LayoutDashboard, 
  Receipt, 
  FileText, 
  ShieldAlert, 
  FlaskConical,
  Cpu
} from 'lucide-react';

export const Sidebar = ({ currentTab, setTab, pendingCount = 0 }) => {
  const navItems = [
    { id: 'command-center', label: 'Command Center', icon: LayoutDashboard },
    { id: 'transactions', label: 'Transactions', icon: Receipt },
    { id: 'transaction-detail', label: 'Transaction Detail', icon: FileText, badge: 'Demo' },
    { id: 'actions', label: 'Recovery Actions', icon: ShieldAlert, count: pendingCount },
    { id: 'simulator', label: 'Strategy Simulator', icon: FlaskConical },
  ];

  return (
    <aside className="w-60 border-r border-[#1B2333] bg-[#0A0E17] flex flex-col justify-between shrink-0 min-h-[calc(100vh-4rem)] select-none">
      <div className="p-3.5 space-y-6">
        <div>
          <p className="px-2.5 text-[10px] font-semibold text-slate-500 uppercase tracking-wider mb-2 font-mono">
            Navigation
          </p>
          <nav className="space-y-0.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setTab(item.id)}
                  className={`relative w-full flex items-center justify-between px-2.5 py-2 rounded-md text-[13px] font-medium transition-colors duration-150 focus:outline-none focus-visible:ring-1 focus-visible:ring-blue-500/40 ${
                    isActive
                      ? 'bg-[#141C2B] text-slate-100 font-semibold'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-[#111824]/60'
                  }`}
                >
                  {/* Left accent indicator for active state */}
                  {isActive && (
                    <span 
                      aria-hidden="true"
                      className="absolute left-0 top-1.5 bottom-1.5 w-[2.5px] rounded-r bg-blue-500" 
                    />
                  )}

                  <div className="flex items-center gap-2.5">
                    <Icon 
                      className={`w-4 h-4 shrink-0 transition-colors duration-150 ${
                        isActive ? 'text-blue-400' : 'text-slate-400'
                      }`} 
                    />
                    <span className="truncate">{item.label}</span>
                  </div>

                  {item.count > 0 && (
                    <span className="px-1.5 py-0.2 text-[11px] font-mono font-semibold rounded bg-amber-500/15 text-amber-300 border border-amber-500/25">
                      {item.count}
                    </span>
                  )}
                  {item.badge && !item.count && (
                    <span className="px-1.5 py-0.2 text-[10px] font-mono text-slate-400 rounded bg-[#161F30] border border-slate-700/40">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Quiet System Infrastructure Panel */}
        <div className="p-3 rounded-lg bg-[#0D121D] border border-[#192233] space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider font-semibold">
              Model Engine
            </span>
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/20">
              L2 Logistic
            </span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
            Calibrated log-odds weights with deterministic policy guardrails.
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="p-3.5 border-t border-[#1B2333] flex items-center justify-between text-[11px] font-mono text-slate-500">
        <span>REVIVE · v1.0</span>
      </div>
    </aside>
  );
};
