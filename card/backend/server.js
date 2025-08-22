import express from 'express';
import cors from 'cors';
import { writeToCard } from './writeHandler.js';
import { readFromCard } from './readHandler.js';

const app = express();
app.use(cors());
app.use(express.json());

app.post('/api/write-card', async (req, res) => {
    try {
        const result = await writeToCard(req.body);
        res.json({ message: result });
    } catch (err) {
        res.status(500).json({ error: err.toString() });
    }
});

app.get('/api/read-card', async (req, res) => {
    try {
        const data = await readFromCard();
        res.json({ data });
    } catch (err) {
        res.status(500).json({ error: err.toString() });
    }
});


const PORT = 5000;
app.listen(PORT, () => console.log(`🚀 Backend running on port ${PORT}`));
