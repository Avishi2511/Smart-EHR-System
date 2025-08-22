import React, { useState, useContext } from 'react';
import { User, Calendar, Droplet, AlertTriangle, Heart, CreditCard, Loader2, Database, Wifi, WifiOff, ArrowRight } from 'lucide-react';
import { readCardData, CardData } from '@/api/cardApi';
import { fetchPatientDataFromFhir, FhirPatientData, checkFhirServerStatus } from '@/api/fhirPatientApi';
import { PatientContext } from '@/contexts/PatientContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useNavigate } from 'react-router-dom';
import useLauncherQuery from '@/hooks/useLauncherQuery';

function CardReader() {
  const [cardData, setCardData] = useState<CardData | null>(null);
  const [fhirData, setFhirData] = useState<FhirPatientData | null>(null);
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [fhirLoading, setFhirLoading] = useState(false);
  const [isOnline, setIsOnline] = useState(false);
  
  const { setSelectedPatient } = useContext(PatientContext);
  const navigate = useNavigate();
  const { setQuery } = useLauncherQuery();

  const handleRead = async () => {
    setLoading(true);
    setStatus('⏳ Waiting for card...');
    setFhirData(null);
    
    try {
      // Step 1: Read card data (offline)
      const res = await readCardData();
      setCardData(res.data);
      setStatus('✅ Card data loaded successfully');
      
      // Step 2: Check if FHIR server is online
      const serverOnline = await checkFhirServerStatus();
      setIsOnline(serverOnline);
      
      if (serverOnline && res.data.patientId) {
        // Step 3: Fetch additional FHIR data (online)
        setFhirLoading(true);
        try {
          const fhirRes = await fetchPatientDataFromFhir(res.data.patientId);
          setFhirData(fhirRes);
          
          // Step 4: Set patient in context and update launch parameters
          if (fhirRes.patient) {
            setSelectedPatient(fhirRes.patient);
            // Update launch parameters to prevent override by PatientNavProfile
            setQuery({ patient: fhirRes.patient.id });
          }
          
          setStatus('✅ Card data loaded + Enhanced with database records');
        } catch (fhirErr: any) {
          console.error('FHIR fetch error:', fhirErr);
          setStatus('✅ Card data loaded (Database unavailable)');
        }
        setFhirLoading(false);
      } else if (!serverOnline) {
        setStatus('✅ Card data loaded (Offline mode - Database unavailable)');
      }
    } catch (err: any) {
      setStatus(`❌ ${err.response?.data?.error || err.message}`);
      setCardData(null);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CreditCard className="h-6 w-6" />
            Read NFC Card
          </CardTitle>
          <CardDescription>
            Tap your NFC card to read the stored health information for emergency access
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={handleRead} disabled={loading} className="w-full" size="lg">
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Reading Card...
              </>
            ) : (
              <>
                <CreditCard className="mr-2 h-4 w-4" />
                Scan Card
              </>
            )}
          </Button>
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
      
      {cardData && (
        <>
          {/* Emergency Card Data (Always Available Offline) */}
          <Card className="border-red-200 bg-red-50">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-5 w-5 text-red-600" />
                  Emergency Patient Information
                </div>
                <Badge variant="destructive">
                  <CreditCard className="h-3 w-3 mr-1" />
                  Card Data
                </Badge>
              </CardTitle>
              <CardDescription>
                Critical health information from NFC card - Always available offline
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center gap-3 p-3 rounded-lg bg-white/50">
                  <User className="h-5 w-5 text-blue-600" />
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Patient Name</p>
                    <p className="font-semibold">{cardData.name}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 p-3 rounded-lg bg-white/50">
                  <Droplet className="h-5 w-5 text-red-600" />
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Blood Type</p>
                    <p className="font-semibold">{cardData.bloodType}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 p-3 rounded-lg bg-white/50">
                  <AlertTriangle className="h-5 w-5 text-orange-600" />
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Allergies</p>
                    <p className="font-semibold">{cardData.allergies || 'None reported'}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 p-3 rounded-lg bg-white/50">
                  <Calendar className="h-5 w-5 text-green-600" />
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Emergency Contact</p>
                    <p className="font-semibold">{cardData.emergencyContact}</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-3 p-3 rounded-lg bg-white/50 md:col-span-2">
                  <Heart className="h-5 w-5 text-purple-600" />
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Chronic Conditions</p>
                    <p className="font-semibold">{cardData.chronicConditions || 'None reported'}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* FHIR Database Data (When Online) */}
          {isOnline && (
            <Card className="border-blue-200 bg-blue-50">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="h-5 w-5 text-blue-600" />
                    Enhanced Medical Records
                  </div>
                  <div className="flex gap-2">
                    <Badge variant="secondary">
                      <Wifi className="h-3 w-3 mr-1" />
                      Online
                    </Badge>
                    {fhirLoading && (
                      <Badge variant="outline">
                        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        Loading...
                      </Badge>
                    )}
                  </div>
                </CardTitle>
                <CardDescription>
                  Additional medical information from hospital database
                </CardDescription>
              </CardHeader>
              <CardContent>
                {fhirData ? (
                  <div className="space-y-4">
                    {fhirData.conditions.length > 0 && (
                      <div className="p-3 rounded-lg bg-white/50">
                        <h4 className="font-medium text-sm text-muted-foreground mb-2">Active Conditions</h4>
                        <div className="space-y-1">
                          {fhirData.conditions.slice(0, 3).map((condition, index) => (
                            <p key={index} className="text-sm">{condition.code?.text}</p>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {fhirData.medications.length > 0 && (
                      <div className="p-3 rounded-lg bg-white/50">
                        <h4 className="font-medium text-sm text-muted-foreground mb-2">Current Medications</h4>
                        <div className="space-y-1">
                          {fhirData.medications.slice(0, 3).map((med, index) => (
                            <p key={index} className="text-sm">{med.medicationCodeableConcept?.text}</p>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {fhirData.observations.length > 0 && (
                      <div className="p-3 rounded-lg bg-white/50">
                        <h4 className="font-medium text-sm text-muted-foreground mb-2">Recent Observations</h4>
                        <div className="space-y-1">
                          {fhirData.observations.slice(0, 3).map((obs, index) => (
                            <p key={index} className="text-sm">
                              {obs.code?.text}: {obs.valueQuantity?.value} {obs.valueQuantity?.unit}
                            </p>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : fhirLoading ? (
                  <div className="flex items-center justify-center p-8">
                    <Loader2 className="h-6 w-6 animate-spin mr-2" />
                    <span>Loading database records...</span>
                  </div>
                ) : (
                  <div className="text-center p-8 text-muted-foreground">
                    <Database className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p>No additional records found in database</p>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {!isOnline && (
            <Card className="border-orange-200 bg-orange-50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-center p-4 rounded-lg bg-white/50">
                  <WifiOff className="h-5 w-5 mr-2 text-orange-600" />
                  <p className="text-sm font-medium text-orange-800">
                    Database offline - Showing emergency card data only
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Navigation to Patient Dashboard */}
          {fhirData && fhirData.patient && (
            <Card className="border-green-200 bg-green-50">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between p-4 rounded-lg bg-white/50">
                  <div className="flex items-center gap-3">
                    <Database className="h-5 w-5 text-green-600" />
                    <div>
                      <p className="font-medium text-green-800">Patient Loaded Successfully</p>
                      <p className="text-sm text-green-700">
                        {fhirData.patient.name?.[0] 
                          ? `${fhirData.patient.name[0].given?.join(' ') || ''} ${fhirData.patient.name[0].family || ''}`.trim()
                          : 'Unknown Patient'} is now selected
                      </p>
                    </div>
                  </div>
                  <Button 
                    onClick={() => navigate(`/patient-summary?patient=${fhirData.patient.id}`)} 
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <ArrowRight className="mr-2 h-4 w-4" />
                    View Patient Dashboard
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

export default CardReader;
