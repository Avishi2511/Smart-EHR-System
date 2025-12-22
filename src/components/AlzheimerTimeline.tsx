import { useState, useEffect } from "react";
import { Brain, TrendingDown, Activity } from "lucide-react";
import "./AlzheimerTimeline.css";

interface PredictionPoint {
    months_from_last_visit: number;
    predicted_scores: {
        MMSE: number;
        CDR_Global: number;
        CDR_SOB: number;
        ADAS_Cog: number;
    };
}

interface AlzheimerTimelineProps {
    predictions: PredictionPoint[];
}

// Alzheimer's stage classification based on CDR score
function getAlzheimerStage(cdrGlobal: number): {
    stage: string;
    color: string;
    bgColor: string;
} {
    if (cdrGlobal === 0) {
        return { stage: "Normal", color: "#10b981", bgColor: "rgba(16, 185, 129, 0.1)" };
    } else if (cdrGlobal === 0.5) {
        return { stage: "Very Mild", color: "#f59e0b", bgColor: "rgba(245, 158, 11, 0.1)" };
    } else if (cdrGlobal === 1) {
        return { stage: "Mild", color: "#f97316", bgColor: "rgba(249, 115, 22, 0.1)" };
    } else if (cdrGlobal === 2) {
        return { stage: "Moderate", color: "#ef4444", bgColor: "rgba(239, 68, 68, 0.1)" };
    } else {
        return { stage: "Severe", color: "#991b1b", bgColor: "rgba(153, 27, 27, 0.1)" };
    }
}



