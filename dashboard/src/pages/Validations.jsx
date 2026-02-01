import { useState, useEffect } from 'react';
import { validationsAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import EmptyState from '../components/EmptyState';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { CheckCircle2 } from 'lucide-react';

const Validations = () => {
  const [validations, setValidations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedValidation, setSelectedValidation] = useState(null);

  useEffect(() => {
    loadValidations();
  }, []);

  const loadValidations = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await validationsAPI.list(null, 100, 0);
      setValidations(data);
      if (data.length > 0 && !selectedValidation) {
        setSelectedValidation(data[0]);
      }
    } catch (err) {
      setError(err.message || 'Failed to load validations');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={loadValidations} />;
  }

  if (validations.length === 0) {
    return (
      <div className="p-6">
        <EmptyState
          title="No Validations Yet"
          description="Run a walk-forward validation to evaluate strategy stability"
          icon={CheckCircle2}
        />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">Validations</h1>
        <p className="text-gray-400">Walk-forward validation results and stability analysis</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Validation List */}
        <div className="lg:col-span-1 bg-gray-800 rounded-lg border border-gray-700 p-4 max-h-[calc(100vh-200px)] overflow-y-auto">
          <h2 className="text-lg font-semibold text-white mb-4">All Validations</h2>
          <div className="space-y-2">
            {validations.map((validation) => (
              <button
                key={validation.id}
                onClick={() => setSelectedValidation(validation)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  selectedValidation?.id === validation.id
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-900/50 text-gray-300 hover:bg-gray-900'
                }`}
              >
                <p className="font-medium text-sm">Strategy {validation.strategy_id}</p>
                <p className="text-xs opacity-75 mt-1">
                  {validation.created_at ? new Date(validation.created_at).toLocaleDateString() : 'Unknown date'}
                </p>
                <div className="flex items-center justify-between mt-2">
                  <span className={`text-xs px-2 py-1 rounded ${
                    validation.status === 'completed' ? 'bg-green-900/30 text-green-400' :
                    validation.status === 'running' ? 'bg-yellow-900/30 text-yellow-400' :
                    validation.status === 'failed' ? 'bg-red-900/30 text-red-400' :
                    'bg-gray-700 text-gray-400'
                  }`}>
                    {validation.status}
                  </span>
                  {validation.results?.stability_score && (
                    <span className="text-xs">Stability: {validation.results.stability_score.toFixed(2)}</span>
                  )}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Validation Details */}
        <div className="lg:col-span-2 space-y-6">
          {selectedValidation && (
            <>
              <ValidationMetrics validation={selectedValidation} />
              {selectedValidation.results?.window_scores && (
                <ValidationChart data={selectedValidation.results.window_scores} />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const ValidationMetrics = ({ validation }) => {
  const results = validation.results || {};

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
      <h2 className="text-xl font-semibold text-white mb-4">Validation Metrics</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Stability Score"
          value={results.stability_score?.toFixed(2) || 'N/A'}
          positive={results.stability_score > 0.7}
        />
        <MetricCard
          label="Degradation"
          value={results.degradation?.toFixed(2) || 'N/A'}
          positive={results.degradation < 0.2}
        />
        <MetricCard
          label="Windows"
          value={results.window_scores ? results.window_scores.length : 'N/A'}
        />
        <MetricCard
          label="Status"
          value={validation.status || 'N/A'}
        />
      </div>
      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Strategy ID</span>
            <p className="text-white font-medium">{validation.strategy_id}</p>
          </div>
          <div>
            <span className="text-gray-400">Created</span>
            <p className="text-white font-medium">
              {validation.created_at ? new Date(validation.created_at).toLocaleString() : 'Unknown'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

const MetricCard = ({ label, value, positive }) => (
  <div className="p-4 bg-gray-900/50 rounded-lg">
    <p className="text-xs text-gray-400 mb-1">{label}</p>
    <p className={`text-xl font-bold ${positive ? 'text-green-400' : positive === false ? 'text-red-400' : 'text-white'}`}>
      {value}
    </p>
  </div>
);

const ValidationChart = ({ data }) => {
  const chartData = data.map((score, index) => ({
    window: index + 1,
    score,
  }));

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
      <h2 className="text-xl font-semibold text-white mb-4">Window Stability Scores</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="window" stroke="#9CA3AF" />
          <YAxis stroke="#9CA3AF" domain={[0, 1]} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
            labelStyle={{ color: '#9CA3AF' }}
          />
          <Legend />
          <Line type="monotone" dataKey="score" stroke="#22C55E" strokeWidth={2} dot />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default Validations;
