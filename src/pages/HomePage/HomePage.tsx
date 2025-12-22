import { useState, useContext, useEffect } from 'react';
import { CreditCard, Loader2, Heart, AlertTriangle } from 'lucide-react';
import { readCardData } from '@/api/cardApi';
import { fetchPatientDataFromFhir, checkFhirServerStatus } from '@/api/fhirPatientApi';
import { PatientContext } from '@/contexts/PatientContext';
import { useSession } from '@/contexts/SessionContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import useLauncherQuery from '@/hooks/useLauncherQuery';

function HomePage() {
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);

  const { setSelectedPatient } = useContext(PatientContext);
  const { login, isAuthenticated } = useSession();
  const navigate = useNavigate();
  const { setQuery } = useLauncherQuery();

  // Redirect to main app if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/app/dashboard');
    }
  }, [isAuthenticated, navigate]);

  const handleScanCard = async () => {
    setLoading(true);
    setStatus('⏳ Waiting for card...');

    try {
      // Step 1: Read card data
      const res = await readCardData();
      setStatus('✅ Card data loaded successfully');

      // Step 2: Check if FHIR server is online
      const serverOnline = await checkFhirServerStatus();

      if (serverOnline && res.data.patientId) {
        // Step 3: Fetch patient data and navigate to dashboard
        try {
          const fhirRes = await fetchPatientDataFromFhir(res.data.patientId);

          if (fhirRes.patient) {
            // Set patient in context and update launch parameters
            setSelectedPatient(fhirRes.patient);
            setQuery({ patient: fhirRes.patient.id });

            // Login to session and navigate to main application
            login();
            navigate('/app/dashboard');
          }
        } catch (fhirErr: any) {
          console.error('FHIR fetch error:', fhirErr);
          setStatus('❌ Patient not found in database');
        }
      } else if (!serverOnline) {
        setStatus('❌ Database offline - Cannot load patient dashboard');
      } else {
        setStatus('❌ No patient ID found on card');
      }
    } catch (err: any) {
      setStatus(`❌ ${err.response?.data?.error || err.message}`);
    }

    setLoading(false);
  };

  // TEMPORARY BYPASS: Direct access without smart card (for development only)
  const handleBypassLogin = async (patientId: string) => {
    setLoading(true);
    setStatus(`⏳ Loading patient ${patientId}...`);

    try {
      // Check if FHIR server is online
      const serverOnline = await checkFhirServerStatus();

      if (!serverOnline) {
        setStatus('❌ Database offline - Cannot load patient dashboard');
        setLoading(false);
        return;
      }

      // Fetch patient data directly
      const fhirRes = await fetchPatientDataFromFhir(patientId);

      if (fhirRes.patient) {
        setStatus('✅ Patient data loaded successfully');

        // Set patient in context and update launch parameters
        setSelectedPatient(fhirRes.patient);
        setQuery({ patient: fhirRes.patient.id });

        // Login to session and navigate to main application
        login();
        navigate('/app/dashboard');
      } else {
        setStatus('❌ Patient not found in database');
      }
    } catch (err: any) {
      console.error('Bypass login error:', err);
      setStatus(`❌ ${err.response?.data?.error || err.message || 'Failed to load patient data'}`);
    }

    setLoading(false);
  };

  return (
    <main className="flex-1 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Main Card Scanning Interface */}
        <Card className="text-center">
          <CardHeader className="pb-4">
            <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <CreditCard className="h-8 w-8 text-blue-600" />
            </div>
            <CardTitle className="text-2xl font-semibold">Smart EHR System</CardTitle>
            <CardDescription className="text-base">
              Scan your emergency card to access patient records
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <Button
              onClick={handleScanCard}
              disabled={loading}
              className="w-full h-14 text-lg"
              size="lg"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Scanning Card...
                </>
              ) : (
                <>
                  <CreditCard className="mr-2 h-5 w-5" />
                  Scan the Card
                </>
              )}
            </Button>

            {/* TEMPORARY BYPASS BUTTON - FOR DEVELOPMENT ONLY */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                  Development Only
                </span>
              </div>
            </div>

            <Button
              onClick={() => handleBypassLogin('patient-002')}
              disabled={loading}
              variant="outline"
              className="w-full h-12 text-base border-amber-300 bg-amber-50 hover:bg-amber-100 text-amber-900"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <AlertTriangle className="mr-2 h-5 w-5" />
                  DEV: Quick Access Patient 002 (Priya Sharma)
                </>
              )}
            </Button>

            {status && (
              <div className="p-4 rounded-lg bg-muted">
                <p className="text-sm font-medium">{status}</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Emergency Information Card */}
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-orange-600 mt-0.5" />
              <div className="text-sm">
                <p className="font-medium text-orange-800 mb-1">Emergency Access</p>
                <p className="text-orange-700">
                  This system provides immediate access to critical patient information for emergency medical situations.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* System Info */}
        <div className="text-center text-sm text-muted-foreground">
          <div className="flex items-center justify-center gap-2">
            <Heart className="h-4 w-4" />
            <span>Secure • FHIR Compliant • Emergency Ready</span>
          </div>
        </div>
      </div>
    </main>
  );
}

export default HomePage;
