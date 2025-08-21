import React, { useState, useEffect } from 'react';
import { User, Calendar, Droplet, AlertTriangle, Heart, Save, Loader2, Database, RefreshCw } from 'lucide-react';
import { writeCardData, CardData } from '@/api/cardApi';
import { fetchAllPatients, checkFhirServerStatus } from '@/api/fhirPatientApi';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

function CardWriter() {
  const [form, setForm] = useState<CardData>({
    patientId: '',
    name: '',
    bloodType: '',
    allergies: '',
    emergencyContact: '',
    chronicConditions: ''
  });
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [patients, setPatients] = useState<any[]>([]);
  const [loadingPatients, setLoadingPatients] = useState(false);
  const [fhirServerOnline, setFhirServerOnline] = useState(false);
  const [selectedPatientId, setSelectedPatientId] = useState('');

  useEffect(() => {
    checkServerAndLoadPatients();
  }, []);

  const checkServerAndLoadPatients = async () => {
    setLoadingPatients(true);
    try {
      const isOnline = await checkFhirServerStatus();
      setFhirServerOnline(isOnline);
      
      if (isOnline) {
        const patientsData = await fetchAllPatients();
        setPatients(patientsData);
      }
    } catch (error) {
      console.error('Error checking server or loading patients:', error);
      setFhirServerOnline(false);
    }
    setLoadingPatients(false);
  };

  const handlePatientSelect = (patientId: string) => {
    setSelectedPatientId(patientId);
    const selectedPatient = patients.find(p => p.id === patientId);
    
    if (selectedPatient) {
      // Auto-populate form with patient data
      const patientName = selectedPatient.name?.[0] 
        ? `${selectedPatient.name[0].given?.join(' ') || ''} ${selectedPatient.name[0].family || ''}`.trim()
        : '';
      
      // Extract emergency contact from telecom
      const emergencyContact = selectedPatient.telecom?.find((t: any) => t.system === 'phone')?.value || '';
      
      setForm({
        patientId: selectedPatient.id,
        name: patientName,
        bloodType: '', // This would need to be extracted from observations or extensions
        allergies: '', // This would need to be extracted from AllergyIntolerance resources
        emergencyContact: emergencyContact,
        chronicConditions: '' // This would need to be extracted from Condition resources
      });
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatus('⏳ Waiting for card...');
    try {
      const res = await writeCardData(form);
      setStatus(`✅ ${res.message}`);
    } catch (err: any) {
      setStatus(`❌ ${err.response?.data?.error || err.message}`);
    }
    setLoading(false);
  };

  const handleClear = () => {
    setForm({
      patientId: '',
      name: '',
      bloodType: '',
      allergies: '',
      emergencyContact: '',
      chronicConditions: ''
    });
    setStatus('');
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-6 w-6" />
            Write Health Info to NFC Card
          </CardTitle>
          <CardDescription>
            Enter patient health information to write to the NFC card for emergency access
          </CardDescription>
        </CardHeader>
        <CardContent>
          {/* Patient Selection Section */}
          {fhirServerOnline && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Database className="h-5 w-5 text-green-600" />
                  <span className="font-medium text-green-800">FHIR Database Connected</span>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={checkServerAndLoadPatients}
                  disabled={loadingPatients}
                >
                  {loadingPatients ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                </Button>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="patientSelect">Select Patient from Database</Label>
                <Select value={selectedPatientId} onValueChange={handlePatientSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a patient to auto-fill data..." />
                  </SelectTrigger>
                  <SelectContent>
                    {patients.map((patient) => {
                      const name = patient.name?.[0] 
                        ? `${patient.name[0].given?.join(' ') || ''} ${patient.name[0].family || ''}`.trim()
                        : 'Unknown Name';
                      return (
                        <SelectItem key={patient.id} value={patient.id}>
                          {name} (ID: {patient.id})
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          {!fhirServerOnline && !loadingPatients && (
            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center gap-2 text-yellow-800">
                <AlertTriangle className="h-5 w-5" />
                <span className="font-medium">FHIR Server Offline</span>
              </div>
              <p className="text-sm text-yellow-700 mt-1">
                Manual entry required. Patient selection unavailable.
              </p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="patientId" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Patient ID
                </Label>
                <Input
                  id="patientId"
                  name="patientId"
                  value={form.patientId}
                  onChange={handleChange}
                  placeholder="Enter patient ID (e.g., patient-001)"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="name" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Full Name
                </Label>
                <Input
                  id="name"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  placeholder="Enter patient's full name"
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="bloodType" className="flex items-center gap-2">
                <Droplet className="h-4 w-4" />
                Blood Type
              </Label>
              <Input
                id="bloodType"
                name="bloodType"
                value={form.bloodType}
                onChange={handleChange}
                placeholder="e.g., A+, B-, O+, AB-"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="allergies" className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Allergies
              </Label>
              <Input
                id="allergies"
                name="allergies"
                value={form.allergies}
                onChange={handleChange}
                placeholder="List any known allergies (e.g., Penicillin, Shellfish)"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="emergencyContact" className="flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Emergency Contact
              </Label>
              <Input
                id="emergencyContact"
                name="emergencyContact"
                value={form.emergencyContact}
                onChange={handleChange}
                placeholder="Emergency contact number (e.g., +91-98765-43210)"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="chronicConditions" className="flex items-center gap-2">
                <Heart className="h-4 w-4" />
                Chronic Conditions
              </Label>
              <Input
                id="chronicConditions"
                name="chronicConditions"
                value={form.chronicConditions}
                onChange={handleChange}
                placeholder="List any chronic conditions (e.g., Diabetes, Hypertension)"
              />
            </div>

            <div className="flex gap-3">
              <Button type="submit" disabled={loading} className="flex-1">
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Writing to Card...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    Write to Card
                  </>
                )}
              </Button>
              <Button type="button" variant="outline" onClick={handleClear}>
                Clear Form
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {status && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-center p-4 rounded-lg bg-muted">
              <p className="text-sm font-medium">{status}</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default CardWriter;
