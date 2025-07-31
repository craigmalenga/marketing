# PROJECT CONTEXT: Marketing Analytics Platform
# Last Updated: 31 July 2025 at 1900
# Version: 1.5

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

### Product Extraction and Report Fixes (31 July 2025 19:00)
**Problem**: Missing VBA macro functionality, incorrect report calculations, missing data validation
**Solution**: Implemented ProductExtractor service, fixed upload status endpoint, enhanced data processing
**Files Modified**: 
- services/product_extractor.py (NEW - replicates VBA macro)
- routes/upload.py (fixed check-status endpoint structure)
- services/data_processor.py (integrated ProductExtractor, added validation)
**Technical Details**: 
- ProductExtractor replicates Excel VBA macro logic for extracting products/prices
- Added processing state tracking and validation warnings
- Fixed upload status endpoint to return proper nested structure
- Enhanced column mapping for flexible CSV formats
- Added product category determination logic
**Testing Notes**: 
- Upload files in recommended order: mappings → affordability → all_leads → ad spend
- Check for validation warnings in response
- Verify products are extracted from descriptions
- Check upload status endpoint returns proper structure for admin page

### Data Structure Understanding and Upload Fixes (31 July 2025 17:00)
**Problem**: Upload routes returning 404 errors, circular import issues, incorrect understanding of data structure
**Solution**: Fixed circular imports, corrected data processing logic, fixed URL routing
**Files Modified**: 
- app.py (removed URL prefixes from blueprint registration)
- services/__init__.py (removed module-level imports)
- services/data_processor.py (complete rewrite for correct data structure)
- routes/upload.py (complete implementation with proper error handling)
- routes/__init__.py (simplified imports)
- templates/404.html (NEW - error page)
**Technical Details**: 
- Affordability CSV files only provide Lead IDs for pass/fail tracking
- all_leads_all_time.csv is the main data source with all details
- Fixed blueprint registration to avoid double /api/upload prefixes
- DataProcessor now maintains state for Lead ID tracking
- Historic ad spend files handled with flexible column detection
- Lazy imports in services to avoid circular dependencies
**Testing Notes**: 
- Upload files in order: mappings → affordability CSVs → all_leads → ad spend
- Check browser console (F12) for detailed error messages
- Verify routes work at /api/upload/applications (not /api/upload/api/upload/applications)

### CSV Support and Multi-File Upload Implementation (31 July 2025 15:30)
**Problem**: System expected Excel files with specific sheet names, but actual data comes as CSV files with different column names. Ad spend wasn't processing. No feedback on what was being processed.
**Solution**: Added full CSV support, column mapping for actual data formats, multi-file upload interface, and detailed processing feedback
**Files Modified**: 
- services/data_processor.py (major rewrite for CSV support)
- templates/upload.html (new multi-file upload interface)
- routes/upload.py (better feedback and logging)
**Technical Details**: 
- Added CSV file detection and processing alongside Excel
- Column mapping for CSV files:
  - "Activity date & time" → datetime
  - "Capital amount" → lead_value/data5_value
  - "Marketing source" → marketing_source
- Smart file type detection based on filename patterns
- Ad spend processor now tries multiple column name variations
- Added detailed logging for debugging
- Multi-file drag-and-drop upload interface
- Real-time progress tracking for each file
- Better error handling with row-level try/catch
**Testing Notes**: 
- Upload multiple CSV files at once using drag-and-drop
- Check console logs for detailed processing information
- Ad spend should now show column names found and data processed
- Upload history shows file types and processing details

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
   - Application passed/failed data (CSV) - Contains ONLY Lead IDs
   - FLG full data (CSV) - Main data source with all lead details
   - Ad spend data (Excel with flexible column detection)
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
- File Processing: pandas, openpyxl for Excel files, CSV support
- Deployment: Railway with PostgreSQL
- CSS Framework: Tailwind CSS via CDN

## CRITICAL DATA STRUCTURE UNDERSTANDING

### 1. **Affordability Check Files** (CSV) - LEAD IDS ONLY
- `affordability_check_passed__craig_.csv` - Contains ONLY Lead IDs that passed
- `affordability_check_failed__craig_.csv` - Contains ONLY Lead IDs that failed
- **PURPOSE**: Just tells us which applications passed or failed affordability checks
- **DO NOT** try to extract other data from these files

### 2. **All Leads File** (CSV) - MAIN DATA SOURCE
- `all_leads_all_time__craig_.csv` - Contains ALL lead information
- **Columns**:
  - Lead ID (links to affordability results)
  - Date & time received
  - Status
  - Marketing source
  - Capital amount
  - Repayment frequency
  - Total interest
  - Regular repayments
  - Total amount to pay
  - Product details

### 3. **Historic Ad Spend Files** (Excel)
- Multiple files with varying formats and date ranges
- Flexible column detection for: date, campaign, ad level, spend
- May have dates in filename, sheet name, or column

