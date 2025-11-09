# VeriFy – Blockchain-Powered Certificate Verification System

VeriFy is a decentralized platform for secure certificate and document verification. It uses **Ethereum smart contracts**, **OCR (PyTesseract)**, **QR code verification**, and an **AI-assisted validation layer** to provide fast, reliable, and fraud-proof verification for academic, professional, and institutional documents.

---

##  Features

###  On-Chain Certificate Storage
Certificate hashes are stored on the Ethereum blockchain, ensuring immutability and tamper-proof verification.

###  OCR-Based Certificate Scanning
PyTesseract extracts key details from uploaded documents for automated verification.

###  QR Code Verification
Each certificate generates a unique QR code linked to its on-chain verification result.

###  Agentic AI Validation Layer
AI assists issuers by checking formatting, cleaning OCR data, and validating fields before committing the certificate to the blockchain.

###  Fraud Detection
VeriFy regenerates the hash of an uploaded certificate and compares it with the stored hash. Any mismatch indicates a tampered or forged certificate.

###  Issuer + Verifier Portals
- **Issuer Dashboard:** Upload certificates, manage records, and track blockchain transactions  
- **Verifier Portal:** Upload or scan certificates to instantly check authenticity  

---

##  Tech Stack

### Blockchain
- Ethereum  
- Solidity Smart Contracts  
- Ethers.js / Web3.js  

### Backend
- Node.js / Express  
- Python (OCR + AI pipeline)

### AI + OCR
- PyTesseract  
- Agentic AI for data validation  

### Frontend
- React.js  
- Tailwind / Next.js (optional)

### Additional
- QR Code Generator  
- IPFS (optional)

---

##  How VeriFy Works

### 1. Issuer Registration
Institutions register and receive access to the upload portal.

### 2. Upload Certificate
OCR extracts text and AI verifies formatting/fields.

### 3. Hash Generation
A secure SHA-256 hash is generated from cleaned certificate data.

### 4. Smart Contract Storage
The hash and metadata are recorded on the Ethereum blockchain.

### 5. Verification
Users can:
- Upload the certificate again  
- Scan the QR code  

VeriFy regenerates the hash and compares it with the on-chain record.  
-  Match → **Authentic**  
-  Mismatch → **Tampered / Fake**

---

##  Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/VeriFy.git
cd VeriFy
