# GymRegister API Migration Guide

## Overview

This document outlines the migration from Streamlit to React frontend with FastAPI backend support.

## Architecture Changes

### Before (Streamlit)
- Single `app.py` file with UI and logic
- SQLite database with direct access
- Session state management
- Streamlit components for UI

### After (React + FastAPI)
- **Frontend**: React TypeScript application
- **Backend**: FastAPI REST API server
- **Database**: SQLite with SQLAlchemy ORM
- **State**: Zustand + React Query

## API Endpoints

### Assets Management

```
GET    /api/assets              # Get all assets
GET    /api/assets/{tag}        # Get asset by tag
POST   /api/assets              # Create new asset
PUT    /api/assets/{tag}        # Update asset
DELETE /api/assets/{tag}        # Delete asset
GET    /api/assets/search       # Search assets
```

### AI Analysis

```
POST   /api/analyze             # Analyze image with GPT-4o
GET    /api/analysis/history    # Get analysis history
```

### Reports

```
GET    /api/reports/statistics  # Get asset statistics
GET    /api/reports/audit-logs  # Get audit logs
GET    /api/reports/export      # Export assets CSV
GET    /api/reports/missing     # Get missing assets
GET    /api/reports/repair      # Get assets needing repair
```

### Health Check

```
GET    /api/health              # API health status
```

## Data Models

### Asset Model
```python
class Asset(BaseModel):
    id: int
    asset_tag: str
    item_type: str
    description: Optional[str]
    location: str
    last_seen: datetime
    status: str  # Active, Missing, Out of Service
    weight: Optional[str]
    condition: str  # Excellent, Good, Fair, Poor, Needs Repair
    notes: Optional[str]
```

### Analysis Result Model
```python
class AnalysisResult(BaseModel):
    asset_tags: List[AssetTag]
    equipment: List[Equipment]
    image_quality: str
    total_items: int
    recommendations: Optional[str]
    error: Optional[str]
```

## Migration Steps

### 1. Backend API Development
- [x] Create FastAPI application structure
- [x] Implement SQLAlchemy models
- [x] Create API endpoints
- [x] Add CORS middleware for React
- [x] Implement AI analysis endpoint
- [x] Add error handling and validation

### 2. Frontend Development
- [x] Create React TypeScript application
- [x] Implement Material-UI components
- [x] Add state management with Zustand
- [x] Create API service layer
- [x] Implement all pages (Scanner, Register, View, Search, Reports)
- [x] Add camera integration
- [x] Implement responsive design

### 3. Integration
- [ ] Connect React frontend to FastAPI backend
- [ ] Test all API endpoints
- [ ] Implement error handling
- [ ] Add loading states
- [ ] Test camera functionality

### 4. Deployment
- [ ] Create Docker configurations
- [ ] Set up CI/CD pipeline
- [ ] Deploy to production environment
- [ ] Configure environment variables

## Key Features Preserved

### From Streamlit App
✅ **AI Equipment Scanner** - GPT-4o image analysis
✅ **Asset Registration** - Manual and AI-assisted
✅ **Asset Management** - View, search, update
✅ **Reports & Analytics** - Statistics and charts
✅ **Camera Integration** - Photo capture
✅ **Database Operations** - SQLite storage
✅ **Audit Logging** - Activity tracking

### Enhanced in React App
🚀 **Better Performance** - Faster loading and interactions
🚀 **Mobile Optimization** - Touch-friendly interface
🚀 **Offline Capability** - PWA features
🚀 **Better UX** - Smooth animations and transitions
🚀 **Type Safety** - TypeScript for better development
🚀 **Scalability** - Modular architecture

## Environment Configuration

### Backend (.env)
```
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=sqlite:///./gym_assets.db
SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000
REACT_APP_APP_NAME=GymRegister
REACT_APP_VERSION=1.0.0
```

## Running the Application

### Development
```bash
# Backend
cd api
pip install -r requirements_api.txt
uvicorn main:app --reload --port 8000

# Frontend
cd ../frontend
npm install
npm start
```

### Production
```bash
# Using Docker Compose
docker-compose up -d
```

## Testing

### Backend Tests
```bash
pytest api/tests/
```

### Frontend Tests
```bash
npm test
```

## Migration Benefits

1. **Separation of Concerns** - Frontend and backend are decoupled
2. **Better Performance** - React is faster than Streamlit for complex UIs
3. **Mobile Support** - Native mobile experience
4. **Scalability** - Can scale frontend and backend independently
5. **Developer Experience** - Better tooling and debugging
6. **Production Ready** - Industry-standard architecture

## Next Steps

1. Complete API implementation
2. Test all endpoints
3. Deploy to staging environment
4. User acceptance testing
5. Production deployment
6. Monitor and optimize performance

---

This migration maintains all existing functionality while providing a modern, scalable architecture for future enhancements.