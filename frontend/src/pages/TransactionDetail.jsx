import React, { useEffect, useState } from 'react';
import { 
  ArrowLeft, 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  User, 
  Sparkles, 
  Play, 
  AlertTriangle,
  RotateCcw
} from 'lucide-react';
import { getTransactionDetail, analyzeTransaction, executeAction, approveAction, rejectAction } from '../api/client';
import { StatusBadge, StrategyBadge, PriorityBadge } from '../components/common/Badge';

const formatTimestamp = (ts) => {
  if (!ts) return 'N/A';
  const iso = String(ts).endsWith('Z') ? ts : `${ts}Z`;
  const d = new Date(iso);
  return isNaN(d.getTime()) 
    ? new Date(ts).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true }) 
    : d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true });
};

const formatDateTime = (ts) => {
  if (!ts) return 'N/A';
  const iso = String(ts).endsWith('Z') ? ts : `${ts}Z`;
  const d = new Date(iso);
  return isNaN(d.getTime()) 
    ? new Date(ts).toLocaleString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true }) 
    : d.toLocaleString('en-IN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true });
};

export const TransactionDetail = ({ txId, onBack, onSelectDemo }) => {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [actionSuccessMessage, setActionSuccessMessage] = useState(null);

  const fetchDetail = async (id = txId) => {
    try {
      setLoading(true);
      const data = await getTransactionDetail(id);
      setDetail(data);
    } catch (err) {
      console.error('Failed to load transaction detail', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (txId) {
      fetchDetail(txId);
    }
  }, [txId]);

  const handleReanalyze = async () => {
    try {
      setAnalyzing(true);
      await analyzeTransaction(detail.transaction_id);
      await fetchDetail(detail.transaction_id);
      setActionSuccessMessage('Transaction re-scored and context re-evaluated.');
      setTimeout(() => setActionSuccessMessage(null), 5000);
    } catch (err) {
      console.error('Failed to analyze', err);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleExecute = async (actionId) => {
    try {
      setExecuting(true);
      await executeAction(actionId);
      setActionSuccessMessage('Action executed successfully! Simulated recovery recorded.');
      await fetchDetail(detail.transaction_id);
      setTimeout(() => setActionSuccessMessage(null), 5000);
    } catch (err) {
      console.error('Execution error', err);
    } finally {
      setExecuting(false);
    }
  };

  const handleApprove = async (actionId) => {
    try {
      setExecuting(true);
      await approveAction(actionId, 'Approved via Transaction Detail');
      setActionSuccessMessage('Action approved by Merchant Ops!');
      await fetchDetail(detail.transaction_id);
      setTimeout(() => setActionSuccessMessage(null), 5000);
    } catch (err) {
      console.error('Approval error', err);
    } finally {
      setExecuting(false);
    }
  };

  const handleReject = async (actionId) => {
    try {
      setExecuting(true);
      await rejectAction(actionId, 'Declined by Merchant Ops');
      setActionSuccessMessage('Action rejected by Merchant Ops.');
      await fetchDetail(detail.transaction_id);
      setTimeout(() => setActionSuccessMessage(null), 5000);
    } catch (err) {
      console.error('Rejection error', err);
    } finally {
      setExecuting(false);
    }
  };

  if (loading && !detail) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-mono text-slate-500">Loading Transaction Details...</span>
        </div>
      </div>
    );
  }

  const decision = detail?.latest_decision;
  const customer = detail?.customer;
  const prob = decision?.recovery_probability ?? (detail?.recovery_probability ?? 0.5);
  const probPct = Math.round(prob * 100);
  const churnPct = Math.round((detail?.churn_probability ?? 0.15) * 100);
  const primaryAction = detail?.actions && detail.actions.length > 0
    ? [...detail.actions].sort((a, b) => b.action_id.localeCompare(a.action_id))[0]
    : null;

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Top Header & Context Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[#1B2333]">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-1.5 rounded-md bg-[#0F1624] border border-[#1B2436] hover:bg-[#151F30] text-slate-300 transition-colors active:scale-[0.98]"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-lg font-bold font-mono text-slate-100">{detail?.transaction_id}</h1>
              <StatusBadge status={detail?.status} />
              <PriorityBadge priority={detail?.recovery_priority} />
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Failed payment analysis & context-driven strategy execution
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Quick Demo Switcher */}
          <div className="flex items-center gap-1 bg-[#0D121D] border border-[#192233] p-1 rounded-md">
            <span className="text-[11px] font-mono text-slate-500 px-1.5">Demo:</span>
            {['TX-DEMO-001', 'TX-DEMO-002', 'TX-DEMO-003', 'TX-DEMO-004', 'TX-DEMO-005', 'TX-DEMO-006'].map((id) => (
              <button
                key={id}
                onClick={() => {
                  if (onSelectDemo) onSelectDemo(id);
                  fetchDetail(id);
                }}
                className={`px-2 py-0.5 text-[10px] font-mono rounded transition-colors ${
                  detail?.transaction_id === id 
                    ? 'bg-blue-600 text-white font-semibold' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#141C2B]'
                }`}
              >
                {id.replace('TX-DEMO-', 'D')}
              </button>
            ))}
          </div>

          <button
            onClick={handleReanalyze}
            disabled={analyzing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#0F1624] border border-[#1B2436] hover:bg-[#151F30] text-xs font-medium text-slate-300 disabled:opacity-50 transition-colors active:scale-[0.98]"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${analyzing ? 'animate-spin' : ''}`} />
            <span>{analyzing ? 'Re-Scoring...' : 'Re-Score'}</span>
          </button>
        </div>
      </div>

      {actionSuccessMessage && (
        <div className="p-3 rounded-md bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 text-xs flex items-center gap-2 font-medium">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>{actionSuccessMessage}</span>
        </div>
      )}

      {/* Main Grid: Left 4 cols (Context) + Right 8 cols (Agent Reasoning & Workflow) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        
        {/* Left Column: Transaction Details & Customer Profile (4 cols) */}
        <div className="lg:col-span-4 space-y-5">
          {/* Transaction Details Card */}
          <div className="p-5 rounded-lg bg-[#0D121D] border border-[#192233] space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-[12px] font-medium text-slate-400 tracking-wide">
                Transaction Details
              </span>
              <span className="text-[11px] font-mono text-slate-500">{detail?.currency}</span>
            </div>

            <div className="flex items-baseline justify-between py-2.5 border-y border-[#161F30]">
              <span className="text-xs text-slate-400">Failed Amount</span>
              <span className="text-2xl font-bold font-mono text-slate-100">
                ₹{(detail?.amount ?? 0).toLocaleString('en-IN')}
              </span>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">Gateway Decline Reason</span>
                <span className="text-slate-200">{String(detail?.failure_reason || '').replace(/_/g, ' ')}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">Payment Method</span>
                <span className="text-slate-200">{detail?.payment_method || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">Retry Count</span>
                <span className="text-slate-200">{detail?.retry_count ?? 0} / 3</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400 font-sans">Created</span>
                <span className="text-slate-400 text-[11px]">{formatDateTime(detail?.created_at)}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-3 border-t border-[#161F30] text-xs">
              <div className="p-2.5 rounded bg-[#0A0F18] border border-[#141C2B]">
                <div className="text-[10px] text-slate-500">Customer Lifetime Value</div>
                <div className="text-sm font-bold font-mono text-slate-200 mt-0.5">
                  ₹{(customer?.clv ?? 0).toLocaleString('en-IN')}
                </div>
              </div>
              <div className="p-2.5 rounded bg-[#0A0F18] border border-[#141C2B]">
                <div className="text-[10px] text-slate-500">Subscription Tenure</div>
                <div className="text-sm font-bold font-mono text-slate-200 mt-0.5">
                  {customer?.subscription_age_months ?? 0} Months
                </div>
              </div>
            </div>
          </div>

          {/* Customer Profile & Affinity */}
          <div className="p-5 rounded-lg bg-[#0D121D] border border-[#192233] space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <User className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-[12px] font-medium text-slate-300">Customer Profile</span>
              </div>
              <span className="px-1.5 py-0.5 text-[10px] font-mono rounded bg-[#131A29] text-slate-400 border border-[#1E283D]">
                {customer?.segment}
              </span>
            </div>

            <div className="space-y-1">
              <div className="text-sm font-semibold text-slate-200">{customer?.name}</div>
              <div className="text-xs text-slate-400 font-mono">{customer?.email}</div>
              <div className="text-xs text-slate-500 font-mono">{customer?.phone}</div>
            </div>

            <div className="grid grid-cols-2 gap-3 pt-3 border-t border-[#161F30] text-xs">
              <div className="p-2.5 rounded bg-[#0A0F18] border border-[#141C2B]">
                <div className="text-[10px] text-slate-500">Customer Lifetime Value</div>
                <div className="text-sm font-bold font-mono text-slate-200 mt-0.5">
                  ₹{customer?.clv?.toLocaleString('en-IN')}
                </div>
              </div>
              <div className="p-2.5 rounded bg-[#0A0F18] border border-[#141C2B]">
                <div className="text-[10px] text-slate-500">Subscription Tenure</div>
                <div className="text-sm font-bold font-mono text-slate-200 mt-0.5">
                  {customer?.subscription_age_months} Months
                </div>
              </div>
              <div className="p-2.5 rounded bg-[#0A0F18] border border-[#141C2B]">
                <div className="text-[10px] text-slate-500">Historical Success</div>
                <div className="text-sm font-bold font-mono text-emerald-400 mt-0.5">
                  {Math.round((detail?.prev_payment_success_rate || 0.85) * 100)}%
                </div>
              </div>
              <div className="p-2.5 rounded bg-[#0A0F18] border border-[#141C2B]">
                <div className="text-[10px] text-slate-500">Peak Success Hour</div>
                <div className="text-sm font-bold font-mono text-blue-400 mt-0.5">
                  {customer?.avg_payment_hour ? `${customer.avg_payment_hour % 12 || 12}:00 ${customer.avg_payment_hour >= 12 ? 'PM' : 'AM'}` : '6:00 PM'}
                </div>
              </div>
            </div>

            {customer?.opted_out && (
              <div className="p-2.5 rounded bg-rose-500/10 border border-rose-500/25 text-rose-300 text-[11px] flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 shrink-0 text-rose-400" />
                <span>Customer opted out of communications. DND policy active.</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Reasoning, Gauges, Policy Gate, Explainability, Audit (8 cols) */}
        <div className="lg:col-span-8 space-y-5">
          
          {/* Recovery Likelihood & Churn Risk Gauges */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 rounded-lg bg-[#0D121D] border border-[#192233] space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[12px] font-medium text-slate-300">
                  Predicted Recovery Likelihood
                </span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/20">
                  L2 Logistic
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-emerald-400">{probPct}%</span>
                <span className="text-xs text-slate-400">
                  {probPct >= 70 ? 'High Recovery Probability' : probPct >= 40 ? 'Moderate Opportunity' : 'Low Probability (Fee Risk)'}
                </span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-[#161F30] overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-500 ${
                    probPct >= 70 ? 'bg-emerald-500' : probPct >= 40 ? 'bg-blue-500' : 'bg-rose-500'
                  }`} 
                  style={{ width: `${probPct}%` }}
                />
              </div>
            </div>

            <div className="p-5 rounded-lg bg-[#0D121D] border border-[#192233] space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[12px] font-medium text-slate-300">
                  Customer Churn Risk
                </span>
                <span className="text-[10px] font-mono text-slate-400 bg-[#131A29] px-1.5 py-0.2 rounded border border-[#1E283D]">
                  Behavioral Score
                </span>
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold font-mono text-rose-400">{churnPct}%</span>
                <span className="text-xs text-slate-400">
                  {churnPct > 50 ? 'Critical Churn Hazard' : churnPct > 20 ? 'Moderate Risk' : 'Low Churn Likelihood'}
                </span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-[#161F30] overflow-hidden">
                <div 
                  className="h-full rounded-full bg-rose-500 transition-all duration-500" 
                  style={{ width: `${churnPct}%` }}
                />
              </div>
            </div>
          </div>

          {/* Agent Decision & Strategy Explanation */}
          <div className="p-5 rounded-lg bg-[#0F1626] border border-[#1E2E48] space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded bg-[#152033] border border-[#202E48] flex items-center justify-center text-blue-400">
                  <Sparkles className="w-3.5 h-3.5" />
                </div>
                <div>
                  <h2 className="text-sm font-semibold text-slate-100">
                    Agent Decision & Strategy Explanation
                  </h2>
                  <span className="text-[11px] text-slate-400">Decision Engine Evaluation</span>
                </div>
              </div>
              <StrategyBadge strategy={decision?.recommended_strategy} />
            </div>

            <div className="p-4 rounded-md bg-[#0A0F18] border border-[#162030]">
              <p className="text-[13px] text-slate-200 leading-relaxed font-normal">
                {decision?.reason_summary || 'Analyzing transaction context...'}
              </p>
            </div>

            {/* Policy Gate Status Banner & Action Machine */}
            {(() => {
              const isExecuted = primaryAction?.status === 'EXECUTED' || detail?.status === 'RECOVERED';
              const isRejected = !isExecuted && (primaryAction?.status === 'REJECTED' || decision?.policy_status === 'REJECTED');
              const isApproved = !isExecuted && !isRejected && (primaryAction?.status === 'APPROVED' || decision?.policy_status === 'APPROVED');
              const isPending = !isExecuted && !isRejected && !isApproved && (primaryAction?.status === 'PENDING_APPROVAL' || decision?.policy_status === 'REQUIRES_APPROVAL');
              const isBlocked = !isExecuted && !isRejected && !isApproved && (primaryAction?.status === 'BLOCKED' || decision?.policy_status === 'BLOCKED');

              const recoveredAmt = detail?.recovered_amount || detail?.amount || 0;

              return (
                <div className={`p-4 rounded-md border flex items-center justify-between ${
                  isExecuted ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-300' :
                  isApproved ? 'bg-emerald-500/10 border-emerald-500/25 text-emerald-300' :
                  isPending ? 'bg-amber-500/10 border-amber-500/25 text-amber-300' :
                  'bg-rose-500/10 border-rose-500/25 text-rose-300'
                }`}>
                  <div className="flex items-center gap-2.5">
                    {isExecuted || isApproved ? <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" /> :
                     isPending ? <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0" /> :
                     <XCircle className="w-4 h-4 text-rose-400 shrink-0" />}
                    <div>
                      <div className="text-xs font-semibold font-mono">
                        {isExecuted ? 'POLICY GATE: APPROVED & EXECUTED (Simulated Recovery)' :
                         isApproved ? 'POLICY GATE: APPROVED (Merchant Ops Sign-Off Recorded)' :
                         isPending ? `POLICY GATE: REQUIRES HUMAN APPROVAL (${decision?.policy_rule_triggered || 'RULE-03-HIGH-VALUE-GATE'})` :
                         isRejected ? 'POLICY GATE: REJECTED (Merchant Ops Sign-Off Declined)' :
                         `POLICY GATE: ${decision?.policy_status || 'BLOCKED'} (${decision?.policy_rule_triggered || 'RULE-00'})`}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        {isExecuted ? `Action ${decision?.recommended_strategy || 'INTELLIGENT_RETRY'} executed in simulation. Simulated recovery: ₹${(recoveredAmt ?? 0).toLocaleString('en-IN')} recorded.` :
                         isApproved ? 'Action approved by Merchant Ops. Ready for controlled execution.' :
                         isPending ? 'Amount > ₹10,000 threshold requires merchant ops sign-off before dispatch.' :
                         isRejected ? 'Recovery action declined by merchant operations. No retries dispatched.' :
                         isBlocked ? 'Compliance guardrail prevents automated execution.' :
                         'All automated guardrails and financial threshold checks passed.'}
                      </div>
                    </div>
                  </div>

                  {/* Action Buttons - Strict State Machine */}
                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    {isPending && primaryAction && (
                      <>
                        <button
                          onClick={() => handleApprove(primaryAction.action_id)}
                          disabled={executing}
                          className="px-3 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition-colors flex items-center gap-1.5 active:scale-[0.98] shadow-sm disabled:opacity-50"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Approve Action</span>
                        </button>
                        <button
                          onClick={() => handleRejectPrompt(primaryAction.action_id)}
                          disabled={executing}
                          className="px-3 py-1.5 rounded-md bg-[#161F2E] border border-[#222E42] hover:bg-rose-500/20 hover:border-rose-500/30 text-rose-300 font-medium text-xs transition-colors flex items-center gap-1.5 active:scale-[0.98] disabled:opacity-50"
                        >
                          <X className="w-3.5 h-3.5" />
                          <span>Reject</span>
                        </button>
                      </>
                    )}
                    {isApproved && primaryAction && (
                      <button
                        onClick={() => handleExecute(primaryAction.action_id)}
                        disabled={executing}
                        className="px-3.5 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs transition-colors flex items-center gap-1.5 active:scale-[0.98] shadow-sm disabled:opacity-50"
                      >
                        <Play className={`w-3.5 h-3.5 fill-current ${executing ? 'animate-pulse' : ''}`} />
                        <span>{executing ? 'Executing...' : 'Execute Action'}</span>
                      </button>
                    )}
                    {isExecuted && (
                      <div className="flex items-center gap-1.5 px-3 py-1 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono font-medium">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Execution Complete</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })()}
          </div>

          {/* Machine Learning Decision & Feature Importance Waterfall */}
          <div className="p-5 rounded-lg bg-[#0D121D] border border-[#192233] space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-slate-100">
                  ML Interpretability & Feature Waterfall Breakdown
                </h2>
                <p className="text-[12px] text-slate-400 mt-0.5">
                  Direct log-odds mathematical attribution from L2 Logistic Regression model
                </p>
              </div>
              <span className="text-[10px] font-mono text-slate-400">
                Log-Odds Engine
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-[#1A2336] text-slate-400 uppercase tracking-wider font-mono text-[11px]">
                  <tr>
                    <th className="pb-2.5 font-medium">Feature Dimension</th>
                    <th className="pb-2.5 font-medium">Value Context</th>
                    <th className="pb-2.5 text-right font-medium">Log-Odds Impact</th>
                    <th className="pb-2.5 text-right font-medium">Direction</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#151D2C] font-mono">
                  {Array.isArray(decision?.feature_breakdown) && decision.feature_breakdown.map((f) => (
                    <tr key={f.feature || Math.random()} className="hover:bg-[#121927] transition-colors duration-100">
                      <td className="py-2.5 font-sans font-medium text-slate-200">{f.label}</td>
                      <td className="py-2.5 font-sans text-slate-400 text-[11px]">{f.explanation}</td>
                      <td className={`py-2.5 text-right font-semibold ${
                        (f.weight ?? 0) > 0 ? 'text-emerald-400' : (f.weight ?? 0) < 0 ? 'text-rose-400' : 'text-slate-400'
                      }`}>
                        {(f.weight ?? 0) > 0 ? `+${Number(f.weight).toFixed(3)}` : Number(f.weight ?? 0).toFixed(3)}
                      </td>
                      <td className="py-2.5 text-right">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          f.impact === 'POSITIVE' ? 'bg-emerald-500/10 text-emerald-400' :
                          f.impact === 'NEGATIVE' ? 'bg-rose-500/10 text-rose-400' : 'bg-[#141C2B] text-slate-400'
                        }`}>
                          {f.impact}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Activity & Audit Trail Timeline */}
          <div className="p-5 rounded-lg bg-[#0D121D] border border-[#192233] space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <h3 className="text-xs font-semibold text-slate-100">
                  Audit Trail & Execution Log
                </h3>
              </div>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.2 rounded border border-emerald-500/20">
                POLICY CONTROLLED
              </span>
            </div>

            <div className="relative pl-4.5 border-l border-[#1E283D] space-y-3.5 ml-2 pt-1">
              {!Array.isArray(detail?.audit_logs) || detail.audit_logs.length === 0 ? (
                <div className="text-xs text-slate-500">No audit records logged yet.</div>
              ) : (
                detail.audit_logs.map((log) => (
                  <div key={log.log_id} className="relative group">
                    {/* Event bullet point */}
                    <div className="absolute -left-[23px] top-1.5 w-2.5 h-2.5 rounded-full bg-blue-500/80 ring-4 ring-[#0D121D]" />

                    <div className="p-3 rounded-md bg-[#0A0F18] border border-[#141C2B] space-y-1">
                      <div className="flex items-center justify-between text-[11px]">
                        <span className="px-1.5 py-0.2 rounded text-[10px] font-mono font-semibold bg-[#131A29] text-slate-300 border border-[#1D273B]">
                          {log.actor}
                        </span>
                        <span className="font-mono text-slate-400 text-[10px]">
                          {formatTimestamp(log?.timestamp)}
                        </span>
                      </div>
                      <div className="text-xs font-medium text-slate-200 leading-snug">
                        {log.message}
                      </div>
                      <div className="text-[10px] font-mono text-slate-500">
                        Event: {log.event_type}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
