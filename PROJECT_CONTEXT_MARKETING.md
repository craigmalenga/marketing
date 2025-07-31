# PROJECT CONTEXT: Marketing Analytics Platform
# Last Updated: 31 July 2025 at 1409
# Version: 1.2

## 🔄 DOCUMENT MAINTENANCE INSTRUCTIONS - READ FIRST

### After EVERY significant code change or session:
1. **UPDATE THIS DOCUMENT** - Add details of what was changed and why
2. **INCREMENT VERSION** - Update version number and date at top
3. **PROVIDE UPDATED FILE** - Use artifacts to generate the complete updated PROJECT_CONTEXT_MARKETING.md
4. **INSTRUCT USER** - Tell user to save the updated version to repository

### Update Template:
```
### [Feature/Fix Name] (Date)
**Problem**: [What wasn't working]
**Solution**: [What was implemented]
**Files Modified**: [List all files changed]
**Technical Details**: [Key code changes]
**Testing Notes**: [How to verify it works]
```

## UPDATE HISTORY

### Complete Implementation of Core System (31 July 2025 12:27)
**Problem**: System stopped partway through implementation
**Solution**: Completed all core components of the marketing analytics platform
**Files Created**: 
- All model files (campaign.py, product.py, status_mapping.py, application.py, flg_data.py, ad_spend.py, flg_meta_mapping.py)
- All route files (upload.py, reports.py, mappings.py)
- All service files (data_processor.py, report_generator.py, mapping_service.py)
- All template files (base.html, index.html, upload.html, credit_performance.html, marketing_campaign.html)
- All JavaScript files (app.js, upload.js, reports.js)
- CSS file (main.css)
- Configuration files (requirements.txt, Procfile, runtime.txt, .env.example, .gitignore)
- Documentation (README.md)
**Technical Details**: 
- Implemented complete data models based on Excel analysis
- Created file upload system for all three data types plus Word doc mapping
- Built report generation services matching Excel formulas
- Developed frontend with real-time charts and filtering
- Added status mapping management UI
- Fixed circular import issues in app.py
**Testing Notes**: 
- Run `flask init-db` to initialize database with default status mappings
- Run `flask seed-test-data` to add test products
- Upload sample Excel files to test data processing
- Check both reports display correctly with filtering

### Railway Deployment Fixes and Database Initialization (31 July 2025 12:45)
**Problem**: Multiple deployment issues - numpy/pandas compatibility, SQLAlchemy datetime errors, import errors, database not initialized, Excel parsing failures, expanding charts
**Solution**: Fixed all deployment issues and added proper database initialization system
**Files Modified**: 
- requirements.txt (fixed numpy/pandas versions, updated python-docx)
- All model files (changed datetime.utcnow to func.now())
- app.py (fixed imports, added /admin route, added /api/init-database endpoint, updated upload history to use real data)
- services/__init__.py (removed MappingService from imports)
- services/data_processor.py (fixed ad spend parsing to match actual Excel structure)
- templates/index.html (fixed expanding charts)
- templates/marketing_campaign.html (fixed expanding charts)
- templates/admin.html (NEW - admin page for database initialization)
- railway.json (simplified configuration)
- Removed nixpacks.toml
**Technical Details**: 
- Fixed numpy 1.24.3 with pandas 2.0.3 compatibility
- Changed all SQLAlchemy datetime defaults from datetime.utcnow to func.now()
- Ad spend parser now looks for "Meta" sheet and correct column names
- Charts now use fixed height containers
- Added admin interface for database initialization
- Upload history now shows real data from database
**Testing Notes**: 
- After deployment, go to /admin and click "Initialize Database"
- Upload Excel files: they should parse without errors
- Charts should not expand infinitely
- Data persists between sessions

## ASSISTANT ROLE & EXPERTISE
You are an experienced programmer with 30+ years of Excel and VBA expertise, now converting a complex Excel-based marketing analytics platform to a modern web application. You have extensive experience with:
- Complex Excel formulas and pivot tables
- VBA automation and macros
- Python/Flask backend development
- JavaScript frontend development with data visualization
- SQL database design and optimization
- Data processing pipelines
- Marketing analytics and reporting
- Railway deployment

## 🚀 SESSION START PROTOCOL

