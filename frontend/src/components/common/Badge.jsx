import React from 'react';

export const StatusBadge = ({ status }) => {
  const map = {
    RECOVERED: { label: 'Recovered', bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/25' },
    FAILED: { label: 'Failed', bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/25' },
    PENDING_RECOVERY: { label: 'In Recovery', bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/25' },
    ESCALATED: { label: 'Escalated', bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/25' },
    STOPPED: { label: 'Stopped', bg: 'bg-slate-800/40', text: 'text-slate-400', border: 'border-slate-700/50' },
    
    // Actions / Policy Governance
    PENDING_APPROVAL: { label: 'Pending Review', bg: 'bg-amber-500/15', text: 'text-amber-300', border: 'border-amber-500/30' },
    APPROVED: { label: 'Approved', bg: 'bg-emerald-500/15', text: 'text-emerald-300', border: 'border-emerald-500/30' },
    EXECUTED: { label: 'Executed', bg: 'bg-blue-500/15', text: 'text-blue-300', border: 'border-blue-500/30' },
    BLOCKED: { label: 'Policy Blocked', bg: 'bg-rose-500/15', text: 'text-rose-300', border: 'border-rose-500/30' },
    REJECTED: { label: 'Rejected', bg: 'bg-slate-800/60', text: 'text-slate-400', border: 'border-slate-700/60' },
    REQUIRES_APPROVAL: { label: 'Needs Approval', bg: 'bg-amber-500/15', text: 'text-amber-300', border: 'border-amber-500/30' },
  };

  const current = map[status] || { label: status, bg: 'bg-slate-800', text: 'text-slate-300', border: 'border-slate-700' };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium border ${current.bg} ${current.text} ${current.border}`}>
      {current.label}
    </span>
  );
};

export const StrategyBadge = ({ strategy }) => {
  const map = {
    INTELLIGENT_RETRY: { label: 'Intelligent Retry', color: 'text-blue-300 bg-[#101828] border-[#1E293B]' },
    CUSTOMER_NUDGE: { label: 'Customer Nudge', color: 'text-indigo-300 bg-[#12162A] border-[#202542]' },
    PAYMENT_UPDATE: { label: 'Payment Update', color: 'text-amber-300 bg-[#1A1814] border-[#2E281C]' },
    ESCALATION: { label: 'Ops Escalation', color: 'text-rose-300 bg-[#1C1318] border-[#331C26]' },
    STOP_RECOVERY: { label: 'Stop Recovery', color: 'text-slate-400 bg-[#111622] border-[#1E2433]' },
  };

  const current = map[strategy] || { label: strategy || 'None', color: 'text-slate-400 bg-[#111622] border-[#1E2433]' };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-sans font-medium border ${current.color}`}>
      {current.label}
    </span>
  );
};

export const PriorityBadge = ({ priority }) => {
  const map = {
    P0: { bg: 'bg-rose-500/15 text-rose-300 border-rose-500/30' },
    P1: { bg: 'bg-amber-500/15 text-amber-300 border-amber-500/30' },
    P2: { bg: 'bg-blue-500/15 text-blue-300 border-blue-500/30' },
    P3: { bg: 'bg-slate-800/40 text-slate-400 border-slate-700/50' },
  };

  const current = map[priority] || map.P2;
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold border ${current.bg}`}>
      {priority}
    </span>
  );
};
