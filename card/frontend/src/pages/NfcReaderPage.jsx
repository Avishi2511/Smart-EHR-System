import React, { useState } from 'react';
import { readCard } from '../api';
import './NfcForm.css';

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
        <div className="form-container">
            <h2>📖 Read NFC Card</h2>
            <button onClick={handleRead} disabled={loading}>
                {loading ? 'Reading...' : '📥 Read Card'}
            </button>
            {status && <p className="status">{status}</p>}
            
            {data && (
                <div className="card-data">
                    <p><strong>👤 Name:</strong> {data.name}</p>
                    <p><strong>🎂 Age:</strong> {data.age}</p>
                    <p><strong>🩸 Blood Type:</strong> {data.bloodType}</p>
                    <p><strong>🌿 Allergies:</strong> {data.allergies}</p>
                    <p><strong>🏥 Chronic Conditions:</strong> {data.chronicConditions}</p>
                </div>
            )}
        </div>
    );
}
