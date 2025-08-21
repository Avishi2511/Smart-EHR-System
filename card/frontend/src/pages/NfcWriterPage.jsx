import React, { useState } from 'react';
import { User, Calendar, Droplet, AlertTriangle, Heart, Save, Loader2 } from 'lucide-react';
import { writeCard } from '../api';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';

export default function NfcWriterPage() {
    const [form, setForm] = useState({
        patientId: '',
        name: '',
        bloodType: '',
        allergies: '',
        emergencyContact: '',
        chronicConditions: ''
    });
    const [status, setStatus] = useState('');
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setStatus('⏳ Waiting for card...');
        try {
            const res = await writeCard(form);
            setStatus(`✅ ${res.message}`);
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
                        <User className="h-6 w-6" />
                        Write Health Info to NFC Card
                    </CardTitle>
                    <CardDescription>
                        Enter patient health information to write to the NFC card
                    </CardDescription>
                </CardHeader>
                <CardContent>
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
                                    placeholder="Enter full name"
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
                                placeholder="List any known allergies"
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
                                placeholder="List any chronic conditions"
                            />
                        </div>

                        <Button type="submit" disabled={loading} className="w-full">
                            {loading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Writing...
                                </>
                            ) : (
                                <>
                                    <Save className="mr-2 h-4 w-4" />
                                    Write to Card
                                </>
                            )}
                        </Button>
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
