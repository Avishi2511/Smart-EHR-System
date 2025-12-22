import { useEffect, useState, useContext } from "react";
import { PatientContext } from "@/contexts/PatientContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Loader2, FileText, Activity, Heart, Brain, Eye, Ear, Stethoscope, File, ExternalLink } from "lucide-react";
import axios from "axios";
import dayjs from "dayjs";

interface Observation {
    id: string;
    patient_id: string;
    observation_type: string;
    value: string | null;
    unit: string | null;
    effective_datetime: string;
    doctor_remarks: string | null;
    medication_prescribed: string | null;
    document_link: string | null;
    status: string;
}

interface ObservationListResponse {
    observations: Observation[];
    total: number;
    filtered: number;
}

interface BackendPatient {
    id: string;
    fhir_id: string;
}

// Observation type icons and labels
const OBSERVATION_CONFIG: Record<string, { icon: any; label: string; color: string }> = {
    glucose: { icon: Activity, label: "Glucose", color: "bg-blue-100 text-blue-800" },
    hba1c: { icon: Activity, label: "HbA1c", color: "bg-purple-100 text-purple-800" },
    creatinine: { icon: Activity, label: "Creatinine", color: "bg-green-100 text-green-800" },
    heart_rate: { icon: Heart, label: "Heart Rate", color: "bg-red-100 text-red-800" },
    bp_systolic: { icon: Heart, label: "BP Systolic", color: "bg-orange-100 text-orange-800" },
    bp_diastolic: { icon: Heart, label: "BP Diastolic", color: "bg-orange-100 text-orange-800" },
    mri: { icon: Brain, label: "MRI Scan", color: "bg-indigo-100 text-indigo-800" },
    pet: { icon: Brain, label: "PET Scan", color: "bg-indigo-100 text-indigo-800" },
    ct_scan: { icon: Brain, label: "CT Scan", color: "bg-indigo-100 text-indigo-800" },
    general_visit: { icon: Stethoscope, label: "General Visit", color: "bg-teal-100 text-teal-800" },
    eye_checkup: { icon: Eye, label: "Eye Checkup", color: "bg-cyan-100 text-cyan-800" },
    ent: { icon: Ear, label: "ENT", color: "bg-pink-100 text-pink-800" },
    alzheimer: { icon: Brain, label: "Alzheimer Assessment", color: "bg-violet-100 text-violet-800" },
    clinical_document: { icon: FileText, label: "Clinical Document", color: "bg-gray-100 text-gray-800" },
    other: { icon: File, label: "Other", color: "bg-slate-100 text-slate-800" },
};

