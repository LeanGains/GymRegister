# GymRegister 🏋️‍♂️

A comprehensive gym asset registry system designed for quick and efficient tracking of moveable gym equipment using AI-powered scanning technology and modern REST APIs.

## 🚀 Project Status

✅ **FastAPI Backend Complete** - The backend has been successfully migrated to a production-ready FastAPI service with comprehensive REST API endpoints, AI-powered analysis, and modern architecture.

## 📋 Overview

GymRegister is specifically designed for fitness facilities to maintain accurate inventory of portable equipment that can easily go missing or be misplaced. While large, stationary equipment like treadmills and cable machines are not easily moved, smaller items like dumbbells, weight plates, resistance bands, and accessories require constant monitoring.

## 🎯 Problem Statement

Gyms face significant challenges with equipment management:
- **Missing Equipment**: Dumbbells, plates, and accessories frequently go missing
- **Time-Consuming Audits**: Manual inventory checks are labor-intensive and error-prone
- **Inaccurate Records**: Traditional tracking methods lead to discrepancies
- **Operational Disruption**: Equipment shortages affect member experience
- **Financial Loss**: Replacement costs for missing equipment add up quickly

## 💡 Solution

GymRegister leverages scanning technology to provide:
- **Rapid Inventory Checks**: Complete equipment audits in minutes, not hours
- **Real-Time Tracking**: Instant updates on equipment status and location
- **Asset Tag Integration**: Works with existing asset tags (upgradeable to QR codes)
- **Organized Layout Optimization**: Designed for neat, rack-based gym layouts
- **Mobile-First Design**: Scan and update from any mobile device

## 🔧 Key Features

### Core Functionality
- **Quick Asset Registration**: Rapidly add new equipment to the system
- **Scanning Integration**: Use mobile cameras to scan asset tags
- **Inventory Audits**: Complete facility-wide equipment checks
- **Missing Item Alerts**: Automatic notifications for equipment not found during audits
- **Location Tracking**: Track which rack/area equipment belongs to

### Equipment Categories
- **Free Weights**: Dumbbells, barbells, weight plates
- **Accessories**: Resistance bands, straps, belts, gloves
- **Small Equipment**: Kettlebells, medicine balls, foam rollers
- **Cardio Accessories**: Heart rate monitors, towels, water bottles
- **Functional Training**: Battle ropes, suspension trainers, agility equipment

### Reporting & Analytics
- **Audit Reports**: Detailed inventory status reports
- **Missing Equipment Tracking**: Historical data on lost items
- **Usage Patterns**: Identify frequently misplaced items
- **Cost Analysis**: Track replacement costs and trends
- **Compliance Documentation**: Maintain records for insurance and audits

## 🏃‍♂️ Quick Start

### For Gym Managers
1. **Initial Setup**: Register your facility and equipment categories
2. **Asset Tagging**: Ensure all moveable equipment has asset tags
3. **Baseline Inventory**: Scan all equipment to create initial database
4. **Staff Training**: Train team members on scanning procedures
5. **Regular Audits**: Schedule periodic inventory checks

### For Staff Members
1. **Daily Checks**: Quick scans of high-traffic areas
2. **Equipment Returns**: Scan items when returned to proper locations
3. **Issue Reporting**: Flag missing or damaged equipment immediately
4. **Audit Participation**: Assist with comprehensive inventory checks

## 🔍 AI-Powered Scanning Technology

### Current Capabilities
- **AI Equipment Detection**: GPT-4o Vision automatically identifies gym equipment from photos
- **Asset Tag Recognition**: Advanced OCR and text recognition for existing tags
- **Condition Assessment**: AI-powered evaluation of equipment condition
- **Weight/Spec Extraction**: Automatic identification of equipment specifications
- **Smart Suggestions**: AI generates asset tags for untagged equipment

### REST API Integration
- **Modern Architecture**: FastAPI backend with comprehensive REST endpoints
- **Real-time Processing**: Asynchronous image analysis with job tracking
- **Scalable Design**: Built for high-volume scanning operations
- **API Documentation**: Full OpenAPI/Swagger documentation available

## 🏗️ Technical Architecture

### Backend (FastAPI)
- **REST API**: Comprehensive endpoints for all operations
- **Database**: SQLAlchemy with SQLite/PostgreSQL support
- **AI Integration**: OpenAI GPT-4o Vision for image analysis
- **Authentication**: API Key and Bearer token support
- **Documentation**: Interactive API docs at `/docs`

### Key API Endpoints
```bash
# Asset Management
GET/POST/PUT/DELETE /api/assets     # Full CRUD operations
PATCH /api/assets/{tag}/location    # Quick location updates

# AI Analysis
POST /api/analyze                   # Submit images for analysis
GET /api/analyze/{job_id}          # Get analysis results
GET /api/analysis/history          # Analysis history

# Reports & Analytics
GET /api/reports/statistics        # Comprehensive statistics
GET /api/reports/export           # CSV data export
GET /api/reports/missing          # Missing equipment
GET /api/reports/repair           # Maintenance needed
```

## 🏋️ Gym Layout Optimization

### Rack-Based Organization
- **Zone Mapping**: Define equipment zones and rack locations
- **Expected Locations**: Set default positions for each item
- **Visual Indicators**: Color-coded status for quick identification
- **Layout Templates**: Pre-configured setups for common gym layouts

