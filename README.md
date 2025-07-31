# Marketing Analytics Platform

A web-based marketing analytics platform that replaces an Excel-based reporting system. The platform processes weekly data uploads to track marketing performance, credit applications, and approval rates across different products and campaigns.

## Features

- **Data Upload System**: Upload weekly Excel files for applications, FLG data, and ad spend
- **Credit Performance Report**: Analyze credit applications and approvals by product category
- **Marketing Campaign Report**: Track marketing spend effectiveness and ROI by campaign
- **Status Mapping Management**: Configure how different statuses map to application stages
- **Export Functionality**: Export reports to Excel format
- **Real-time Dashboard**: View key metrics and trends at a glance

## Technology Stack

- **Backend**: Python Flask with SQLAlchemy
- **Database**: PostgreSQL (production) / SQLite (development)
- **Frontend**: Vanilla JavaScript with Chart.js for visualizations
- **CSS Framework**: Tailwind CSS via CDN
- **File Processing**: pandas, openpyxl for Excel files
- **Deployment**: Railway-ready with Procfile

## Project Structure

```
marketing-analytics-platform/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── Procfile                   # Railway deployment
├── runtime.txt                # Python version
├── README.md                  # Project documentation
│
├── models/                    # Database models
│   ├── __init__.py
│   ├── campaign.py
│   ├── product.py
│   ├── application.py
│   ├── flg_data.py
│   ├── ad_spend.py
│   └── status_mapping.py
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
│   └── js/
│       ├── app.js           # Main application
│       ├── upload.js        # File upload handling
│       └── reports.js       # Report display
│
├── templates/                 # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── upload.html
│   ├── credit_performance.html
│   └── marketing_campaign.html
│
└── data/                      # Local data storage
    ├── uploads/              # Temporary file uploads
    └── exports/              # Generated reports
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/marketing-analytics-platform.git
cd marketing-analytics-platform
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
flask init-db
flask seed-test-data  # Optional: add test data
```

6. Run the application:
```bash
flask run
```

The application will be available at `http://localhost:5000`

## Usage

### Uploading Data

1. Navigate to the "Upload Data" page
2. Upload the three weekly Excel files:
   - **Applications Data**: Affordability check results (passed/failed)
   - **FLG Full Data**: Lead information with sale values and status
   - **Ad Spend Data**: Campaign and ad level spending

### Viewing Reports

1. **Credit Performance Report**:
   - Shows metrics by product including approval rates and credit issued
   - Filter by date range and product category
   - Export to Excel format

2. **Marketing Campaign Report**:
   - Displays ROI metrics, cost per acquisition, and status breakdowns
   - Filter by date range, campaign, and ad level
   - Visual charts for funnel analysis and ROI

### Managing Status Mappings

1. Click "Status Mappings" in the navigation
2. Configure how each status maps to application stages:
   - Application Received
   - Application Processed
   - Application Approved
   - Future

## Data File Formats

### Applications Data (Excel)
- Sheet: "Affordability data - passed"
- Sheet: "Affordability data - failed"
- Columns: DateTime, Status, User, Lead ID, LeadDateTime, LeadName, etc.

### FLG Full Data (Excel)
- Sheet: "ALL"
- Columns: Reference, ReceivedDateTime, Status, MarketingSource, Data5, Data6, etc.

### Ad Spend Data (Excel)
- Columns: Reporting End Date, Meta Campaign Name, Ad Level, Spend Amount

## API Endpoints

- `POST /api/upload/applications` - Upload applications data
- `POST /api/upload/flg-data` - Upload FLG data
- `POST /api/upload/ad-spend` - Upload ad spend data
- `GET /api/reports/credit-performance` - Get credit performance report
- `GET /api/reports/marketing-campaign` - Get marketing campaign report
- `GET /api/mappings/status` - Get status mappings
- `POST /api/mappings/status` - Create status mapping

## Deployment

### Railway Deployment

1. Push code to GitHub
2. Connect Railway to your GitHub repository
3. Set environment variables in Railway:
   - `DATABASE_URL` (automatically provided by Railway PostgreSQL)
   - `SECRET_KEY` (generate a secure secret key)
   - `FLASK_ENV=production`

4. Deploy will start automatically

### Environment Variables

- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: PostgreSQL connection string
- `FLASK_ENV`: Environment (development/production)
- `FLASK_DEBUG`: Debug mode (True/False)

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
flake8
```

### Database Migrations
If you need to modify the database schema:
```bash
flask db init
flask db migrate -m "Description of changes"
flask db upgrade
```

## Troubleshooting

### Common Issues

1. **File upload fails**: Check file format matches expected Excel structure
2. **Reports show no data**: Ensure data has been uploaded for the selected date range
3. **Database connection errors**: Verify DATABASE_URL is correctly set

### Logs

Check application logs for detailed error messages:
```bash
tail -f logs/app.log  # If logging to file
heroku logs --tail   # If deployed on Heroku
railway logs         # If deployed on Railway
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@example.com or create an issue in the GitHub repository.