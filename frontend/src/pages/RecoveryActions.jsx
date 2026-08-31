import React, { useEffect, useState } from 'react';
import { 
  CheckCircle2, 
  Play, 
  RefreshCw, 
  ChevronRight,
  ShieldCheck,
  Clock,
  Check,
  X
} from 'lucide-react';
import { getActions, approveAction, rejectAction, executeAction } from '../api/client';
import { StatusBadge, StrategyBadge } from '../components/common/Badge';

export const RecoveryActions = ({ onSelectTransaction }) => {
  const [allActions, setAllActions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [rejectingAction, setRejectingAction] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  const [feedback, setFeedback] = useState(null);

  const fetchActions = async () => {
    try {
      setLoading(true);
      const data = await getActions({ limit: 200 });
      setAllActions(data);
    } catch (err) {
      console.error('Failed to load actions', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchActions();
  }, []);

  const handleApprove = async (actionId) => {
    try {
      await approveAction(actionId, 'Approved by Merchant Ops from Actions Queue');
      setFeedback('Action approved successfully.');
      fetchActions();
      setTimeout(() => setFeedback(null), 4000);
    } catch (err) {
      console.error('Approval failed', err);
    }
  };

  const handleConfirmReject = async () => {
    if (!rejectingAction || !rejectReason.trim()) return;
    try {
      await rejectAction(rejectingAction.action_id, rejectReason);
      setFeedback('Action rejected.');
      setRejectingAction(null);
      setRejectReason('');
      fetchActions();
      setTimeout(() => setFeedback(null), 4000);
    } catch (err) {
      console.error('Reject failed', err);
    }
  };

  const handleExecute = async (actionId) => {
    try {
      await executeAction(actionId);
      setFeedback('Simulated recovery action executed successfully.');
      fetchActions();
      setTimeout(() => setFeedback(null), 4000);
    } catch (err) {
      console.error('Execution failed', err);
    }
  };

  const totalCount = allActions.length;
  const pendingCount = allActions.filter((a) => a.status === 'PENDING_APPROVAL').length;
  const approvedCount = allActions.filter((a) => a.status === 'APPROVED').length;
  const executedCount = allActions.filter((a) => a.status === 'EXECUTED').length;

  const actions = statusFilter === 'ALL'
    ? allActions
    : allActions.filter((a) => a.status === statusFilter);

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[#1B2333]">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl font-bold tracking-tight text-slate-100">
              Recovery Actions & Approvals
            </h1>
            <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-[#131A29] text-slate-400 border border-[#1E283D]">
              Controlled Autonomy
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Human-in-the-loop review queue for high-value transactions and policy-gated operations.
          </p>
        </div>

        <button
          onClick={fetchActions}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#0F1624] border border-[#1B2436] hover:bg-[#151F30] text-xs font-medium text-slate-300 transition-colors self-start sm:self-auto active:scale-[0.98]"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Queue</span>
        </button>
      </div>

      {feedback && (
        <div className="p-3 rounded-md bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-xs flex items-center gap-2 font-medium">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>{feedback}</span>
        </div>
      )}

      {/* Compact Operational Summary Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded-lg bg-[#0D121D] border border-[#192233] text-xs">
        <div className="flex items-center justify-between p-2 rounded bg-[#0A0F18] border border-[#141C2B]">
          <span className="text-slate-400 font-sans">Total Actions</span>
          <span className="font-mono font-bold text-slate-200">{totalCount}</span>
        </div>
        <div className="flex items-center justify-between p-2 rounded bg-[#0A0F18] border border-[#141C2B]">
          <span className="text-slate-400 font-sans">Pending Review</span>
          <span className={`font-mono font-bold ${pendingCount > 0 ? 'text-amber-400' : 'text-slate-400'}`}>
            {pendingCount}
          </span>
        </div>
        <div className="flex items-center justify-between p-2 rounded bg-[#0A0F18] border border-[#141C2B]">
          <span className="text-slate-400 font-sans">Approved</span>
          <span className="font-mono font-bold text-emerald-400">{approvedCount}</span>
        </div>
        <div className="flex items-center justify-between p-2 rounded bg-[#0A0F18] border border-[#141C2B]">
          <span className="text-slate-400 font-sans">Executed</span>
          <span className="font-mono font-bold text-blue-400">{executedCount}</span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1 border-b border-[#1B2333] pb-0.5 text-xs">
        {[
          { id: 'ALL', label: 'All Actions' },
          { id: 'PENDING_APPROVAL', label: 'Pending Review', count: pendingCount },
          { id: 'APPROVED', label: 'Approved' },
          { id: 'EXECUTED', label: 'Executed' },
          { id: 'BLOCKED', label: 'Blocked by Policy' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setStatusFilter(tab.id)}
            className={`px-3 py-2 font-medium border-b-2 transition-colors duration-150 flex items-center gap-1.5 ${
              statusFilter === tab.id
                ? 'border-blue-500 text-slate-100 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>{tab.label}</span>
            {tab.count !== undefined && tab.count > 0 && (
              <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-amber-500/15 text-amber-300 border border-amber-500/25 font-semibold">
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Actions Table */}
      <div className="rounded-lg bg-[#0D121D] border border-[#192233] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0A0E17] border-b border-[#1A2336] text-slate-400 uppercase tracking-wider font-mono text-[11px]">
              <tr>
                <th className="py-3 px-4 font-medium">Action ID</th>
                <th className="py-3 px-4 font-medium">Transaction ID</th>
                <th className="py-3 px-4 font-medium">Strategy & Type</th>
                <th className="py-3 px-4 font-medium">Channel</th>
                <th className="py-3 px-4 font-medium">Governance Status</th>
                <th className="py-3 px-4 font-medium">Approved By</th>
                <th className="py-3 px-4 font-medium text-right">Review / Execute</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#151D2C] font-mono">
              {loading ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500 font-mono text-xs">
                    Loading actions queue...
                  </td>
                </tr>
              ) : actions.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500 text-xs">
                    No actions in this queue.
                  </td>
                </tr>
              ) : (
                actions.map((act) => (
                  <tr key={act.action_id} className="hover:bg-[#121927] transition-colors duration-150">
                    <td className="py-3 px-4 font-medium text-slate-300">{act.action_id}</td>
                    <td className="py-3 px-4">
                      <button
                        onClick={() => onSelectTransaction(act.transaction_id)}
                        className="text-blue-400 hover:text-blue-300 font-semibold flex items-center gap-1 transition-colors"
                      >
                        <span>{act.transaction_id}</span>
                        <ChevronRight className="w-3 h-3" />
                      </button>
                    </td>
                    <td className="py-3 px-4 font-sans">
                      <StrategyBadge strategy={act.action_type} />
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-sans text-xs">{act.channel}</td>
                    <td className="py-3 px-4 font-sans">
                      <StatusBadge status={act.status} />
                    </td>
                    <td className="py-3 px-4 text-[11px] text-slate-400 font-sans">
                      {act.approved_by || 'Awaiting Review'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {act.status === 'PENDING_APPROVAL' ? (
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleApprove(act.action_id)}
                            className="px-2.5 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-sans font-medium transition-colors active:scale-[0.98]"
                          >
                            Approve
                          </button>
                          <button
                            onClick={() => setRejectingAction(act)}
                            className="px-2.5 py-1 rounded-md bg-[#182233] hover:bg-[#222E42] text-slate-300 text-xs font-sans transition-colors active:scale-[0.98]"
                          >
                            Reject
                          </button>
                        </div>
                      ) : act.status === 'APPROVED' ? (
                        <button
                          onClick={() => handleExecute(act.action_id)}
                          className="px-3 py-1 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-sans font-medium flex items-center gap-1 ml-auto transition-colors active:scale-[0.98]"
                        >
                          <Play className="w-3 h-3 fill-current" />
                          <span>Execute</span>
                        </button>
                      ) : act.status === 'EXECUTED' ? (
                        <span className="text-emerald-400 text-xs font-sans font-medium flex items-center justify-end gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Captured</span>
                        </span>
                      ) : (
                        <span className="text-slate-500 text-xs font-sans">Policy Blocked</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Reject Modal */}
      {rejectingAction && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 select-none">
          <div className="bg-[#0D121D] border border-[#1E283D] rounded-lg p-5 max-w-md w-full space-y-4 shadow-2xl">
            <div>
              <h2 className="text-sm font-semibold text-slate-100">Reject Recovery Action</h2>
              <p className="text-xs text-slate-400 mt-1">
                Provide a compliance or business rationale for rejecting action <span className="font-mono text-slate-200">{rejectingAction.action_id}</span> on transaction <span className="font-mono text-slate-200">{rejectingAction.transaction_id}</span>:
              </p>
            </div>
            <textarea
              rows={3}
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Account undergoing dispute review, halt automated recovery..."
              className="w-full p-2.5 rounded-md bg-[#0A0F18] border border-[#1B2538] text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-sans"
            />
            <div className="flex items-center justify-end gap-2 pt-1">
              <button
                onClick={() => setRejectingAction(null)}
                className="px-3 py-1.5 rounded-md bg-[#151F30] border border-[#202D42] text-xs text-slate-300 hover:bg-[#1C283F] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmReject}
                disabled={!rejectReason.trim()}
                className="px-3.5 py-1.5 rounded-md bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-xs font-medium text-white transition-colors"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
