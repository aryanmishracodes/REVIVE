import React, { useEffect, useState } from 'react';
import { 
  Search, 
  Filter, 
  RefreshCw, 
  ChevronRight
} from 'lucide-react';
import { getTransactions } from '../api/client';
import { StatusBadge, StrategyBadge } from '../components/common/Badge';

export const Transactions = ({ onSelectTransaction }) => {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [failureFilter, setFailureFilter] = useState('ALL');
  const [page, setPage] = useState(1);

  const fetchTxList = async () => {
    try {
      setLoading(true);
      const params = {
        page,
        page_size: 25,
        status: statusFilter !== 'ALL' ? statusFilter : undefined,
        failure_reason: failureFilter !== 'ALL' ? failureFilter : undefined,
        search: search || undefined,
      };
      const data = await getTransactions(params);
      setTransactions(data);
    } catch (err) {
      console.error('Failed to fetch transactions', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchTxList();
    }, 200);
    return () => clearTimeout(timer);
  }, [search, page, statusFilter, failureFilter]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchTxList();
  };

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[#1B2333]">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-slate-100">Transactions</h1>
          <p className="text-xs text-slate-400 mt-1">
            Monitoring failed payments, recovery outcomes, and agent recommendations.
          </p>
        </div>

        <button
          onClick={fetchTxList}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-[#0F1624] border border-[#1B2436] hover:bg-[#151F30] text-xs font-medium text-slate-300 transition-colors self-start sm:self-auto active:scale-[0.98]"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="p-3.5 rounded-lg bg-[#0D121D] border border-[#192233] flex flex-col md:flex-row gap-3 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
          <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Search by TX ID or Customer..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className="w-full pl-9 pr-4 py-1.5 rounded-md bg-[#0A0F18] border border-[#162030] text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 font-mono"
          />
        </form>

        <div className="flex flex-wrap items-center gap-2.5 w-full md:w-auto">
          {/* Status Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <span>Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
              className="bg-[#0A0F18] border border-[#162030] rounded px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-sans"
            >
              <option value="ALL">All Statuses</option>
              <option value="FAILED">Failed</option>
              <option value="PENDING_RECOVERY">In Recovery</option>
              <option value="RECOVERED">Recovered</option>
              <option value="ESCALATED">Escalated</option>
              <option value="STOPPED">Stopped</option>
            </select>
          </div>

          {/* Failure Reason Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-400">
            <span>Failure:</span>
            <select
              value={failureFilter}
              onChange={(e) => { setFailureFilter(e.target.value); setPage(1); }}
              className="bg-[#0A0F18] border border-[#162030] rounded px-2 py-1 text-xs text-slate-200 focus:outline-none focus:border-blue-500 font-sans"
            >
              <option value="ALL">All Failures</option>
              <option value="INSUFFICIENT_FUNDS">Insufficient Funds</option>
              <option value="NETWORK_TIMEOUT">Network Timeout</option>
              <option value="AUTHENTICATION_FAILURE">Auth / OTP Drop</option>
              <option value="CARD_EXPIRED">Card Expired</option>
              <option value="BANK_DECLINED">Bank Declined</option>
              <option value="LIMIT_EXCEEDED">Limit Exceeded</option>
              <option value="PAYMENT_ABANDONED">Payment Abandoned</option>
            </select>
          </div>
        </div>
      </div>

      {/* Transactions Data Table */}
      <div className="rounded-lg bg-[#0D121D] border border-[#192233] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0A0E17] border-b border-[#1A2336] text-slate-400 uppercase tracking-wider font-mono text-[11px]">
              <tr>
                <th className="py-3 px-4 font-medium">Transaction ID</th>
                <th className="py-3 px-4 font-medium">Customer</th>
                <th className="py-3 px-4 font-medium text-right">Amount</th>
                <th className="py-3 px-4 font-medium">Failure Reason</th>
                <th className="py-3 px-4 font-medium text-center">Retries</th>
                <th className="py-3 px-4 font-medium">Recovery Prob</th>
                <th className="py-3 px-4 font-medium">Strategy</th>
                <th className="py-3 px-4 font-medium">Status</th>
                <th className="py-3 px-4 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#151D2C]">
              {loading ? (
                <tr>
                  <td colSpan="9" className="py-12 text-center text-slate-500 font-mono text-xs">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-3.5 h-3.5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                      <span>Loading transactions...</span>
                    </div>
                  </td>
                </tr>
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan="9" className="py-12 text-center text-slate-400 font-medium text-xs">
                    No transactions found
                  </td>
                </tr>
              ) : (
                transactions.map((tx) => {
                  const prob = tx.recovery_probability ?? 0.5;
                  const probPct = Math.round(prob * 100);
                  return (
                    <tr
                      key={tx.transaction_id}
                      onClick={() => onSelectTransaction(tx.transaction_id)}
                      className="hover:bg-[#121927] cursor-pointer transition-colors duration-150 group"
                    >
                      <td className="py-2.5 px-4 font-mono font-medium text-slate-300 group-hover:text-blue-400 transition-colors">
                        {tx.transaction_id}
                      </td>
                      <td className="py-2.5 px-4">
                        <div className="font-medium text-slate-200">{tx.customer_name}</div>
                        <div className="text-[11px] text-slate-400 font-mono">
                          {tx.customer_segment} • {tx.payment_method}
                        </div>
                      </td>
                      <td className="py-2.5 px-4 text-right font-mono font-semibold text-slate-100">
                        ₹{tx.amount.toLocaleString('en-IN')}
                      </td>
                      <td className="py-2.5 px-4">
                        <span className="text-slate-300 font-sans">
                          {tx.failure_reason.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 text-center font-mono text-slate-400">
                        {tx.retry_count} / 3
                      </td>
                      <td className="py-2.5 px-4">
                        <div className="flex items-center gap-2 font-mono">
                          <div className="w-12 h-1.5 rounded-full bg-[#161F30] overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-300 ${
                                probPct >= 70 ? 'bg-emerald-500' :
                                probPct >= 40 ? 'bg-blue-500' : 'bg-rose-500'
                              }`}
                              style={{ width: `${probPct}%` }}
                            />
                          </div>
                          <span className={`text-[11px] font-bold ${
                            probPct >= 70 ? 'text-emerald-400' :
                            probPct >= 40 ? 'text-blue-400' : 'text-rose-400'
                          }`}>
                            {probPct}%
                          </span>
                        </div>
                      </td>
                      <td className="py-2.5 px-4 font-sans">
                        <StrategyBadge strategy={tx.recommended_strategy} />
                      </td>
                      <td className="py-2.5 px-4 font-sans">
                        <StatusBadge status={tx.status} />
                      </td>
                      <td className="py-2.5 px-4 text-right">
                        <button className="text-xs text-slate-400 group-hover:text-blue-400 font-medium flex items-center justify-end gap-1 ml-auto transition-colors">
                          <span>Inspect</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-3.5 border-t border-[#161F30] flex items-center justify-between text-xs text-slate-400">
          <span>Showing page {page}</span>
          <div className="flex items-center gap-2">
            <button
              disabled={page === 1}
              onClick={(e) => { e.stopPropagation(); setPage((p) => Math.max(1, p - 1)); }}
              className="px-3 py-1 rounded bg-[#0A0F18] border border-[#162030] disabled:opacity-40 hover:bg-[#141C2B] text-slate-300 transition-colors"
            >
              Previous
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); setPage((p) => p + 1); }}
              className="px-3 py-1 rounded bg-[#0A0F18] border border-[#162030] hover:bg-[#141C2B] text-slate-300 transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
