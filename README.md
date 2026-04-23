# ITVE Integrated Backend

This repository contains two backend services for the **ITVE** project:

- **FastAPI Backend** — Python-based REST API (port `8000`)
- **Node.js Backend** — Express-based Classroom API (port `5000`)

Both services connect to a shared **MongoDB** database (`ITVE_Database`).

---

## Prerequisites

- Python 3.8+
- Node.js v14+
- MongoDB (local on port `27017`, or remote cluster)

---

## 1. FastAPI Backend Setup

```bash
cd fastAPI-backend
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file inside `fastAPI-backend/app/`:

```env
MONGO_URL=mongodb://localhost:27017/
DB_NAME=ITVE_Database
JWT_SECRET_KEY=my-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin credentials
email=mainadmin.itve@gmail.com
password=wadvus-wiqzij-6Pepmo
phone=+921234567890
username=mainadmin.itve1
admin_code=ADMIN2024SECRET
admin_id=65f01234567890abcdef1234

# Cloudinary (for document uploads)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret
```

### Run the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

### Run Tests

```bash
cd fastAPI-backend
python -m pytest tests/ -v
```

---

## 2. Node.js Backend Setup

```bash
cd node-backend
```

### Install Dependencies

```bash
npm install
```

### Configure Environment Variables

Create a `.env` file inside `node-backend/`:

```env
PORT=5000
MONGO_URI=mongodb://localhost:27017/ITVE_Database
JWT_SECRET=my-super-secret-key
```

> ⚠️ `JWT_SECRET` must match the `JWT_SECRET_KEY` in the FastAPI `.env` so tokens are interoperable.

### Run the Server

```bash
npm run dev    # Development (with nodemon)
npm start      # Production
```

- API: `http://localhost:5000`

---

## API Overview

### FastAPI Endpoints (port 8000)

| Route | Tag | Description |
|-------|-----|-------------|
| `/api/v1/auth` | Auth | Login, token refresh |
| `/api/v1/admins` | Admins | Admin signup |
| `/api/v1/students` | Students | Student CRUD |
| `/api/v1/schools` | Schools | School CRUD |
| `/api/v1/promoters` | Promoters | Promoter management |
| `/api/v1/users` | General Users | User operations |
| `/api/v1/workers` | Workers | Worker management |
| `/api/v1/teachers` | Teachers | Teacher account generation |
| `/api/v1/documents` | Worker Documents | CNIC/profile image uploads |
| `/api/v1/main` | Main Entities | Domains, courses |
| `/api/v1/reports` | Student Reports | Student reporting |

### Node.js Endpoints (port 5000)

| Route | Description |
|-------|-------------|
| `POST /api/classrooms/create` | Create classroom (Institution auth) |
| `GET /api/classrooms/validate/:classCode` | Validate class code |
| `POST /api/classrooms/assign` | Assign student to class |
| `GET /api/classrooms/count/:classCode` | Get class student count |
| `GET /api/classrooms/school/total-students` | Get school total students |

---

## Project Structure

```
ITVE_Integrated/
├── fastAPI-backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # All endpoint handlers
│   │   ├── core/                # Config, database, security
│   │   ├── models/              # Pydantic models
│   │   ├── services/            # Business logic
│   │   └── main.py              # App entry point
│   ├── tests/                   # Pytest test suite
│   ├── uploads/                 # File uploads directory
│   └── requirements.txt
├── node-backend/
│   ├── src/
│   │   ├── controllers/         # Classroom controller
│   │   ├── middleware/           # JWT auth middleware
│   │   ├── models/              # Mongoose models
│   │   ├── routes/              # Express routes
│   │   └── config/              # DB connection
│   ├── server.js                # Server entry point
│   └── package.json
└── README.md
```
