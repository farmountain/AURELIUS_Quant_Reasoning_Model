import { useEffect, useState } from 'react';
import { useWebSocket } from '../context/WebSocketContext';

export const useRealtimeStrategies = () => {
  const [strategies, setStrategies] = useState([]);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('strategy_update', (data) => {
      setStrategies(prev => {
        const index = prev.findIndex(s => s.id === data.id);
        if (index >= 0) {
          return [...prev.slice(0, index), data, ...prev.slice(index + 1)];
        }
        return [...prev, data];
      });
    });

    return unsubscribe;
  }, [subscribe]);

  return strategies;
};

export const useRealtimeBacktests = () => {
  const [backtests, setBacktests] = useState([]);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('backtest_update', (data) => {
      setBacktests(prev => {
        const index = prev.findIndex(b => b.id === data.id);
        if (index >= 0) {
          return [...prev.slice(0, index), data, ...prev.slice(index + 1)];
        }
        return [...prev, data];
      });
    });

    return unsubscribe;
  }, [subscribe]);

  return backtests;
};

export const useRealtimeDashboard = () => {
  const [stats, setStats] = useState({
    active_strategies: 0,
    running_backtests: 0,
    gates_passed: 0,
    gates_failed: 0,
    recent_backtests: [],
  });
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe('dashboard_update', (data) => {
      setStats(prev => ({ ...prev, ...data }));
    });

    return unsubscribe;
  }, [subscribe]);

  return stats;
};

export const useRealtimeBacktestProgress = (backtestId) => {
  const [progress, setProgress] = useState(null);
  const { subscribe } = useWebSocket();

  useEffect(() => {
    const unsubscribe = subscribe(`backtest_progress_${backtestId}`, (data) => {
      setProgress(data);
    });

    return unsubscribe;
  }, [backtestId, subscribe]);

  return progress;
};
