import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

export const writeCard = (data) => axios.post(`${API_URL}/write-card`, data).then(res => res.data);
export const readCard = () => axios.get(`${API_URL}/read-card`).then(res => res.data);