function Observations() {
    const { selectedPatient } = useContext(PatientContext);
    const [observations, setObservations] = useState<Observation[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Filters
    const [limitFilter, setLimitFilter] = useState<string>("all");
    const [dateRangeFilter, setDateRangeFilter] = useState<string>("all");
    const [typeFilter, setTypeFilter] = useState<string>("all");

    // Stats
    const [totalCount, setTotalCount] = useState(0);
    const [filteredCount, setFilteredCount] = useState(0);

    useEffect(() => {
        const fetchObservations = async () => {
            if (!selectedPatient?.id) return;

            try {
                setLoading(true);
                setError(null);

                // Get backend patient ID from FHIR ID
                const patientResponse = await axios.get<BackendPatient>(
                    `http://localhost:8001/api/patients/by-fhir/${selectedPatient.id}`
                );
                const backendPatientId = patientResponse.data.id;

                // Build query params
                const params: any = {};

                // Limit filter
                if (limitFilter !== "all") {
                    params.limit = parseInt(limitFilter);
                }

                // Date range filter
                if (dateRangeFilter !== "all") {
                    const now = new Date();
                    let startDate: Date;

                    switch (dateRangeFilter) {
                        case "6months":
                            startDate = new Date(now.setMonth(now.getMonth() - 6));
                            break;
                        case "1year":
                            startDate = new Date(now.setFullYear(now.getFullYear() - 1));
                            break;
                        case "2years":
                            startDate = new Date(now.setFullYear(now.getFullYear() - 2));
                            break;
                        default:
                            startDate = new Date(0);
                    }
                    params.start_date = startDate.toISOString();
                }

                // Type filter
                if (typeFilter !== "all") {
                    params.observation_type = typeFilter;
                }

                // Fetch observations
                const response = await axios.get<ObservationListResponse>(
                    `http://localhost:8001/api/observations/${backendPatientId}`,
                    { params }
                );

                setObservations(response.data.observations);
                setTotalCount(response.data.total);
                setFilteredCount(response.data.filtered);
            } catch (err) {
                console.error("Error fetching observations:", err);
                setError("Failed to load observations");
            } finally {
                setLoading(false);
            }
        };

        fetchObservations();
    }, [selectedPatient?.id, limitFilter, dateRangeFilter, typeFilter]);

    const getObservationIcon = (type: string) => {
        const config = OBSERVATION_CONFIG[type] || OBSERVATION_CONFIG.other;
        const Icon = config.icon;
        return <Icon className="h-4 w-4" />;
    };

    const getObservationBadge = (type: string) => {
        const config = OBSERVATION_CONFIG[type] || OBSERVATION_CONFIG.other;
        return (
            <Badge variant="outline" className={config.color}>
                {config.label}
            </Badge>
        );
    };

    const truncateText = (text: string | null, maxLength: number = 50) => {
        if (!text) return "-";
        return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
    };

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
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Observations</h2>
                    <p className="text-muted-foreground mt-1">
                        Showing {observations.length} of {filteredCount} observations
                        {filteredCount !== totalCount && ` (${totalCount} total)`}
                    </p>
                </div>
            </div>

            {/* Filters */}
            <Card>
                <CardHeader>
                    <CardTitle>Filters</CardTitle>
                    <CardDescription>Filter observations by count, date range, and type</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Limit Filter */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Number of Observations</label>
                            <Select value={limitFilter} onValueChange={setLimitFilter}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Observations</SelectItem>
                                    <SelectItem value="10">Last 10</SelectItem>
                                    <SelectItem value="25">Last 25</SelectItem>
                                    <SelectItem value="50">Last 50</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Date Range Filter */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Date Range</label>
                            <Select value={dateRangeFilter} onValueChange={setDateRangeFilter}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Time</SelectItem>
                                    <SelectItem value="6months">Last 6 Months</SelectItem>
                                    <SelectItem value="1year">Last 1 Year</SelectItem>
                                    <SelectItem value="2years">Last 2 Years</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Type Filter */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Observation Type</label>
                            <Select value={typeFilter} onValueChange={setTypeFilter}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Types</SelectItem>
                                    <SelectItem value="glucose">Glucose</SelectItem>
                                    <SelectItem value="hba1c">HbA1c</SelectItem>
                                    <SelectItem value="creatinine">Creatinine</SelectItem>
                                    <SelectItem value="heart_rate">Heart Rate</SelectItem>
                                    <SelectItem value="bp_systolic">BP Systolic</SelectItem>
                                    <SelectItem value="bp_diastolic">BP Diastolic</SelectItem>
                                    <SelectItem value="mri">MRI</SelectItem>
                                    <SelectItem value="pet">PET Scan</SelectItem>
                                    <SelectItem value="ct_scan">CT Scan</SelectItem>
                                    <SelectItem value="general_visit">General Visit</SelectItem>
                                    <SelectItem value="eye_checkup">Eye Checkup</SelectItem>
                                    <SelectItem value="ent">ENT</SelectItem>
                                    <SelectItem value="alzheimer">Alzheimer</SelectItem>
                                    <SelectItem value="clinical_document">Clinical Document</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Observations Table */}
            <Card>
                <CardHeader>
                    <CardTitle>Observation Records</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="rounded-md border">
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Type</TableHead>
                                    <TableHead>ID</TableHead>
                                    <TableHead>Value</TableHead>
                                    <TableHead>Date/Time</TableHead>
                                    <TableHead>Doctor Remarks</TableHead>
                                    <TableHead>Medication</TableHead>
                                    <TableHead>Link</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {observations.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                                            No observations found matching the selected filters
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    observations.map((obs) => (
                                        <TableRow key={obs.id}>
                                            <TableCell>{getObservationBadge(obs.observation_type)}</TableCell>
                                            <TableCell className="font-mono text-xs">{obs.id.substring(0, 8)}</TableCell>
                                            <TableCell>
                                                {obs.value && obs.unit ? `${obs.value} ${obs.unit}` : obs.value || "-"}
                                            </TableCell>
                                            <TableCell className="text-sm">
                                                {dayjs(obs.effective_datetime).format("MMM D, YYYY h:mm A")}
                                            </TableCell>
                                            <TableCell className="max-w-xs">
                                                <span className="text-sm text-muted-foreground">
                                                    {truncateText(obs.doctor_remarks)}
                                                </span>
                                            </TableCell>
                                            <TableCell className="max-w-xs">
                                                <span className="text-sm text-muted-foreground">
                                                    {truncateText(obs.medication_prescribed)}
                                                </span>
                                            </TableCell>
                                            <TableCell>
                                                {obs.document_link ? (
                                                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                                        <ExternalLink className="h-4 w-4" />
                                                    </Button>
                                                ) : (
                                                    <span className="text-muted-foreground text-sm">-</span>
                                                )}
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}

export default Observations;
