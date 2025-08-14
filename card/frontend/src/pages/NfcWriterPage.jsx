import React, { useState } from 'react';
import { writeCard } from '../api';
import './NfcForm.css'; // custom styles

export default function NfcWriterPage() {
    const [form, setForm] = useState({
        name: '',
        age: '',
        bloodType: '',
        allergies: '',
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
        <div className="form-container">
            <h2>📝 Write Health Info to NFC Card</h2>
            <form onSubmit={handleSubmit} className="card-form">
                <label>Full Name</label>
                <input name="name" value={form.name} onChange={handleChange} required />

                <label>Age</label>
                <input name="age" type="number" value={form.age} onChange={handleChange} required />

                <label>Blood Type</label>
                <input name="bloodType" value={form.bloodType} onChange={handleChange} required />

                <label>Allergies</label>
                <input name="allergies" value={form.allergies} onChange={handleChange} />

                <label>Chronic Conditions</label>
                <input name="chronicConditions" value={form.chronicConditions} onChange={handleChange} />

                <button type="submit" disabled={loading}>
                    {loading ? 'Writing...' : '💾 Write to Card'}
                </button>
            </form>
            {status && <p className="status">{status}</p>}
        </div>
    );
}

