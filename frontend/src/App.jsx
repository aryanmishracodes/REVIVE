import React, { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import { CommandCenter } from './pages/CommandCenter';
import { Transactions } from './pages/Transactions';
import { TransactionDetail } from './pages/TransactionDetail';
import { RecoveryActions } from './pages/RecoveryActions';
import { StrategySimulator } from './pages/StrategySimulator';
import { getActions } from './api/client';

export function App() {
  const [currentTab, setCurrentTab] = useState('command-center');
  const [selectedTxId, setSelectedTxId] = useState('TX-DEMO-001');
  const [pendingCount, setPendingCount] = useState(0);

  // Periodic check for pending actions to update the sidebar badge
  const updatePendingCount = async () => {
    try {
      const actions = await getActions({ status: 'PENDING_APPROVAL' });
      setPendingCount(actions.length);
    } catch (err) {
      // ignore
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
  );
}

export default App;