### When starting a new session:
1. **FIRST WORDS**: "I'm reviewing the PROJECT_CONTEXT_MARKETING.md to understand the current system state..."
2. **ACKNOWLEDGE VERSION**: State the version and last update date you're reading
3. **CONFIRM UNDERSTANDING**: Briefly summarize the latest changes documented
4. **ASK FOR UPDATES**: "Have there been any changes since [last update date] that I should know about?"
5. **READY CONFIRMATION**: "I'm ready to continue development on the marketing analytics platform. What would you like to work on today?"

## PROJECT OVERVIEW
This is a web-based marketing analytics platform that replaces an Excel-based reporting system. The platform processes weekly data uploads to track marketing performance, credit applications, and approval rates across different products and campaigns.

### Key Business Process
1. Weekly data uploads:
   - Application passed/failed data (affordability checks)
   - FLG full data (lead information, sales values, status)
   - Ad spend data (campaign and ad level spending)
2. FLG to Meta name mapping (from Word document)
3. Status variant mapping (1s and 0s for application stages)
4. Generate two key reports:
   - Credit Performance by Product
   - Marketing Campaign Performance
5. Filtering capabilities by date range, campaign, product, ad level
6. Data persistence - manager can view reports without uploading new data

### Technology Stack
- Backend: Python Flask with SQLAlchemy
- Database: PostgreSQL (production) / SQLite (development)
- Frontend: Vanilla JavaScript with Chart.js for visualizations
- File Processing: pandas, openpyxl for Excel files
- Deployment: Railway with PostgreSQL
- CSS Framework: Tailwind CSS via CDN

## SYSTEM ARCHITECTURE

### Database Schema
```sql
-- Core Tables
campaigns (
    id, name, meta_name, created_at, updated_at
)

products (
    id, name, category, created_at
)

status_mappings (
    id, status_name, is_application_received, 
    is_application_processed, is_application_approved,
    is_future, created_at, updated_at
)

-- Data Tables
applications (
    id, lead_id, datetime, status, user, lead_datetime,
    lead_name, lead_postcode, lead_introducer, lead_partner,
    lead_cost, lead_value, current_status, affordability_result, 
    created_at
)

flg_data (
    id, reference, received_datetime, status, marketing_source,
    data5_value, data6_payment_type, data7_value, data8_value,
    data10_value, data29_product_description, sale_value,
    product_name, campaign_name, created_at
)

ad_spend (
    id, reporting_end_date, meta_campaign_name, ad_level,
    spend_amount, is_new, campaign_id, created_at
)

-- Mapping Tables
flg_meta_mappings (
    id, flg_name, meta_name, created_at
)
```

### File Structure
```
marketing-analytics-platform/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── Procfile                   # Railway deployment
├── runtime.txt                # Python version
├── railway.json               # Railway configuration
├── README.md                  # Project documentation
├── PROJECT_CONTEXT_MARKETING.md # This file
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore file
│
├── models/                    # Database models
│   ├── __init__.py
│   ├── campaign.py
│   ├── product.py
│   ├── application.py
│   ├── flg_data.py
│   ├── ad_spend.py
│   ├── status_mapping.py
│   └── flg_meta_mapping.py
│
├── routes/                    # API endpoints
│   ├── __init__.py
│   ├── upload.py             # File upload handling
│   ├── reports.py            # Report generation
│   └── mappings.py           # Status/name mappings
│
├── services/                  # Business logic
│   ├── __init__.py
│   ├── data_processor.py     # Excel file processing
│   ├── report_generator.py   # Report calculations
│   └── mapping_service.py    # Handle mappings
│
├── static/                    # Frontend assets
│   ├── css/
│   │   └── main.css
│   ├── js/
│   │   ├── app.js           # Main application
│   │   ├── upload.js        # File upload handling
│   │   └── reports.js       # Report display
│   └── images/
│
├── templates/                 # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   ├── credit_performance.html
│   ├── marketing_campaign.html
│   └── admin.html           # NEW: Admin page for DB init
│
└── data/                      # Local data storage
    ├── uploads/              # Temporary file uploads
    │   └── .gitkeep
    └── exports/              # Generated reports
        └── .gitkeep
```

## KEY FEATURES IMPLEMENTED

