import React, { useEffect, useState } from 'react';
import { 
  TrendingUp, 
  AlertOctagon, 
  CheckCircle2, 
  DollarSign, 
  RefreshCw, 
  ShieldCheck, 
  ChevronRight,
  ExternalLink
} from 'lucide-react';
import { getDashboardMetrics, getFailureDistribution } from '../api/client';
import { MetricCard } from '../components/common/MetricCard';

export const CommandCenter = ({ onSelectTransaction, onNavigateTab }) => {
  const [metrics, setMetrics] = useState(null);
  const [distribution, setDistribution] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [m, d] = await Promise.all([getDashboardMetrics(), getFailureDistribution()]);
      setMetrics(m);
      setDistribution(d);
    } catch (err) {
      console.error('Failed to load dashboard metrics', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading && !metrics) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-3">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-mono text-slate-500">Loading Telemetry...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[#1B2333]">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100">
            Revenue Recovery Command Center
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time decisioning and policy execution across failed payment transactions.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchData}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#0F1624] border border-[#1B2436] hover:bg-[#151F30] text-xs font-medium text-slate-300 transition-colors active:scale-[0.98]"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => onNavigateTab('simulator')}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-xs font-medium text-white transition-colors active:scale-[0.98]"
          >
            <span>Open Simulator</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Top 4 KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
        <MetricCard
          title="Total Failed Value"
          value={`₹${(metrics?.total_failed_value || 0).toLocaleString('en-IN')}`}
          subtitle={`${metrics?.total_failed_count || 0} failed transactions`}
          icon={AlertOctagon}
          trend="-2.4%"
          trendLabel="past 30d"
        />
        <MetricCard
          title="Recoverable Opportunity"
          value={`₹${(metrics?.recoverable_value || 0).toLocaleString('en-IN')}`}
          subtitle="ML-Predicted Total Opportunity"
          icon={TrendingUp}
          highlight={true}
        />
        <MetricCard
          title="Total Recovered"
          value={`₹${(metrics?.recovered_value || 0).toLocaleString('en-IN')}`}
          subtitle={`${(metrics?.overall_recovery_rate ?? 49.0).toFixed(1)}% transaction recovery rate`}
          icon={CheckCircle2}
          trend={metrics?.revive_uplift_percent ? `+${metrics.revive_uplift_percent}%` : undefined}
          trendLabel="vs baseline"
        />
        <MetricCard
          title="REVIVE Uplift"
          value={`+${metrics?.revive_uplift_percent || 0}%`}
          subtitle={`${metrics?.pending_approvals_count || 0} pending ops reviews`}
          icon={DollarSign}
          badge="SIMULATED BENCHMARK"
        />
      </div>

      {/* Main Content Grid: Failure Distribution Table + Pitch Scenario Launcher */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left 2 Cols: Financial Failure Breakdown Table */}
        <div className="lg:col-span-2 p-5 rounded-lg bg-[#0D121D] border border-[#192233] space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-slate-100">
                Payment Failure Distribution & Recovery Rates
              </h2>
              <p className="text-[12px] text-slate-400 mt-0.5">
                Empirical recovery performance categorized by failure reason
              </p>
            </div>
            <button
              onClick={() => onNavigateTab('transactions')}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1 font-medium transition-colors"
            >
              <span>View All</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="border-b border-[#1A2336] text-slate-400 uppercase tracking-wider font-mono text-[11px]">
                <tr>
                  <th className="pb-2.5 font-medium">Failure Category</th>
                  <th className="pb-2.5 font-medium text-right">Volume</th>
                  <th className="pb-2.5 font-medium text-right">Failed Value</th>
                  <th className="pb-2.5 font-medium text-right">Recovered</th>
                  <th className="pb-2.5 font-medium text-right">Capture Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#151D2C]">
                {distribution.map((d) => (
                  <tr key={d.failure_reason} className="hover:bg-[#121927] transition-colors duration-100">
                    <td className="py-2.5 font-sans font-medium text-slate-200">
                      {d.failure_reason.replace(/_/g, ' ')}
                    </td>
                    <td className="py-2.5 text-right font-mono text-slate-400">{d.count}</td>
                    <td className="py-2.5 text-right font-mono text-slate-300">₹{d.failed_value.toLocaleString('en-IN')}</td>
                    <td className="py-2.5 text-right font-mono text-slate-200 font-medium">₹{d.recovered_value.toLocaleString('en-IN')}</td>
                    <td className="py-2.5 text-right font-mono">
                      <span className={`font-semibold ${
                        d.recovery_rate >= 50 ? 'text-emerald-400' :
                        d.recovery_rate >= 35 ? 'text-slate-200' : 'text-slate-400'
                      }`}>
                        {d.recovery_rate}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right 1 Col: Live Pitch Scenarios Launcher */}
        <div className="p-5 rounded-lg bg-[#0D121D] border border-[#192233] space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <h2 className="text-sm font-semibold text-slate-100">Live Pitch Scenarios</h2>
              <span className="text-[10px] font-mono text-slate-400 px-1.5 py-0.5 rounded bg-[#131A29] border border-[#1D273B]">
                6 Fixtures
              </span>
            </div>
            <p className="text-[12px] text-slate-400 mb-3.5">
              Select a canonical fixture to inspect the end-to-end decision trail:
            </p>

            <div className="space-y-1.5">
              <button
                onClick={() => onSelectTransaction('TX-DEMO-001')}
                className="w-full text-left p-2.5 rounded-md bg-[#0B101A] border border-[#17202F] hover:border-[#222E42] hover:bg-[#101726] transition-colors duration-150 flex items-center justify-between group cursor-pointer active:scale-[0.99]"
              >
                <div>
                  <div className="text-xs font-medium text-slate-200 group-hover:text-blue-400 transition-colors">
                    TX-DEMO-001: High-Value (₹18.5k)
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Requires Human Approval gate</div>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-blue-400 transition-colors shrink-0" />
              </button>

              <button
                onClick={() => onSelectTransaction('TX-DEMO-002')}
                className="w-full text-left p-2.5 rounded-md bg-[#0B101A] border border-[#17202F] hover:border-[#222E42] hover:bg-[#101726] transition-colors duration-150 flex items-center justify-between group cursor-pointer active:scale-[0.99]"
              >
                <div>
                  <div className="text-xs font-medium text-slate-200 group-hover:text-blue-400 transition-colors">
                    TX-DEMO-002: Network Timeout
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Intelligent Retry at optimal hour</div>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-blue-400 transition-colors shrink-0" />
              </button>

              <button
                onClick={() => onSelectTransaction('TX-DEMO-003')}
                className="w-full text-left p-2.5 rounded-md bg-[#0B101A] border border-[#17202F] hover:border-[#222E42] hover:bg-[#101726] transition-colors duration-150 flex items-center justify-between group cursor-pointer active:scale-[0.99]"
              >
                <div>
                  <div className="text-xs font-medium text-slate-200 group-hover:text-blue-400 transition-colors">
                    TX-DEMO-003: Card Expired
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">0% retry; routes to card update link</div>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-blue-400 transition-colors shrink-0" />
              </button>

              <button
                onClick={() => onSelectTransaction('TX-DEMO-004')}
                className="w-full text-left p-2.5 rounded-md bg-[#0B101A] border border-[#17202F] hover:border-[#222E42] hover:bg-[#101726] transition-colors duration-150 flex items-center justify-between group cursor-pointer active:scale-[0.99]"
              >
                <div>
                  <div className="text-xs font-medium text-slate-200 group-hover:text-blue-400 transition-colors">
                    TX-DEMO-004: Low Probability Drop
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Stops retries to prevent interchange fee waste</div>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-blue-400 transition-colors shrink-0" />
              </button>

              <button
                onClick={() => onSelectTransaction('TX-DEMO-005')}
                className="w-full text-left p-2.5 rounded-md bg-[#0B101A] border border-[#17202F] hover:border-[#222E42] hover:bg-[#101726] transition-colors duration-150 flex items-center justify-between group cursor-pointer active:scale-[0.99]"
              >
                <div>
                  <div className="text-xs font-medium text-slate-200 group-hover:text-blue-400 transition-colors">
                    TX-DEMO-005: Opted-Out Customer
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">DND active; silent retry permitted</div>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-blue-400 transition-colors shrink-0" />
              </button>

              <button
                onClick={() => onSelectTransaction('TX-DEMO-006')}
                className="w-full text-left p-2.5 rounded-md bg-[#0B101A] border border-[#17202F] hover:border-[#222E42] hover:bg-[#101726] transition-colors duration-150 flex items-center justify-between group cursor-pointer active:scale-[0.99]"
              >
                <div>
                  <div className="text-xs font-medium text-slate-200 group-hover:text-blue-400 transition-colors">
                    TX-DEMO-006: Already Recovered
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">Verified revenue recovery audit trail (₹6,500)</div>
                </div>
                <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-blue-400 transition-colors shrink-0" />
              </button>
            </div>
          </div>

          <div className="pt-3 border-t border-[#182130]">
            <div className="flex items-center gap-2 text-[11px] text-slate-400">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
              <span>All decisions audited with policy guardrails and complete trails.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
