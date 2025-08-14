import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import NfcWriterPage from './pages/NfcWriterPage';
import NfcReaderPage from './pages/NfcReaderPage';

export default function App() {
    return (
        <Router>
            <nav>
                <Link to="/nfc-writer">Write Card</Link> | 
                <Link to="/nfc-reader">Read Card</Link>
            </nav>
            <Routes>
                <Route path="/nfc-writer" element={<NfcWriterPage />} />
                <Route path="/nfc-reader" element={<NfcReaderPage />} />
            </Routes>
        </Router>
    );
}
