# 🏥 Smart-EHR-System  

A hybrid **Smart Card + FHIR-based Electronic Health Record (EHR) system** designed for emergency-first scenarios. It ensures **immediate offline access** to life-saving patient data via NFC smart cards, while providing **enhanced medical records** from a FHIR server when online.  

---

## 🌟 Features  

### 🔑 Emergency-First Design  
- **Offline Priority** → Emergency-critical data always available on the smart card  
- **Online Enhancement** → Full patient records fetched from the FHIR server when available  
- **Progressive Loading** → Card data loads first, then enriched with database data  

### 💳 Smart Card Integration  
- **CardWriter** → Write patient emergency data to NFC cards  
- **CardReader** → Read card instantly and enhance with FHIR records  
- **Hybrid Mode** → Works seamlessly in offline (disaster zones) and online (hospital) scenarios  

### 🩺 FHIR Server (Python + FastAPI)  
- **FHIR R4 compliant** with CRUD operations  
- **SQLite/ PostgreSQL support** for development & production  
- **Resources Supported**: Patient, Condition, Observation, Encounter, MedicationRequest, Procedure, AllergyIntolerance, Immunization  
- **RESTful API** with OpenAPI docs  

### 📊 Frontend (React + TypeScript)  
- Emergency UI → **Red-bordered** emergency card data  
- Enhanced UI → **Blue-bordered** online FHIR records  
- Responsive design → Works on mobile for field use  
- Real-time status indicators (Online/Offline/Card Data)  

---

## 🖼️ System Architecture  

**Flow:**  

```

Smart Card Scan → Immediate Emergency Data → Extract Patient ID →
FHIR Query (if online) → Enhanced Medical Records → Unified Patient Dashboard

```

- **Offline Mode**: Blood type, allergies, emergency contact, chronic conditions  
- **Online Mode**: Full patient history (conditions, medications, lab results, encounters)  

---

## 🗂️ Project Structure  

```

Smart-EHR-System/
├── fhir-server/              # Python FastAPI FHIR backend
│   ├── app/                  # API, models, DB
│   ├── load\_sample\_data.py   # Sample patient data loader
│   ├── test\_server.py        # Testing script
│   └── requirements.txt
├── card/backend/             # Node.js NFC card backend
│   ├── server.js             # Express server
│   ├── writeHandler.js       # Card writing
│   └── readHandler.js        # Card reading
├── src/                      # React + TS frontend
│   ├── pages/CardManagement/ # CardWriter & CardReader UI
│   ├── api/                  # FHIR API integration
│   └── ...
└── README.md                 # Project documentation

````

---

## ⚡ Quick Start (Development)  

### 1. Start the FHIR Server  
```bash
cd fhir-server
pip install -r requirements.txt
python -m app.main
````

Server runs at → **[http://localhost:8000](http://localhost:8000)**

### 2. Load Sample Data

```bash
cd fhir-server
python load_sample_data.py
```

### 3. Start the Card Backend

```bash
cd card/backend
npm install
npm start
```

### 4. Start the React Frontend

```bash
npm install
npm run dev
```

Frontend runs at → **[http://localhost:5173](http://localhost:5173)**

---

## 🧪 Testing

* **Write Test** → Select patient, write to NFC card
* **Read Test** → Scan card, verify immediate emergency display
* **Offline Test** → Disconnect network, card-only mode still works
* **Online Test** → Connect network, enhanced data loads

---

## 🔐 Security

* **Card Security** → Only emergency-critical info stored (no sensitive data like SSNs)
* **Database Security** → Authentication, encryption, audit trails
* **Hybrid Privacy** → Physical card presence required for offline access

---

## 🎉 Conclusion

The **Smart-EHR-System** bridges the gap between **emergency response needs** and **comprehensive medical care**.
With **offline-first smart card access** and **online FHIR integration**, it ensures healthcare providers always have the **right patient information at the right time**, even in disaster or low-connectivity environments.
