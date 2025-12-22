import { useEffect, useState, useContext } from "react";
import { PatientContext } from "@/contexts/PatientContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Loader2 } from "lucide-react";
import axios from "axios";
import dayjs from "dayjs";

interface HbA1cData {
    id: string;
    patient_id: string;
    parameter_name: string;
    value: number;
    unit: string;
    source: string;
    source_id: string | null;
    timestamp: string;
    created_at: string;
}

interface BloodPressureData {
    timestamp: string;
    systolic: number;
    diastolic: number;
    unit: string;
}

interface ChartDataPoint {
    date: string;
    value: number;
    displayDate: string;
}

interface BPChartDataPoint {
    date: string;
    systolic: number;
    diastolic: number;
    displayDate: string;
}

interface BackendPatient {
    id: string;
    fhir_id: string;
}

function Analytics() {
    const { selectedPatient } = useContext(PatientContext);
    const [hba1cData, setHba1cData] = useState<ChartDataPoint[]>([]);
    const [bpData, setBpData] = useState<BPChartDataPoint[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchAnalyticsData = async () => {
            if (!selectedPatient?.id) return;

            try {
                setLoading(true);
                setError(null);

                // First, get the backend patient ID from FHIR ID
                const patientResponse = await axios.get<BackendPatient>(
                    `http://localhost:8001/api/patients/by-fhir/${selectedPatient.id}`
                );
                const backendPatientId = patientResponse.data.id;

                // Fetch HbA1c data
                const hba1cResponse = await axios.get<HbA1cData[]>(
                    `http://localhost:8001/api/analytics/${backendPatientId}/hba1c`
                );

                // Fetch Blood Pressure data
                const bpResponse = await axios.get<BloodPressureData[]>(
                    `http://localhost:8001/api/analytics/${backendPatientId}/blood-pressure`
                );

                // Transform HbA1c data for chart
                const transformedHba1c = hba1cResponse.data.map((item) => ({
                    date: item.timestamp,
                    value: item.value,
                    displayDate: dayjs(item.timestamp).format("MMM YYYY"),
                }));

                // Transform BP data for chart
                const transformedBp = bpResponse.data.map((item) => ({
                    date: item.timestamp,
                    systolic: item.systolic,
                    diastolic: item.diastolic,
                    displayDate: dayjs(item.timestamp).format("MMM YYYY"),
                }));

                setHba1cData(transformedHba1c);
                setBpData(transformedBp);
            } catch (err) {
                console.error("Error fetching analytics data:", err);
                setError("Failed to load analytics data");
            } finally {
                setLoading(false);
            }
        };

        fetchAnalyticsData();
    }, [selectedPatient?.id]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-full">
                <p className="text-destructive">{error}</p>
            </div>
        );
    }

    return (
        <div className="flex-1 space-y-6 p-8 pt-6">
            <div className="flex items-center justify-between space-y-2">
                <h2 className="text-3xl font-bold tracking-tight">Analytics</h2>
            </div>

            <div className="grid gap-6 grid-cols-1">
                {/* HbA1c Chart */}
                <Card className="col-span-1">
                    <CardHeader>
                        <CardTitle>HbA1c Levels Over Time</CardTitle>
                        <CardDescription>
                            Hemoglobin A1c (HbA1c) levels showing long-term blood sugar control
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart
                                data={hba1cData}
                                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                            >
                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                <XAxis
                                    dataKey="displayDate"
                                    stroke="#6b7280"
                                    fontSize={12}
                                    tickLine={false}
                                />
                                <YAxis
                                    stroke="#6b7280"
                                    fontSize={12}
                                    tickLine={false}
                                    domain={[4, 8]}
                                    label={{ value: "HbA1c (%)", angle: -90, position: "insideLeft" }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: "white",
                                        border: "1px solid #e5e7eb",
                                        borderRadius: "8px",
                                    }}
                                    formatter={(value: number) => [`${value.toFixed(1)}%`, "HbA1c"]}
                                />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="value"
                                    name="HbA1c Level"
                                    stroke="#ef4444"
                                    strokeWidth={2}
                                    dot={{ fill: "#ef4444", r: 4 }}
                                    activeDot={{ r: 6 }}
                                />
                                {/* Reference line for normal range */}
                                <Line
                                    type="monotone"
                                    dataKey={() => 5.7}
                                    name="Normal Upper Limit"
                                    stroke="#10b981"
                                    strokeWidth={1}
                                    strokeDasharray="5 5"
                                    dot={false}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                        <div className="mt-4 flex items-center justify-center gap-6 text-sm text-muted-foreground">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                                <span>Normal: &lt; 5.7%</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                                <span>Prediabetes: 5.7% - 6.4%</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                                <span>Diabetes: ≥ 6.5%</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Blood Pressure Chart */}
                <Card className="col-span-1">
                    <CardHeader>
                        <CardTitle>Blood Pressure Over Time</CardTitle>
                        <CardDescription>
                            Systolic and diastolic blood pressure measurements
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart
                                data={bpData}
                                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                            >
                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                <XAxis
                                    dataKey="displayDate"
                                    stroke="#6b7280"
                                    fontSize={12}
                                    tickLine={false}
                                />
                                <YAxis
                                    stroke="#6b7280"
                                    fontSize={12}
                                    tickLine={false}
                                    domain={[60, 140]}
                                    label={{ value: "Blood Pressure (mmHg)", angle: -90, position: "insideLeft" }}
                                />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: "white",
                                        border: "1px solid #e5e7eb",
                                        borderRadius: "8px",
                                    }}
                                    formatter={(value: number, name: string) => [
                                        `${value} mmHg`,
                                        name === "systolic" ? "Systolic" : "Diastolic",
                                    ]}
                                />
                                <Legend />
                                <Line
                                    type="monotone"
                                    dataKey="systolic"
                                    name="Systolic"
                                    stroke="#3b82f6"
                                    strokeWidth={2}
                                    dot={{ fill: "#3b82f6", r: 4 }}
                                    activeDot={{ r: 6 }}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="diastolic"
                                    name="Diastolic"
                                    stroke="#8b5cf6"
                                    strokeWidth={2}
                                    dot={{ fill: "#8b5cf6", r: 4 }}
                                    activeDot={{ r: 6 }}
                                />
                                {/* Reference lines for normal range */}
                                <Line
                                    type="monotone"
                                    dataKey={() => 120}
                                    name="Systolic Normal Upper"
                                    stroke="#10b981"
                                    strokeWidth={1}
                                    strokeDasharray="5 5"
                                    dot={false}
                                />
                                <Line
                                    type="monotone"
                                    dataKey={() => 80}
                                    name="Diastolic Normal Upper"
                                    stroke="#10b981"
                                    strokeWidth={1}
                                    strokeDasharray="5 5"
                                    dot={false}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                        <div className="mt-4 flex items-center justify-center gap-6 text-sm text-muted-foreground">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                                <span>Normal: &lt; 120/80 mmHg</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                                <span>Elevated: 120-129/&lt;80 mmHg</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                                <span>High: ≥ 130/80 mmHg</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}

export default Analytics;
