import React, { useState } from 'react';
import { User, Calendar, Droplet, AlertTriangle, Heart, CreditCard, Loader2 } from 'lucide-react';
import { readCard } from '../api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';

export default function NfcReaderPage() {
    const [data, setData] = useState(null);
    const [status, setStatus] = useState('');
    const [loading, setLoading] = useState(false);

    const handleRead = async () => {
        setLoading(true);
        setStatus('⏳ Waiting for card...');
        try {
            const res = await readCard();
            setData(res.data);
            setStatus('✅ Card data loaded');
        } catch (err) {
            setStatus(`❌ ${err.response?.data?.error || err.message}`);
        }
        setLoading(false);
    };

    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <CreditCard className="h-6 w-6" />
                        Read NFC Card
                    </CardTitle>
                    <CardDescription>
                        Tap your NFC card to read the stored health information
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <Button onClick={handleRead} disabled={loading} className="w-full" size="lg">
                        {loading ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Reading...
                            </>
                        ) : (
                            <>
                                <CreditCard className="mr-2 h-4 w-4" />
                                Read Card
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
            
            {data && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <User className="h-5 w-5" />
                            Patient Information
                        </CardTitle>
                        <CardDescription>
                            Health information retrieved from NFC card
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                                <User className="h-5 w-5 text-blue-600" />
                                <div>
                                    <p className="text-sm font-medium text-muted-foreground">Name</p>
                                    <p className="font-semibold">{data.name}</p>
                                </div>
                            </div>
                            
                            <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                                <Calendar className="h-5 w-5 text-green-600" />
                                <div>
                                    <p className="text-sm font-medium text-muted-foreground">Age</p>
                                    <p className="font-semibold">{data.age} years</p>
                                </div>
                            </div>
                            
                            <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                                <Droplet className="h-5 w-5 text-red-600" />
                                <div>
                                    <p className="text-sm font-medium text-muted-foreground">Blood Type</p>
                                    <p className="font-semibold">{data.bloodType}</p>
                                </div>
                            </div>
                            
                            <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                                <AlertTriangle className="h-5 w-5 text-orange-600" />
                                <div>
                                    <p className="text-sm font-medium text-muted-foreground">Allergies</p>
                                    <p className="font-semibold">{data.allergies || 'None reported'}</p>
                                </div>
                            </div>
                            
                            <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                                <Heart className="h-5 w-5 text-purple-600" />
                                <div>
                                    <p className="text-sm font-medium text-muted-foreground">Chronic Conditions</p>
                                    <p className="font-semibold">{data.chronicConditions || 'None reported'}</p>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