### 1. File Upload System ✓
- Accept three weekly Excel files
- Accept Word document for FLG/Meta mappings
- Validate file formats and structure
- Show upload status and history (real data from DB)
- Handle specific Excel sheet names and column structures

### 2. Data Processing Pipeline ✓
- Parse Excel files using pandas
- Map data to database schema
- Handle status variant mappings
- Update or insert records appropriately
- Persist all data to PostgreSQL

### 3. Credit Performance Report ✓
Replicate Excel metrics:
- Number of applications by product
- Average credit value applied
- Combined enquiry credit value
- Pull-through rates
- Processing and approval rates
- Credit issued metrics

### 4. Marketing Campaign Report ✓
Replicate Excel metrics:
- Marketing cost by campaign
- Cost per enquiry/application/approved loan
- Approval rates
- Credit issued totals and averages
- Status breakdown with 1s and 0s

### 5. Filtering System ✓
- Date range selection
- Product category filtering
- Campaign filtering
- Ad level filtering
- Export to Excel functionality

### 6. Status Management ✓
- UI to manage status variants
- Set 1s and 0s for each status
- Add new statuses as they appear
- Initialize default mappings
- 33 default status mappings pre-configured

### 7. Admin Interface ✓
- Database initialization page at /admin
- One-click database setup
- View database status
- Initialize default data

## DEPLOYMENT CONFIGURATION

### Railway Deployment Settings
- **Build Command**: (leave empty - Railway auto-detects)
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
- **Environment Variables**:
  - `SECRET_KEY`: (generate a secure random key)
  - `FLASK_ENV`: production
  - `DATABASE_URL`: (automatically set by Railway PostgreSQL)

### Database Initialization Process
1. Deploy app to Railway
2. Add PostgreSQL database
3. Visit `https://your-app.railway.app/admin`
4. Click "Initialize Database" button
5. Upload your Excel files

### Excel File Requirements

#### Applications Data (Excel)
- **Filename**: Any .xlsx file
- **Required Sheets**: 
  - "Affordability data - passed"
  - "Affordability data - failed"
- **Columns**: DateTime, Status, User, Lead ID, LeadDateTime, LeadName, LeadPostcode, LeadIntroducer, LeadPartner, LeadCost, LeadValue, CurrentStatus

#### FLG Full Data (Excel)
- **Filename**: Any .xlsx file
- **Required Sheet**: "ALL"
- **Columns**: Reference, ReceivedDateTime, Status, MarketingSource, Data5, Data6, Data7, Data8, Data10, Data29

#### Ad Spend Data (Excel)
- **Filename**: Any .xlsx file
- **Required Sheet**: "Meta"
- **Columns**: Reporting ends, Meta campaign name, Ad level, Spend, New -versus last weel?

## CRITICAL IMPLEMENTATION NOTES

### Excel Formula Translations
The Excel workbook uses complex formulas that have been translated:
- SUBTOTAL functions → SQL aggregations with filters
- Pivot table logic → Programmatic grouping and aggregation
- Cell references → Database relationships
- Conditional formatting → Frontend styling logic

### Data Processing Considerations
- Date formats vary between files (handled for both string and date objects)
- Missing data is handled gracefully
- Status names may have variations (exact matching used)
- All uploads are logged with timestamps
- Data persists between sessions

### Fixed Issues
1. **numpy/pandas compatibility** - Fixed with specific versions
2. **SQLAlchemy datetime** - Using func.now() instead of datetime.utcnow
3. **Import errors** - Removed circular imports
4. **Chart expansion** - Fixed with height containers
5. **Excel parsing** - Matches actual file structure
6. **Database initialization** - Admin page with init button

### Performance Optimization
- Database indexes on frequently queried columns
- Report calculations optimized with SQL
- Connection pooling via SQLAlchemy
- Efficient Excel parsing with pandas

### Security Considerations
- File upload validation
- Secure filenames
- SQL injection prevention via SQLAlchemy
- XSS prevention in templates
- CSRF protection via Flask

## API ENDPOINTS

### Upload Endpoints
- `POST /api/upload/applications` - Upload applications data
- `POST /api/upload/flg-data` - Upload FLG data
- `POST /api/upload/ad-spend` - Upload ad spend data
- `POST /api/upload/flg-meta-mapping` - Upload FLG/Meta mappings
- `GET /api/upload/check-status` - Check upload status

