/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
import React, { useState } from 'react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceLine
} from 'recharts';
import './ADNIModelPage.css';

interface TimelinePoint {
    visit: string;
    months_from_baseline: number;
    is_historical: boolean;
    is_predicted: boolean;
    scores: {
        mmse?: number;
        cdr_global?: number;
        cdr_sob?: number;
        adas_totscore?: number;
    };
    confidence: number;
}

interface ADNISummary {
    baseline_scores: Record<string, number>;
    predicted_final_scores: Record<string, number>;
    predicted_changes: {
        mmse: number;
        cdr_global: number;
        adas_totscore: number;
        [key: string]: number;
    };
    risk_level: string;
    prediction_horizon_months: number;
}

interface ADNIResults {
    result_id: string;
    timeline: TimelinePoint[];
    summary: ADNISummary;
    confidence_score: number;
    metadata: Record<string, any>;
}

interface Props {
    patientId: string;
}

// Type for the chart data point
interface ChartDataPoint {
    visit: string;
    months: number;
    mmse?: number;
    cdr_global?: number;
    cdr_sob?: number;
    adas?: number;
    isHistorical: boolean;
    isPredicted: boolean;
    confidence?: number;
}

const ADNIModelPage: React.FC<Props> = ({ patientId }) => {
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<ADNIResults | null>(null);
    const [error, setError] = useState<string | null>(null);

    const runModel = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/models/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    patient_id: patientId,
                    model_name: 'adni_progression'
                })
            });

            if (!response.ok) {
                throw new Error(`Model execution failed: ${response.statusText}`);
            }

            const data = await response.json();
            // Expecting data.results to match ADNIResults structure
            if (data && data.results) {
                setResults(data.results as ADNIResults);
            } else {
                throw new Error('Invalid response format');
            }
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'An error occurred';
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const getRiskColor = (level: string) => {
        switch (level) {
            case 'Stable': return '#10b981';
            case 'Mild Decline': return '#f59e0b';
            case 'Moderate Decline': return '#f97316';
            case 'Severe Decline': return '#ef4444';
            default: return '#6b7280';
        }
    };

    const prepareChartData = (): ChartDataPoint[] => {
        if (!results) return [];

        return results.timeline.map(point => ({
            visit: point.visit,
            months: point.months_from_baseline,
            mmse: point.scores.mmse,
            cdr_global: point.scores.cdr_global,
            cdr_sob: point.scores.cdr_sob,
            adas: point.scores.adas_totscore,
            isHistorical: point.is_historical,
            isPredicted: point.is_predicted,
            confidence: point.confidence
        }));
    };

    // Custom tooltip component for Recharts
    const CustomTooltip = ({ active, payload }: any) => {
        if (!active || !payload || !payload.length) return null;

        const data = payload[0].payload as ChartDataPoint;

        return (
            <div className="custom-tooltip">
                <p className="label"><strong>{data.visit}</strong></p>
                <p>Months: {data.months}</p>
                <p>Type: {data.isHistorical ? 'Historical' : 'Predicted'}</p>
                {data.confidence !== undefined && (
                    <p>Confidence: {(data.confidence * 100).toFixed(0)}%</p>
                )}
            </div>
        );
    };

    const chartData = prepareChartData();
    const lastHistoricalVisit = chartData.filter(d => d.isHistorical).pop()?.visit;

    return (
        <div className="adni-model-page">
            <div className="header">
                <h1>Alzheimer's Disease Progression Prediction</h1>
                <p className="subtitle">ADNI Multi-Modal LSTM Model</p>
            </div>

            <div className="run-section">
                <button
                    onClick={runModel}
                    disabled={loading}
                    className="run-model-btn"
                >
                    {loading ? (
                        <>
                            <span className="spinner"></span>
                            Running Model...
                        </>
                    ) : (
                        'Run ADNI Progression Model'
                    )}
                </button>
            </div>

            {error && (
                <div className="error-alert">
                    <strong>Error:</strong> {error}
                </div>
            )}

            {results && (
                <div className="results-container">
                    {/* Summary Card */}
                    <div className="summary-card">
                        <h2>Prediction Summary</h2>
                        <div className="risk-badge" style={{ backgroundColor: getRiskColor(results.summary.risk_level) }}>
                            {results.summary.risk_level}
                        </div>
                        <div className="summary-stats">
                            <div className="stat">
                                <span className="label">Prediction Horizon:</span>
                                <span className="value">{results.summary.prediction_horizon_months} months</span>
                            </div>
                            <div className="stat">
                                <span className="label">Overall Confidence:</span>
                                <span className="value">{results.confidence_score ? (results.confidence_score * 100).toFixed(0) : 0}%</span>
                            </div>
                        </div>
                    </div>

                    {/* MMSE Chart */}
                    <div className="chart-container">
                        <h3>MMSE Score (Cognitive Function)</h3>
                        <p className="chart-description">Range: 0-30 (higher is better)</p>
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis
                                    dataKey="visit"
                                    label={{ value: 'Visit', position: 'insideBottom', offset: -5 }}
                                />
                                <YAxis
                                    domain={[0, 30]}
                                    label={{ value: 'MMSE Score', angle: -90, position: 'insideLeft' }}
                                />
                                <Tooltip content={CustomTooltip as any} />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="mmse"
                                    stroke="#2563eb"
                                    strokeWidth={3}
                                    name="MMSE"
                                    dot={{ fill: '#2563eb', r: 5 }}
                                    connectNulls
                                />
                                {lastHistoricalVisit && (
                                    <ReferenceLine
                                        x={lastHistoricalVisit}
                                        stroke="#64748b"
                                        strokeDasharray="3 3"
                                        label="Current"
                                    />
                                )}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* CDR Global Chart */}
                    <div className="chart-container">
                        <h3>CDR Global (Dementia Rating)</h3>
                        <p className="chart-description">Range: 0-3 (lower is better)</p>
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="visit" />
                                <YAxis domain={[0, 3]} />
                                <Tooltip content={CustomTooltip as any} />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="cdr_global"
                                    stroke="#10b981"
                                    strokeWidth={3}
                                    name="CDR Global"
                                    dot={{ fill: '#10b981', r: 5 }}
                                    connectNulls
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* ADAS Chart */}
                    <div className="chart-container">
                        <h3>ADAS Total Score (Cognitive Assessment)</h3>
                        <p className="chart-description">Range: 0-70 (lower is better)</p>
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="visit" />
                                <YAxis domain={[0, 70]} />
                                <Tooltip content={CustomTooltip as any} />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="adas"
                                    stroke="#f59e0b"
                                    strokeWidth={3}
                                    name="ADAS"
                                    dot={{ fill: '#f59e0b', r: 5 }}
                                    connectNulls
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Clinical Interpretation */}
                    <div className="interpretation-card">
                        <h2>Clinical Interpretation</h2>
                        <div className="score-changes">
                            <h3>Predicted Changes from Baseline</h3>
                            <div className="changes-grid">
                                <div className="change-item">
                                    <span className="score-name">MMSE:</span>
                                    <span className={`change-value ${results.summary.predicted_changes.mmse < 0 ? 'negative' : 'positive'}`}>
                                        {results.summary.predicted_changes.mmse > 0 ? '+' : ''}
                                        {results.summary.predicted_changes.mmse.toFixed(1)} points
                                    </span>
                                </div>
                                <div className="change-item">
                                    <span className="score-name">CDR Global:</span>
                                    <span className={`change-value ${results.summary.predicted_changes.cdr_global > 0 ? 'negative' : 'positive'}`}>
                                        {results.summary.predicted_changes.cdr_global > 0 ? '+' : ''}
                                        {results.summary.predicted_changes.cdr_global.toFixed(2)}
                                    </span>
                                </div>
                                <div className="change-item">
                                    <span className="score-name">ADAS:</span>
                                    <span className={`change-value ${results.summary.predicted_changes.adas_totscore > 0 ? 'negative' : 'positive'}`}>
                                        {results.summary.predicted_changes.adas_totscore > 0 ? '+' : ''}
                                        {results.summary.predicted_changes.adas_totscore.toFixed(1)} points
                                    </span>
                                </div>
                            </div>
                        </div>

                        {results.metadata && results.metadata.observed_data_ratio < 0.5 && (
                            <div className="warning-box">
                                <strong>Note:</strong> Predictions made with limited imaging data.
                                Confidence may be lower than optimal. Consider uploading MRI/PET scans for better accuracy.
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default ADNIModelPage;