### 4. **FLG to Meta Mapping** (Word)
- Table format with FLG campaign names → Meta campaign names
- May have '?' prefix on some names (should be stripped)

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
│   ├── __init__.py           # Simple exports, no complex imports
│   ├── upload.py             # File upload handling
│   ├── reports.py            # Report generation
│   └── mappings.py           # Status/name mappings
│
├── services/                  # Business logic
│   ├── __init__.py           # NO module-level imports!
│   ├── data_processor.py     # Excel/CSV file processing
│   ├── report_generator.py   # Report calculations
│   ├── mapping_service.py    # Handle mappings
│   └── product_extractor.py  # Extract products from descriptions (NEW)
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
│   ├── upload.html          # Multi-file upload interface
│   ├── credit_performance.html
│   ├── marketing_campaign.html
│   ├── admin.html           # Admin page for DB init
│   └── 404.html             # Error page
│
└── data/                      # Local data storage
    ├── uploads/              # Temporary file uploads
    │   ├── applications/
    │   ├── flg/
    │   ├── ad_spend/
    │   ├── mappings/
    │   └── .gitkeep
    └── exports/              # Generated reports
        └── .gitkeep
```

## KEY FEATURES IMPLEMENTED

### 1. File Upload System ✓
- Multi-file drag-and-drop upload interface
- Accept CSV and Excel files
- Smart file type detection
- Real-time upload progress
- Detailed processing feedback
- Correct data structure handling
- Processing order validation with warnings

### 2. Data Processing Pipeline ✓
- Affordability CSVs → Extract Lead IDs only
- All Leads CSV → Main data with affordability status applied
- Historic ad spend → Flexible column detection
- Row-level error handling
- State management for Lead ID tracking
- Product extraction from descriptions (NEW)
- Flexible column mapping for various CSV formats

### 3. Product Extraction Service ✓ (NEW)
Replicates Excel VBA macro functionality:
- Pattern matching for 25+ product types
- Price extraction from descriptions
- Bundle detection and price distribution
- Handles multiple products in single description
- Category assignment based on product type

### 4. Credit Performance Report ✓
Replicate Excel metrics:
- Number of applications by product
- Average credit value applied
- Combined enquiry credit value
- Pull-through rates
- Processing and approval rates
- Credit issued metrics

### 5. Marketing Campaign Report ✓
Replicate Excel metrics:
- Marketing cost by campaign
- Cost per enquiry/application/approved loan
- Approval rates
- Credit issued totals and averages
- Status breakdown with 1s and 0s

### 6. Filtering System ✓
- Date range selection
- Product category filtering
- Campaign filtering
- Ad level filtering
- Export to Excel functionality

### 7. Status Management ✓
- UI to manage status variants
- Set 1s and 0s for each status
- Add new statuses as they appear
- Initialize default mappings
- 33 default status mappings pre-configured

### 8. Admin Interface ✓
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
5. Upload your data files in correct order

### Correct Data Upload Order
1. **Initialize Database** (/admin)
2. **Upload FLG to Meta Mappings** (Word doc) - RECOMMENDED FIRST
3. **Upload Affordability CSVs** (both passed and failed)
4. **Upload All Leads CSV** (main data file)
5. **Upload Historic Ad Spend** (Excel files)

Note: System will warn if files uploaded out of order but will still process

## CRITICAL IMPLEMENTATION NOTES

### Product Extraction Logic
- ProductExtractor service replicates VBA macro "Populate_product_types_and_prices()"
- Checks specific sofa models before generic "Sofa - other"
- Extracts multiple prices using various patterns
- Handles bundles by distributing total price
- Falls back to "Other" if no products matched

### Circular Import Prevention
- `services/__init__.py` has NO module-level imports
- DataProcessor imported lazily in routes
- Blueprints registered WITHOUT URL prefix (routes already include /api/)
- Model imports happen within app context

### Data Processing Logic
1. **Affordability files** are processed first to build sets of passed/failed Lead IDs
2. **All Leads file** creates both FLG records AND Application records
3. **Application records** only created for Lead IDs found in affordability sets
4. **Marketing sources** mapped to campaigns using FLG to Meta mappings
5. **Products extracted** from descriptions using pattern matching

### Excel Formula Translations
The Excel workbook uses complex formulas that have been translated:
- SUBTOTAL functions → SQL aggregations with filters
- Pivot table logic → Programmatic grouping and aggregation
- Cell references → Database relationships
- Conditional formatting → Frontend styling logic
- VBA macro logic → ProductExtractor service

### Fixed Issues (Chronological)
1. **numpy/pandas compatibility** - Fixed with specific versions
2. **SQLAlchemy datetime** - Using func.now() instead of datetime.utcnow
3. **Import errors** - Removed circular imports
4. **Chart expansion** - Fixed with height containers
5. **Excel parsing** - Matches actual file structure
6. **Database initialization** - Admin page with init button
7. **CSV support** - Full support for CSV files with column mapping
8. **Ad spend detection** - Smart column detection for various formats
9. **Multi-file upload** - Drag-and-drop interface for batch uploads
10. **URL routing** - Removed duplicate prefixes in blueprint registration
11. **Circular imports** - Lazy loading in services and routes
12. **Data structure** - Correct understanding of affordability vs all_leads
13. **Product extraction** - VBA macro functionality replicated
14. **Upload status endpoint** - Fixed structure for admin page
15. **Processing validation** - Added warnings for out-of-order uploads

### Performance Optimization
- Database indexes on frequently queried columns
- Report calculations optimized with SQL
- Connection pooling via SQLAlchemy
- Efficient file parsing with pandas
- Row-level error handling for resilience
- State management in DataProcessor instance

### Security Considerations
- File upload validation
- Secure filenames with timestamps
- SQL injection prevention via SQLAlchemy
- XSS prevention in templates
- CSRF protection via Flask
- 50MB file size limit

## API ENDPOINTS

### Upload Endpoints (Working)
- `POST /api/upload/applications` - Upload applications data (CSV or Excel)
- `POST /api/upload/flg-data` - Upload FLG data (CSV or Excel)
- `POST /api/upload/ad-spend` - Upload ad spend data (Excel)
- `POST /api/upload/flg-meta-mapping` - Upload FLG/Meta mappings (Word/Excel)
- `GET /api/upload/check-status` - Check upload status and history (FIXED)

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
3. **Visit /admin and initialize database** ✓
4. **Upload files in recommended order**:
   - FLG to Meta mappings first (IMPORTANT)
   - Affordability CSVs (both)
   - All leads CSV
   - Historic ad spend files
5. **Verify reports show correct data**

### For Ongoing Use:
1. **Weekly uploads** - Follow the same order as initial setup
2. **Monitor browser console** - F12 for debugging
3. **Check unmapped sources** - Update FLG to Meta mappings as needed
4. **Update status mappings** - Add new statuses as they appear
5. **Review validation warnings** - System will warn about processing order

### Future Enhancements to Consider:
1. **Automated Upload Order** - System could detect and queue files
2. **Data Validation Dashboard** - Show data quality metrics
3. **Enhanced Analytics**:
   - Trend analysis over time
   - Year-over-year comparisons
   - Predictive analytics
4. **Email Reports** - Automated weekly report distribution
5. **API Access** - REST API for external systems
6. **Bulk Historic Import** - Process years of historic data
7. **Audit Trail** - Complete history of all changes
8. **Performance Dashboards** - Real-time KPI monitoring
9. **Multi-product handling** - Full support for multiple products per sale
10. **Advanced price extraction** - Handle more complex pricing scenarios

## TROUBLESHOOTING GUIDE

### Common Issues and Solutions

1. **"Not found" errors on upload**
   - Check browser console for 404 errors
   - Verify URL is `/api/upload/applications` not `/api/upload/api/upload/applications`
   - Restart Flask app completely
   - Check `services/__init__.py` has no imports

2. **"Upload failed" errors**
   - Check browser console (F12) for detailed error
   - Verify file format matches expected structure
   - Ensure upload folders exist in data/uploads/
   - Check file size is under 50MB

3. **"No Lead ID column found"**
   - Ensure CSV has column containing "Lead" and "ID"
   - Check for hidden characters or spaces
   - Verify file encoding is UTF-8

4. **Ad spend showing 0 records**
   - Check console logs for "Found columns:" messages
   - Ensure Excel has recognizable date/campaign/spend columns
   - Try different sheets in the file
   - Check for merged cells or complex formatting

5. **Data not linking correctly**
   - Upload files in correct order
   - Ensure Lead IDs match between files
   - Check FLG to Meta mappings are loaded
   - Verify affordability files uploaded before all_leads

6. **Products showing as "Other"**
   - Check product descriptions contain recognizable keywords
   - Review ProductExtractor patterns in services/product_extractor.py
   - Ensure descriptions aren't empty

7. **Admin page not loading data counts**
   - Check /api/upload/check-status endpoint returns proper structure
   - Verify database connection is working
   - Check browser console for JavaScript errors

### Debugging Commands
```bash
# Check Flask routes
flask routes

# View detailed logs
export FLASK_DEBUG=1
python app.py

# Database queries
flask shell
>>> from models import Application, FLGData
>>> Application.query.count()
>>> FLGData.query.count()

# Check product extraction
>>> from services.product_extractor import ProductExtractor
>>> ProductExtractor.extract_products_and_prices("Sofa - Aldis £1,299.99")
```

### Railway Deployment Checklist
- [x] PostgreSQL database added
- [x] Environment variables set (SECRET_KEY, FLASK_ENV)
- [x] Start command is `gunicorn app:app --bind 0.0.0.0:$PORT`
- [x] Database initialized via /admin
- [x] Upload folders created automatically
- [x] Product extraction service deployed
- [ ] Test file uploads in correct order
- [ ] Verify reports display data correctly

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
6. **AVOID CIRCULAR IMPORTS** - Use lazy imports in functions when needed
7. **INCLUDE NEW SERVICES** - Remember to add ProductExtractor when updating data_processor.py