### Report Endpoints
- `GET /api/reports/credit-performance` - Get credit performance report
- `GET /api/reports/marketing-campaign` - Get marketing campaign report
- `POST /api/reports/export/credit-performance` - Export credit report
- `POST /api/reports/export/marketing-campaign` - Export marketing report
- `GET /api/reports/summary` - Get dashboard summary
- `GET /api/reports/available-filters` - Get filter options

### Mapping Endpoints
- `GET /api/mappings/status` - Get all status mappings
- `POST /api/mappings/status` - Create status mapping
- `PUT /api/mappings/status/<id>` - Update status mapping
- `DELETE /api/mappings/status/<id>` - Delete status mapping
- `POST /api/mappings/status/initialize` - Initialize defaults
- `GET /api/mappings/flg-meta` - Get FLG/Meta mappings
- `POST /api/mappings/flg-meta` - Create FLG/Meta mapping

### Admin Endpoints
- `POST /api/init-database` - Initialize database with defaults
- `GET /api/health` - Health check endpoint

## NEXT STEPS

### For Initial Setup:
1. **Deploy to Railway** ✓
2. **Add PostgreSQL database** ✓
3. **Visit /admin and initialize database**
4. **Upload your three Excel files**
5. **Verify reports show correct data**

### For Ongoing Use:
1. **Weekly uploads** - Upload new data files each week
2. **Monitor performance** - Check Railway metrics
3. **Backup database** - Regular PostgreSQL backups
4. **Update mappings** - Add new statuses as they appear

### Future Enhancements to Consider:

1. **User Authentication**: Add login system to secure the platform
2. **Automated Uploads**: Schedule automatic file imports
3. **Enhanced Analytics**:
   - Trend analysis over time
   - Year-over-year comparisons
   - Predictive analytics
4. **Email Reports**: Automated weekly report distribution
5. **API Access**: REST API for external systems
6. **Data Validation**: More robust file validation
7. **Audit Trail**: Complete history of all changes
8. **Performance Dashboards**: Real-time KPI monitoring

## TROUBLESHOOTING GUIDE

### Common Issues and Solutions

1. **"No tables in database"**
   - Visit /admin and click Initialize Database
   - Or use DBeaver with Railway PostgreSQL credentials

2. **"Excel file has wrong format"**
   - Check sheet names match exactly (case-sensitive)
   - Ensure required columns are present
   - Ad spend must have "Meta" sheet

3. **"Charts expanding infinitely"**
   - Deploy the latest code with chart fixes
   - Clear browser cache

4. **"All values show zero"**
   - Upload data files first
   - Check database initialization completed
   - Verify date filters aren't excluding all data

5. **"Import errors on deployment"**
   - Check requirements.txt has correct versions
   - Ensure all files are committed to git

### Railway Deployment Checklist
- [ ] PostgreSQL database added
- [ ] Environment variables set (SECRET_KEY, FLASK_ENV)
- [ ] Start command is `gunicorn app:app --bind 0.0.0.0:$PORT`
- [ ] Database initialized via /admin
- [ ] Test file uploads work
- [ ] Reports display data correctly

## CODE GENERATION INSTRUCTIONS

### 🚨 CRITICAL INSTRUCTION - READ FIRST 🚨
**PLEASE GIVE ME THE FULL CODE - THIS IS IMPORTANT**
- Provide FULL FILES for each code you make changes to
- NO PLACEHOLDERS, NO ELLIPSIS, NO "rest remains the same"
- Full code with no loss of functionality
- Only replace or add as per requirements, preserve everything else
- Response in code area to right (artifacts system), not in chat below
- Focus on fully functional and exact code that will work first time
- If modifying even one line in a 1000-line file, provide all 1000 lines

### MANDATORY CODE GENERATION RULES:
1. **NEVER USE PLACEHOLDERS** - Every single line of code must be included
2. **COMPLETE FILES ONLY** - If modifying line 500 of a 1000-line file, provide all 1000 lines
3. **USE ARTIFACTS SYSTEM** - Code goes in the right panel, not in chat responses
4. **NO SNIPPETS** - Even for single-line changes, provide the entire file
5. **PRESERVE EVERYTHING** - Every comment, every blank line, every import