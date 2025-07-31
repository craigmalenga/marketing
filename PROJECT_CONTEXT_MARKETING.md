# PROJECT CONTEXT: Marketing Analytics Platform
# Last Updated: 31 July 2025 at 12:27
# Version: 1.1

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

### Technology Stack
- Backend: Python Flask with SQLAlchemy
- Database: PostgreSQL (production) / SQLite (development)
- Frontend: Vanilla JavaScript with Chart.js for visualizations
- File Processing: pandas, openpyxl for Excel files
- Deployment: Railway-ready with Procfile
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
│   └── marketing_campaign.html
│
├── data/                      # Local data storage
│   ├── uploads/              # Temporary file uploads
│   │   └── .gitkeep
│   └── exports/              # Generated reports
│       └── .gitkeep
│
└── tests/                     # Test suite
    ├── __init__.py
    ├── test_data_processor.py
    └── test_reports.py
```

## KEY FEATURES IMPLEMENTED

### 1. File Upload System ✓
- Accept three weekly Excel files
- Accept Word document for FLG/Meta mappings
- Validate file formats and structure
- Show upload status and history

### 2. Data Processing Pipeline ✓
- Parse Excel files using pandas
- Map data to database schema
- Handle status variant mappings
- Update or insert records appropriately

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

## IMPLEMENTATION PHASES

### Phase 1: Core Infrastructure (COMPLETED ✓)
- [x] Project structure setup
- [x] Database schema creation
- [x] Basic Flask application
- [x] File upload endpoints
- [x] Data models

### Phase 2: Data Processing (COMPLETED ✓)
- [x] Excel file parsers
- [x] Data validation
- [x] Database population
- [x] Status mapping logic

### Phase 3: Report Generation (COMPLETED ✓)
- [x] Credit performance calculations
- [x] Marketing campaign calculations
- [x] API endpoints for reports
- [x] Basic report display

### Phase 4: Frontend Development (COMPLETED ✓)
- [x] Upload interface
- [x] Report visualization
- [x] Filtering controls
- [x] Status management UI

### Phase 5: Advanced Features (PARTIALLY COMPLETE)
- [x] Export functionality
- [ ] Historical comparisons
- [ ] Automated weekly processing
- [ ] Email notifications

### Phase 6: Deployment (READY)
- [x] Railway configuration
- [x] Production database setup files
- [x] Environment variables
- [ ] Performance optimization (pending real-world testing)

## CRITICAL IMPLEMENTATION NOTES

### Excel Formula Translations
The Excel workbook uses complex formulas that need translation:
- SUBTOTAL functions → SQL aggregations with filters
- Pivot table logic → Programmatic grouping and aggregation
- Cell references → Database relationships
- Conditional formatting → Frontend styling logic

### Data Processing Considerations
- Date formats vary between files (handle both string and date objects)
- Missing data should be handled gracefully
- Status names may have variations (use fuzzy matching)
- Maintain audit trail of all uploads

### Performance Optimization
- Index database on frequently queried columns
- Cache report calculations
- Paginate large result sets
- Use connection pooling for database

### Security Considerations
- Validate all file uploads
- Sanitize file names
- Implement user authentication (future phase)
- Log all data modifications
- Secure file storage

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

## NEXT STEPS

### Immediate Actions Required:

1. **Save all generated files** to your project directory maintaining the exact folder structure
2. **Create virtual environment and install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Create .env file** from .env.example and set your SECRET_KEY
4. **Initialize the database**:
   ```bash
   flask init-db
   flask seed-test-data
   ```
5. **Run the application**:
   ```bash
   flask run
   ```
6. **Test with your Excel files**:
   - Navigate to http://localhost:5000
   - Go to Upload Data page
   - Upload your three Excel files
   - Check the reports

### Future Enhancements to Consider:

1. **User Authentication**: Add login system to secure the platform
2. **Data Validation**: Add more robust validation for uploaded files
3. **Performance Optimization**: 
   - Add database indexes for large datasets
   - Implement caching for reports
   - Use background jobs for file processing
4. **Enhanced Reporting**:
   - Add trend analysis over time
   - Implement year-over-year comparisons
   - Create PDF export option
5. **Automation**:
   - Schedule automatic report generation
   - Send email alerts for anomalies
   - Auto-import from cloud storage
6. **Data Quality**:
   - Add data quality checks
   - Highlight missing or inconsistent data
   - Provide data reconciliation reports