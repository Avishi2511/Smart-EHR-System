import axios from 'axios';

const CARD_API_URL = 'http://localhost:5000/api';

export interface CardData {
  patientId: string;
  name: string;
  bloodType: string;
  allergies: string;
  emergencyContact: string;
  chronicConditions: string;
}

export const readCardData = async (): Promise<{ data: CardData }> => {
  try {
    const response = await axios.get(`${CARD_API_URL}/read-card`);
    return response.data;
  } catch (error) {
    console.error('Error reading card:', error);
    throw error;
  }
};

export const writeCardData = async (data: CardData): Promise<{ message: string }> => {
  try {
    const response = await axios.post(`${CARD_API_URL}/write-card`, data);
    return response.data;
  } catch (error) {
    console.error('Error writing card:', error);
    throw error;
  }
};

export const checkCardReaderStatus = async (): Promise<boolean> => {
  try {
    // Simple health check to see if card backend is running
    await axios.get(`${CARD_API_URL}/read-card`);
    return true;
  } catch (error) {
    return false;
  }
};
