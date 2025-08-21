import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { CreditCard, FileText } from 'lucide-react';
import { Button } from './components/ui/button';
import NfcWriterPage from './pages/NfcWriterPage';
import NfcReaderPage from './pages/NfcReaderPage';

export default function App() {
    return (
        <Router>
            <div className="min-h-screen bg-muted/40">
                <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                    <div className="container flex h-14 items-center">
                        <div className="mr-4 flex">
                            <CreditCard className="mr-2 h-6 w-6" />
                            <span className="font-bold">NFC Health Card</span>
                        </div>
                        <nav className="flex items-center space-x-4 lg:space-x-6">
                            <Link to="/nfc-writer">
                                <Button variant="ghost" className="w-full justify-start">
                                    <FileText className="mr-2 h-4 w-4" />
                                    Write Card
                                </Button>
                            </Link>
                            <Link to="/nfc-reader">
                                <Button variant="ghost" className="w-full justify-start">
                                    <CreditCard className="mr-2 h-4 w-4" />
                                    Read Card
                                </Button>
                            </Link>
                        </nav>
                    </div>
                </header>
                <main className="container mx-auto py-6">
                    <Routes>
                        <Route path="/nfc-writer" element={<NfcWriterPage />} />
                        <Route path="/nfc-reader" element={<NfcReaderPage />} />
                        <Route path="/" element={<NfcWriterPage />} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}
