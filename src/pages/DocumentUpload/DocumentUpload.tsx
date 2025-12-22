import { useState, useContext } from 'react';
import { PatientContext } from '@/contexts/PatientContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Upload, FileText, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { useSnackbar } from 'notistack';

const BACKEND_URL = 'http://localhost:8001/api';

interface UploadStatus {
    status: 'idle' | 'uploading' | 'success' | 'error';
    message?: string;
}

const DocumentUpload = () => {
    const { selectedPatient } = useContext(PatientContext);
    const { enqueueSnackbar } = useSnackbar();
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [category, setCategory] = useState<string>('lab_report');
    const [uploadStatus, setUploadStatus] = useState<UploadStatus>({ status: 'idle' });

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            // Validate file type
            const validTypes = ['application/pdf', 'text/plain'];
            if (!validTypes.includes(file.type)) {
                enqueueSnackbar('Please upload a PDF or TXT file', { variant: 'error' });
                return;
            }

            // Validate file size (50MB max)
            if (file.size > 50 * 1024 * 1024) {
                enqueueSnackbar('File size must be less than 50MB', { variant: 'error' });
                return;
            }

            setSelectedFile(file);
            setUploadStatus({ status: 'idle' });
        }
    };

    const handleUpload = async () => {
        if (!selectedFile || !selectedPatient) {
            enqueueSnackbar('Please select a file and ensure patient is loaded', { variant: 'error' });
            return;
        }

        setUploadStatus({ status: 'uploading', message: 'Uploading document...' });

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('patient_id', selectedPatient.id!);
            formData.append('category', category);

            const response = await fetch(`${BACKEND_URL}/files/upload`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('Upload failed');
            }

            const result = await response.json();

            setUploadStatus({
                status: 'success',
                message: 'Document uploaded and processed successfully! Clinical data has been extracted and stored in FHIR database.'
            });

            enqueueSnackbar('Document processed successfully', { variant: 'success' });

            // Reset form
            setSelectedFile(null);
            setCategory('lab_report');

            // Reset file input
            const fileInput = document.getElementById('file-upload') as HTMLInputElement;
            if (fileInput) fileInput.value = '';

            // Refresh page after 2 seconds to show updated data
            setTimeout(() => {
                window.location.reload();
            }, 2000);

        } catch (error) {
            console.error('Upload error:', error);
            setUploadStatus({
                status: 'error',
                message: 'Failed to upload document. Please try again.'
            });
            enqueueSnackbar('Upload failed', { variant: 'error' });
        }
    };

    if (!selectedPatient) {
        return (
            <div className="flex items-center justify-center h-full">
                <Card className="w-full max-w-md">
                    <CardHeader>
                        <CardTitle>No Patient Selected</CardTitle>
                        <CardDescription>Please select a patient to upload documents</CardDescription>
                    </CardHeader>
                </Card>
            </div>
        );
    }

    return (
        <div className="container mx-auto p-6 max-w-4xl">
            <div className="mb-6">
                <h1 className="text-3xl font-bold">Document Upload</h1>
                <p className="text-muted-foreground mt-2">
                    Upload clinical documents (PDF/TXT) to extract and store patient data
                </p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Upload Clinical Document</CardTitle>
                    <CardDescription>
                        <div>
                            Upload lab reports, clinical notes, or other medical documents. The system will automatically extract:
                            <ul className="list-disc list-inside mt-2 space-y-1">
                                <li>Vital signs (Blood Pressure, Heart Rate, Temperature, etc.)</li>
                                <li>Lab results (Glucose, Cholesterol, HbA1c, Hemoglobin, etc.)</li>
                                <li>Diagnoses and conditions</li>
                                <li>Medications</li>
                            </ul>
                        </div>
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Patient Info */}
                    <div className="bg-muted p-4 rounded-lg">
                        <p className="text-sm font-medium">Patient: {selectedPatient.name?.[0]?.given?.[0]} {selectedPatient.name?.[0]?.family}</p>
                        <p className="text-sm text-muted-foreground">ID: {selectedPatient.id}</p>
                    </div>

                    {/* File Upload */}
                    <div className="space-y-2">
                        <Label htmlFor="file-upload">Select Document</Label>
                        <div className="flex items-center gap-4">
                            <Input
                                id="file-upload"
                                type="file"
                                accept=".pdf,.txt"
                                onChange={handleFileChange}
                                className="flex-1"
                            />
                            {selectedFile && (
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <FileText className="h-4 w-4" />
                                    <span>{selectedFile.name}</span>
                                    <span className="text-xs">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Category Selection */}
                    <div className="space-y-2">
                        <Label htmlFor="category">Document Category</Label>
                        <Select value={category} onValueChange={setCategory}>
                            <SelectTrigger id="category">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="lab_report">Lab Report</SelectItem>
                                <SelectItem value="imaging">Imaging Report</SelectItem>
                                <SelectItem value="clinical_note">Clinical Note</SelectItem>
                                <SelectItem value="prescription">Prescription</SelectItem>
                                <SelectItem value="discharge_summary">Discharge Summary</SelectItem>
                                <SelectItem value="other">Other</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Upload Button */}
                    <Button
                        onClick={handleUpload}
                        disabled={!selectedFile || uploadStatus.status === 'uploading'}
                        className="w-full"
                        size="lg"
                    >
                        {uploadStatus.status === 'uploading' ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Processing...
                            </>
                        ) : (
                            <>
                                <Upload className="mr-2 h-4 w-4" />
                                Upload and Process Document
                            </>
                        )}
                    </Button>

                    {/* Status Messages */}
                    {uploadStatus.status === 'success' && (
                        <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
                            <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                            <div className="flex-1">
                                <p className="font-medium text-green-900">Success!</p>
                                <p className="text-sm text-green-700 mt-1">{uploadStatus.message}</p>
                            </div>
                        </div>
                    )}

                    {uploadStatus.status === 'error' && (
                        <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-lg">
                            <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                            <div className="flex-1">
                                <p className="font-medium text-red-900">Error</p>
                                <p className="text-sm text-red-700 mt-1">{uploadStatus.message}</p>
                            </div>
                        </div>
                    )}

                    {uploadStatus.status === 'uploading' && (
                        <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                            <Loader2 className="h-5 w-5 text-blue-600 mt-0.5 animate-spin" />
                            <div className="flex-1">
                                <p className="font-medium text-blue-900">Processing</p>
                                <p className="text-sm text-blue-700 mt-1">
                                    Extracting clinical data from document and storing in FHIR database...
                                </p>
                            </div>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Information Card */}
            <Card className="mt-6">
                <CardHeader>
                    <CardTitle>How It Works</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="space-y-2">
                        <h3 className="font-medium">1. Upload Document</h3>
                        <p className="text-sm text-muted-foreground">
                            Select a PDF or TXT file containing clinical information (lab reports, clinical notes, etc.)
                        </p>
                    </div>
                    <div className="space-y-2">
                        <h3 className="font-medium">2. Automatic Extraction</h3>
                        <p className="text-sm text-muted-foreground">
                            The system automatically extracts vital signs, lab results, diagnoses, and medications using pattern matching
                        </p>
                    </div>
                    <div className="space-y-2">
                        <h3 className="font-medium">3. FHIR Storage</h3>
                        <p className="text-sm text-muted-foreground">
                            Extracted data is converted to FHIR-compliant resources (Observations, Conditions, MedicationRequests) and stored in the FHIR server
                        </p>
                    </div>
                    <div className="space-y-2">
                        <h3 className="font-medium">4. View on Dashboard</h3>
                        <p className="text-sm text-muted-foreground">
                            Updated clinical data will be visible on the patient dashboard immediately after processing
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default DocumentUpload;
