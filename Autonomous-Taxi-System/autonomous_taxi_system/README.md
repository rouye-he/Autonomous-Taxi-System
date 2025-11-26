# Autonomous Taxi Management Platform

A comprehensive web-based management system for autonomous taxi fleet operations, built with Flask and MySQL.

## Tech Stack

- **Backend**: Python 3.8+, Flask 2.3.3
- **Database**: MySQL 8.0
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Data Visualization**: Chart.js

## Core Features

### Intelligent Order Allocation
The system implements a Hungarian algorithm-based order dispatch system that optimizes vehicle-to-order matching for minimal wait times.

**Key capabilities:**
- Global optimization using the Hungarian algorithm
- Batch processing support for multiple orders
- Automatic fallback to greedy algorithm when needed
- Multi-city parallel processing
- Graceful task interruption

### Analytics Dashboard
Real-time monitoring and analysis of key business metrics:
- Average order value trends
- Charging station utilization rates
- Revenue per kilometer analysis
- Coupon conversion tracking
- User activity and retention metrics

### Notification System
Unified message notification framework with:
- Success, error, warning, and info message types
- Auto-dismiss after 5 seconds (pause on hover)
- Consistent styling across all pages
- Standardized API for message handling

### Financial Management
Streamlined payment processing:
- Account balance-based payments
- Direct deduction on order completion
- Automated income recording for top-ups
- Simplified payment flow

## Project Structure

```
app/
├── admin/              # Admin modules (blueprints)
│   ├── dashboard.py    # Dashboard analytics
│   ├── users.py        # User management
│   ├── vehicles.py     # Vehicle management
│   ├── orders.py       # Order management
│   ├── finance.py      # Financial operations
│   ├── analytics.py    # Data analytics
│   ├── algorithm.py    # Algorithm testing
│   └── notifications.py # Notification management
├── api/                # RESTful API
│   └── v1/             # API version 1
├── config/             # Configuration
│   ├── database.py     # Database settings
│   └── vehicle_params.py # Vehicle parameters
├── dao/                # Data Access Objects
├── models/             # Database models
├── static/             # Static assets
│   ├── css/
│   ├── js/
│   └── images/
├── templates/          # HTML templates
└── utils/              # Utility functions
```

## Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure database settings in `.env`

5. Run the application:
```bash
python run.py
```

## Algorithm Details

The order allocation algorithm follows these steps:

1. **Preprocessing**: Group orders by city
2. **Resource Check**: Verify available vehicles per city
3. **Cost Matrix**: Calculate ETA for all vehicle-order pairs
4. **Optimization**: Apply Hungarian algorithm for global optimum
5. **Execution**: Update order and vehicle states

## License

MIT License