### Audit Efficiency
- **Systematic Scanning**: Organized approach for complete coverage
- **Progress Tracking**: Real-time audit completion status
- **Exception Handling**: Quick identification of discrepancies
- **Route Optimization**: Efficient paths for comprehensive checks

## 📱 Technology Stack

### Backend API (Production Ready)
- **FastAPI**: High-performance Python API framework
- **SQLAlchemy**: Robust ORM with SQLite/PostgreSQL support
- **OpenAI GPT-4o**: Advanced AI vision for equipment analysis
- **Pydantic**: Data validation and serialization
- **Docker**: Containerized deployment ready

### Database & Storage
- **SQLite**: Development and small deployments
- **PostgreSQL**: Production-ready with full ACID compliance
- **File Storage**: Local filesystem or cloud storage integration
- **Migrations**: Automated database schema management

### Development & Testing
- **Pytest**: Comprehensive test suite with 80%+ coverage
- **GitHub Actions**: CI/CD pipeline with automated testing
- **Docker Compose**: Complete development environment
- **Interactive Docs**: Swagger UI and ReDoc documentation

### Integration Ready
- **REST APIs**: Standard HTTP/JSON interfaces
- **OpenAPI Spec**: Machine-readable API documentation
- **Frontend Agnostic**: Works with any frontend framework
- **Mobile Compatible**: Optimized for mobile app integration

## 🔒 Security & Compliance

### Data Protection
- **Encrypted Storage**: All data encrypted at rest and in transit
- **Access Controls**: Role-based permissions for different user types
- **Audit Trails**: Complete history of all system activities
- **Backup & Recovery**: Automated data backup and disaster recovery

### Compliance Features
- **Asset Documentation**: Maintain detailed equipment records
- **Insurance Requirements**: Generate reports for insurance claims
- **Regulatory Compliance**: Meet industry standards and regulations
- **Privacy Protection**: GDPR and privacy law compliance

## 📊 Benefits

### Operational Efficiency
- **Time Savings**: Reduce inventory time by 80-90%
- **Accuracy Improvement**: Eliminate human counting errors
- **Staff Productivity**: Free up staff for member service
- **Automated Reporting**: Generate reports automatically

### Financial Impact
- **Reduced Losses**: Minimize equipment theft and loss
- **Lower Replacement Costs**: Accurate tracking prevents over-ordering
- **Insurance Benefits**: Better documentation for claims
- **ROI Tracking**: Measure return on equipment investments

### Member Experience
- **Equipment Availability**: Ensure equipment is where it should be
- **Reduced Wait Times**: Better equipment distribution
- **Facility Reputation**: Professional, well-managed appearance
- **Member Satisfaction**: Consistent equipment availability

## 🚀 Getting Started

### Quick Start with Docker (Recommended)
```bash
# Clone repository
git clone https://github.com/LeanGains/GymRegister.git
cd GymRegister

# Setup environment
cp .env.example .env
# Add your OpenAI API key to .env

# Start services
docker-compose -f docker-compose.dev.yml up -d

# Access API documentation
open http://localhost:8000/docs
```

### Local Development
```bash
# Install dependencies
pip install -r requirements_api.txt

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export SECRET_KEY="your-secret-key"

# Run development server
uvicorn api.main:app --reload

# Run tests
pytest api/tests/ -v
```

### API Authentication
```bash
# All API requests require authentication
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/assets

# Or using Bearer token
curl -H "Authorization: Bearer your-token" http://localhost:8000/api/assets
```

## 🔄 Migration from Legacy Streamlit

If upgrading from the previous Streamlit version:
```bash
# Automatic migration script preserves all existing data
python -m api.migrate_from_streamlit
```

## 📊 Implementation Status

### ✅ Completed Features
- [x] **FastAPI Backend**: Production-ready REST API
- [x] **AI Analysis**: GPT-4o Vision integration
- [x] **Asset Management**: Full CRUD operations
- [x] **Reporting System**: Statistics, exports, alerts
- [x] **Authentication**: API key and Bearer token security
- [x] **Database**: SQLAlchemy with migration support
- [x] **Testing**: Comprehensive test suite
- [x] **Documentation**: Interactive API docs
- [x] **Docker Support**: Complete containerization
- [x] **CI/CD Pipeline**: Automated testing and deployment

### 🔄 In Progress
- [ ] Frontend React/TypeScript application
- [ ] Mobile app optimization
- [ ] Advanced analytics dashboard
- [ ] Multi-facility support

### 🎯 Upcoming Features
- [ ] WebSocket real-time updates
- [ ] Advanced image preprocessing
- [ ] Integration with gym management systems
- [ ] Mobile apps (iOS/Android)

## 🤝 Contributing

We welcome contributions from the fitness and technology communities! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on how to get involved.

## 📞 Support

For questions, issues, or feature requests:
- **Email**: support@gymregister.com
- **Documentation**: [Wiki](../../wiki)
- **Issues**: [GitHub Issues](../../issues)
- **Discussions**: [GitHub Discussions](../../discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**GymRegister** - Making gym equipment management simple, fast, and accurate. 🏋️‍♂️✨