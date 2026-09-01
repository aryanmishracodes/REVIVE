import React, { useState, useEffect, Component } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { CommandCenter } from './pages/CommandCenter';
import { Transactions } from './pages/Transactions';
import { TransactionDetail } from './pages/TransactionDetail';
import { RecoveryActions } from './pages/RecoveryActions';
import { StrategySimulator } from './pages/StrategySimulator';
import { getActions } from './api/client';
import { AlertTriangle, RefreshCw } from 'lucide-react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('ErrorBoundary caught error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-8 min-h-[60vh] flex flex-col items-center justify-center text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Telemetry Rendering Error</h2>
            <p className="text-xs text-slate-400 max-w-md mt-1 font-sans">
              An unexpected error occurred while rendering the interface.
            </p>
          </div>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reload Application</span>
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export function App() {
  const [currentTab, setCurrentTab] = useState('command-center');
  const [selectedTxId, setSelectedTxId] = useState('TX-DEMO-001');
  const [pendingCount, setPendingCount] = useState(0);

  // Periodic check for pending actions to update the sidebar badge
  const updatePendingCount = async () => {
    try {
      const actions = await getActions({ status: 'PENDING_APPROVAL' });
      setPendingCount(Array.isArray(actions) ? actions.length : 0);
    } catch (err) {
      setPendingCount(0);
    }
  };

  useEffect(() => {
    updatePendingCount();
    const interval = setInterval(updatePendingCount, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectTransaction = (txId) => {
    setSelectedTxId(txId);
    setCurrentTab('transaction-detail');
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-fintech-bg text-slate-100 flex flex-col font-sans">
        <Navbar activeScreen={currentTab} />
        
        <div className="flex-1 flex overflow-hidden">
          <Sidebar 
            currentTab={currentTab} 
            setTab={setCurrentTab} 
            pendingCount={pendingCount} 
          />

          <main className="flex-1 overflow-y-auto bg-[#080C14]">
            {currentTab === 'command-center' && (
              <CommandCenter 
                onSelectTransaction={handleSelectTransaction} 
                onNavigateTab={setCurrentTab} 
              />
            )}

            {currentTab === 'transactions' && (
              <Transactions 
                onSelectTransaction={handleSelectTransaction} 
              />
            )}

            {currentTab === 'transaction-detail' && (
              <TransactionDetail 
                txId={selectedTxId} 
                onBack={() => setCurrentTab('transactions')}
                onSelectDemo={setSelectedTxId}
              />
            )}

            {currentTab === 'actions' && (
              <RecoveryActions 
                onSelectTransaction={handleSelectTransaction} 
              />
            )}

            {currentTab === 'simulator' && (
              <StrategySimulator 
                onSelectTransaction={handleSelectTransaction} 
              />
            )}
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default App;