function AlzheimerTimeline({ predictions }: AlzheimerTimelineProps) {
    const [visiblePoints, setVisiblePoints] = useState(0);
    const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

    // Animate points appearing one by one
    useEffect(() => {
        const interval = setInterval(() => {
            setVisiblePoints((prev) => {
                if (prev < predictions.length) {
                    return prev + 1;
                }
                clearInterval(interval);
                return prev;
            });
        }, 200); // 200ms per point = 3 seconds total for 15 points

        return () => clearInterval(interval);
    }, [predictions.length]);



    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center">
                            <Brain className="w-6 h-6 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-slate-800">
                                Alzheimer's Progression Timeline
                            </h1>
                            <p className="text-slate-600">7.5-year disease progression forecast</p>
                        </div>
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                    <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                        <div className="flex items-center gap-2 mb-2">
                            <TrendingDown className="w-4 h-4 text-purple-600" />
                            <span className="text-sm text-slate-600">Predictions</span>
                        </div>
                        <p className="text-2xl font-bold text-slate-800">15 Timepoints</p>
                    </div>
                    <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                        <div className="flex items-center gap-2 mb-2">
                            <Activity className="w-4 h-4 text-pink-600" />
                            <span className="text-sm text-slate-600">Horizon</span>
                        </div>
                        <p className="text-2xl font-bold text-slate-800">90 Months</p>
                    </div>
                    <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                        <div className="flex items-center gap-2 mb-2">
                            <Brain className="w-4 h-4 text-indigo-600" />
                            <span className="text-sm text-slate-600">Final Stage</span>
                        </div>
                        <p className="text-2xl font-bold text-slate-800">
                            {getAlzheimerStage(predictions[predictions.length - 1]?.predicted_scores.CDR_Global || 0).stage}
                        </p>
                    </div>
                </div>

                {/* Timeline Visualization */}
                <div className="bg-white rounded-2xl shadow-xl p-8 border border-slate-200">
                    <h2 className="text-xl font-bold text-slate-800 mb-6">Disease Progression Timeline</h2>

                    {/* Timeline Container */}
                    <div className="relative">
                        {/* Timeline SVG */}
                        <div className="relative" style={{ height: "400px" }}>
                            <svg width="100%" height="100%" viewBox="0 0 1000 400" preserveAspectRatio="none" className="timeline-svg">
                                <defs>
                                    <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                        <stop offset="0%" stopColor="#6366f1" />
                                        <stop offset="50%" stopColor="#a855f7" />
                                        <stop offset="100%" stopColor="#ec4899" />
                                    </linearGradient>
                                </defs>

                                {/* Horizontal stage bands based on ADAS-Cog scores */}
                                {/* Normal: 0-10 (green) */}
                                <rect
                                    x="0"
                                    y={400 - (10 / 70) * 400}
                                    width="1000"
                                    height={(10 / 70) * 400}
                                    fill="rgba(16, 185, 129, 0.15)"
                                />
                                {/* Very Mild: 10-20 (amber) */}
                                <rect
                                    x="0"
                                    y={400 - (20 / 70) * 400}
                                    width="1000"
                                    height={(10 / 70) * 400}
                                    fill="rgba(245, 158, 11, 0.15)"
                                />
                                {/* Mild: 20-35 (orange) */}
                                <rect
                                    x="0"
                                    y={400 - (35 / 70) * 400}
                                    width="1000"
                                    height={(15 / 70) * 400}
                                    fill="rgba(249, 115, 22, 0.15)"
                                />
                                {/* Moderate: 35-55 (red) */}
                                <rect
                                    x="0"
                                    y={400 - (55 / 70) * 400}
                                    width="1000"
                                    height={(20 / 70) * 400}
                                    fill="rgba(239, 68, 68, 0.15)"
                                />
                                {/* Severe: 55-70 (dark red) */}
                                <rect
                                    x="0"
                                    y="0"
                                    width="1000"
                                    height={(15 / 70) * 400}
                                    fill="rgba(153, 27, 27, 0.15)"
                                />

                                {/* Grid lines */}
                                {[0, 1, 2, 3, 4, 5, 6, 7].map((i) => (
                                    <line
                                        key={`grid-${i}`}
                                        x1="0"
                                        y1={(i / 7) * 400}
                                        x2="1000"
                                        y2={(i / 7) * 400}
                                        stroke="#e2e8f0"
                                        strokeWidth="1"
                                        strokeDasharray="4 4"
                                    />
                                ))}

                                {/* Connected line through all points */}
                                <polyline
                                    points={predictions
                                        .map((point, index) => {
                                            const x = (index / (predictions.length - 1)) * 1000;
                                            const adasScore = Math.min(Math.max(point.predicted_scores.ADAS_Cog, 0), 70);
                                            const y = 400 - (adasScore / 70) * 400;
                                            return `${x},${y}`;
                                        })
                                        .join(" ")}
                                    fill="none"
                                    stroke="#6366f1"
                                    strokeWidth="4"
                                />

                                {/* Data points */}
                                {predictions.slice(0, visiblePoints).map((point, index) => {
                                    const x = (index / (predictions.length - 1)) * 1000;
                                    const adasScore = Math.min(Math.max(point.predicted_scores.ADAS_Cog, 0), 70);
                                    const y = 400 - (adasScore / 70) * 400;
                                    const stageInfo = getAlzheimerStage(point.predicted_scores.CDR_Global);

                                    return (
                                        <g key={index} className="timeline-point-group">
                                            {/* Outer ring animation */}
                                            <circle
                                                cx={x}
                                                cy={y}
                                                r="12"
                                                fill="none"
                                                stroke={stageInfo.color}
                                                strokeWidth="2"
                                                opacity="0.3"
                                                className="point-ring"
                                                style={{ animationDelay: `${index * 0.2}s` }}
                                            />

                                            {/* Main point */}
                                            <circle
                                                cx={x}
                                                cy={y}
                                                r="8"
                                                fill={stageInfo.color}
                                                className="timeline-point"
                                                style={{ animationDelay: `${index * 0.2}s` }}
                                                onMouseEnter={() => setHoveredIndex(index)}
                                                onMouseLeave={() => setHoveredIndex(null)}
                                            />

                                            {/* Inner glow */}
                                            <circle
                                                cx={x}
                                                cy={y}
                                                r="4"
                                                fill="white"
                                                opacity="0.8"
                                            />
                                        </g>
                                    );
                                })}
                            </svg>

                            {/* Tooltip - outside SVG */}
                            {hoveredIndex !== null && (
                                <div
                                    className="absolute bg-white rounded-lg shadow-2xl p-4 border-2 z-50"
                                    style={{
                                        left: `${(hoveredIndex / (predictions.length - 1)) * 100}%`,
                                        top: "50%",
                                        transform: "translate(-50%, -50%)",
                                        borderColor: getAlzheimerStage(
                                            predictions[hoveredIndex].predicted_scores.CDR_Global
                                        ).color,
                                        pointerEvents: "none"
                                    }}
                                >
                                    <div className="mb-3">
                                        <p className="text-sm font-bold text-slate-800">
                                            +{predictions[hoveredIndex].months_from_last_visit} months
                                        </p>
                                    </div>

                                    <div className="space-y-1">
                                        <div className="flex justify-between items-center gap-4">
                                            <span className="text-xs text-slate-600">ADAS-Cog:</span>
                                            <span className="text-sm font-semibold text-slate-800">
                                                {predictions[hoveredIndex].predicted_scores.ADAS_Cog.toFixed(1)}
                                            </span>
                                        </div>
                                        <div className="flex justify-between items-center gap-4">
                                            <span className="text-xs text-slate-600">MMSE:</span>
                                            <span className="text-sm font-semibold text-slate-800">
                                                {predictions[hoveredIndex].predicted_scores.MMSE.toFixed(1)}
                                            </span>
                                        </div>
                                        <div className="flex justify-between items-center gap-4">
                                            <span className="text-xs text-slate-600">CDR-Global:</span>
                                            <span className="text-sm font-semibold text-slate-800">
                                                {predictions[hoveredIndex].predicted_scores.CDR_Global.toFixed(1)}
                                            </span>
                                        </div>
                                        <div className="flex justify-between items-center gap-4">
                                            <span className="text-xs text-slate-600">CDR-SOB:</span>
                                            <span className="text-sm font-semibold text-slate-800">
                                                {predictions[hoveredIndex].predicted_scores.CDR_SOB.toFixed(1)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* X-axis labels */}
                        <div className="flex justify-between mt-4 text-xs text-slate-600">
                            <span>Baseline</span>
                            <span>+45 months</span>
                            <span>+90 months (7.5 years)</span>
                        </div>

                        {/* Y-axis label */}
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-12 -rotate-90">
                            <span className="text-xs text-slate-600 whitespace-nowrap">ADAS-Cog Score (0-70)</span>
                        </div>
                    </div>
                </div>

                {/* Stage Legend */}
                <div className="mt-6 bg-white rounded-xl p-6 shadow-sm border border-slate-200">
                    <h3 className="text-sm font-semibold text-slate-700 mb-4">Disease Stage Legend</h3>
                    <div className="flex flex-wrap gap-4">
                        {[
                            { stage: "Normal", cdr: 0 },
                            { stage: "Very Mild", cdr: 0.5 },
                            { stage: "Mild", cdr: 1 },
                            { stage: "Moderate", cdr: 2 },
                            { stage: "Severe", cdr: 3 },
                        ].map(({ stage, cdr }) => {
                            const info = getAlzheimerStage(cdr);
                            return (
                                <div key={stage} className="flex items-center gap-2">
                                    <div
                                        className="w-4 h-4 rounded-full"
                                        style={{ background: info.color }}
                                    />
                                    <span className="text-sm text-slate-600">{stage}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AlzheimerTimeline;
