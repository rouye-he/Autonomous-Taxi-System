# Autonomous Taxi System

## Project Overview

This project is a comprehensive autonomous taxi operation management system, consisting of two core platforms:

1. **Autonomous Taxi Booking Platform** (User-side WeChat Mini Program) - Provides convenient taxi booking services for passengers
2. **Autonomous Taxi Management Platform** (Backend Management System) - Provides comprehensive vehicle, order, and financial management functions for operations personnel (**Deployment URL**: http://112.124.2.50)

The system adopts a front-end and back-end separation architecture, with Flask framework for the backend, HTML, CSS, JavaScript, and Bootstrap 5 for the frontend, and MySQL database, implementing intelligent order allocation, real-time vehicle monitoring, user credit management, financial analysis, and other core functions.

---

## I. Autonomous Taxi Management Platform (Backend Management System)

### Platform Overview

The Autonomous Taxi Management Platform is a backend management system for operations personnel, providing comprehensive operational management functions including vehicle management, order management, user management, financial management, and data analysis. The system adopts modular design, supports multi-city operations, has intelligent order allocation algorithms and real-time monitoring capabilities, and supports Chinese-English language switching.

**Deployment URL**: http://112.124.2.50

### Core Functions

#### 1. System Settings Module

**Function Description:**
Administrators can configure various core parameters for system operation, including vehicle parameters, charging station parameters, order parameters, and city parameters.

**Usage:**

**1.1 Vehicle Parameter Settings**
1. Navigate to "System Settings" → "Vehicle Parameters"
2. **Operating Parameters**: Set vehicle movement speed, battery consumption rate, low battery threshold, passenger waiting time, location update frequency, etc.
3. **Maintenance Parameters**: Configure base maintenance costs and maintenance intervals; the system automatically calculates total maintenance costs based on vehicle type maintenance coefficient and city coefficient
4. **Vehicle Type Pricing**: Set order price coefficients for different vehicle series (Alpha, Nova, Neon, etc.) and specific models
5. **Detailed Vehicle Type Parameters**: Configure speed coefficient, battery capacity coefficient, charging speed coefficient, maintenance cost coefficient, energy consumption coefficient, etc.

**1.2 Charging Station Parameter Settings**
1. Navigate to "System Settings" → "Charging Station Parameters"
2. Set charging rate, battery level update frequency, charging unit price
3. Configure charging station purchase price (base cost + variable cost per parking space)
4. Set dispatch parameters (check interval, maximum retry attempts, low battery update frequency)

**1.3 Order Parameter Settings**
1. Navigate to "System Settings" → "Order Parameters"
2. Set base fare, price per kilometer, starting distance
3. The system automatically calculates order prices based on these parameters

**1.4 City Parameter Settings**
1. Navigate to "System Settings" → "City Parameters"
2. Select a specific city (Shanghai, Beijing, Guangzhou, Shenzhen, etc.)
3. Configure city map center point coordinates (longitude/latitude)
4. Set map zoom ratio and zoom level
5. Configure city distance conversion ratio (map coordinates to actual kilometers)
6. Set city price coefficient (affects all price calculations for that city)

#### 2. User Management Module

**Function Description:**
Comprehensive management of platform users, including user information management, credit management, data analysis, and review management.

**Usage:**

**2.1 User List Management**
1. Navigate to "User Management" → "User List"
2. View all user basic information (User ID, username, real name, phone number, etc.)
3. Use advanced search to filter users by multiple criteria
4. Available operations: View details, edit, delete users
5. Support pagination browsing and page jumping

**2.2 User Credit Management**
1. Navigate to "User Management" → "Credit Management"
2. **Credit Level Rules**: View and edit credit levels (Very Low/Low/Average/Good/Excellent), set score ranges, benefits, and restrictions for each level
3. **Credit Score Change Rules**: Add/edit/delete credit score change rules, set point addition, deduction, and recovery rules, enable/disable specific rules
4. **Credit Change Records**: Query by user ID, change type, date range; view detailed information for each change; support exporting records

**2.3 User Data Analysis**
1. Navigate to "User Management" → "Data Analysis"
2. View key indicators: Total users, new users this month, user activity rate, 30-day retention rate
3. Analysis charts: User growth trend, registration channel distribution, age/gender/credit score distribution, geographic distribution, tag cloud, usage time distribution, consumption capacity analysis, retention rate analysis
4. Support exporting analysis reports (Excel/PDF format)

**2.4 User Review Management**
1. Navigate to "User Management" → "Review Management"
2. View all user review data
3. Click "View Details" to see detailed review information
4. Support exporting review data

**2.5 Intelligent Customer Service Management**
1. Navigate to "User Management" → "Intelligent Customer Service Management"
2. View customer service session records (classified by user)
3. Click "View Conversation" to see complete conversation history between user and AI
4. View all conversation messages on the "All Session Records" page

#### 3. Vehicle Management Module

**Function Description:**
Manage the full lifecycle of autonomous vehicles, including vehicle information, status monitoring, charging station management, map view, and data analysis.

**Usage:**

**3.1 Vehicle List Management**
1. Navigate to "Vehicle Management" → "Vehicle List"
2. View all vehicle information (Vehicle ID, license plate, model, status, location, battery level, etc.)
3. Use advanced search to filter by city, status, vehicle type, etc.
4. Available operations: View details, edit, delete, vehicle rescue, maintenance management
5. Page header displays vehicle status statistics (Idle/Running/Charging, etc.)

**3.2 Add Vehicle**
1. Click "Add Vehicle" button
2. Fill in vehicle basic information (license plate, VIN, model, etc.)
3. Select operating city and vehicle type
4. System automatically calculates purchase cost (base price × city coefficient)
5. Vehicle is added to system after submission

**3.3 Charging Station Management**
1. Navigate to "Vehicle Management" → "Charging Station List"
2. View all charging station information, support filtering by city
3. Click "Expense Records" to view charging station-related expenses
4. **Add Charging Station**: Click "Add Charging Station", fill in information, system automatically calculates purchase cost

**3.4 Map View**
1. Navigate to "Vehicle Management" → "Map View"
2. **Simulated Map View**: Real-time display of vehicles, charging stations, unassigned order locations; switch by city; filter by landmark type or vehicle status
3. **Amap View**: Refined map based on Amap API, providing more detailed geographic information

**3.5 Vehicle Operation Logs**
1. Navigate to "Vehicle Management" → "Operation Logs"
2. View all vehicle operation history records
3. Support switching between table view and card view
4. Search by vehicle ID/license plate, filter by log type, query by time range

**3.6 Vehicle Data Analysis**
1. Navigate to "Vehicle Management" → "Data Analysis"
2. Analysis content: Vehicle geographic distribution, charging station geographic distribution, order quantity geographic distribution, vehicle type distribution, vehicle review distribution, cumulative distance distribution
3. Trend analysis: Changes in vehicle numbers by city/vehicle type over time, key performance indicator trends

#### 4. Order Management Module

**Function Description:**
Process and monitor the full lifecycle of user orders, including order viewing, vehicle assignment, status tracking, and history management.

**Usage:**

**4.1 Order List Management**
1. Navigate to "Order Management" → "Order List"
2. View all order basic information
3. Page header displays order status statistics (Pending/In Progress/Completed)
4. Use advanced search: Search by order ID, order number, user ID; filter by city, status, location; query by time range
5. Available operations: View details, get real-time information, assign vehicle, edit order, view rating/cancellation reason, delete order

**4.2 Order Assignment**
1. **Manual Assignment**: Click order's "Assign Vehicle" button, view available vehicle list, select appropriate vehicle for assignment
2. **Intelligent Assignment**: Click "One-Click Assignment" to batch assign pending orders from filtered results; click "Auto Assignment" to continuously assign pending orders; system uses Hungarian algorithm for optimal matching

**4.3 Add Test Orders**
1. Click "Add Order" button
2. Select city, set generation quantity
3. Choose whether to update user last login time
4. System batch generates test orders and displays progress

#### 5. Algorithm Testing Module

**Function Description:**
Test and verify core order allocation and vehicle matching algorithms, evaluate algorithm performance.

**Usage:**

**5.1 Algorithm Principle Description**
1. Navigate to "Algorithm Testing" module
2. View advanced intelligent order allocation algorithm description: Algorithm objectives and working principles, key mechanisms and considerations, decision-making process
3. View dynamically loaded algorithm parameters (vehicle type speed, etc.)

**5.2 Order Allocation Algorithm Testing**
1. Enter one or more order IDs (comma-separated) in the "Order Allocation Testing" area
2. Click "Start Test", view processing status and allocation results (JSON format)
3. Analyze allocation process and final results

**5.3 Intelligent Vehicle Matching Algorithm Testing**
1. Select city or enter precise coordinates in the "Vehicle Matching Testing" area
2. Choose whether to enable AI intelligent scoring
3. Click "Start Test", compare matching results with and without intelligent scoring
4. View vehicle information, scores, and matching basis (JSON format)

**5.4 Algorithm Performance Testing**
1. Select test type and set iteration count in the "Performance Testing" area
2. Click "Start Test", view test progress bar
3. Analyze performance metrics: Average/minimum/maximum execution time, standard deviation
4. View detailed test data and time consumption for each iteration

#### 6. Notification Management Module

**Function Description:**
Centrally manage system notifications, vehicle warnings, and other messages to ensure administrators receive critical information promptly.

**Usage:**

**6.1 System Notification Management**
1. Navigate to "Notification Management" → "System Notifications"
2. View notification list (title, content, type, priority, status, time)
3. Page header displays notification statistics (Total/Unread/Read)
4. Use advanced search: Search by title/content keywords; filter by type, priority, status; query by creation time range
5. Available operations: View details, mark as read, delete, batch delete, mark all as read, delete filtered results
6. Page header displays latest important notifications in real-time

**6.2 User Notification Management**
1. Click "User Notification" button
2. Select notification target: Notify all users or notify specific users (support search selection)
3. Fill in notification title and content, send notification

#### 7. Financial Management Module

**Function Description:**
Complete recording, monitoring, analysis, and management of platform income, expenses, and profits.

**Usage:**

**7.1 Financial Dashboard**
1. Navigate to "Financial Management" homepage
2. View core financial indicators: Total income, operating costs, net profit, profit margin, and month-over-month growth
3. Use month selector to switch between different months' data
4. View trend charts: Income trend chart, cost analysis chart, profit trend chart, income source distribution pie chart
5. View geographic distribution: Order quantity geographic distribution, order amount geographic distribution

**7.2 Income Management**
1. Navigate to "Financial Management" → "Income Management"
2. View income record list (table/card view switching)
3. View income type statistics (Total income/Recharge income/Fare income/Other income)
4. Use advanced search: Filter by amount range, income source type, user ID, date range, description keywords
5. Available operations: Add income record, edit income information, delete income record

**7.3 Expense Management**
1. Navigate to "Financial Management" → "Expense Management"
2. View expense record list (table/card view switching)
3. View expense type statistics (Total expenses/Vehicle expenses/Charging station expenses/Other expenses)
4. Use advanced search: Filter by amount range, expense type, associated vehicle ID/charging station ID/user ID, date range, description keywords
5. Available operations: Add expense record, edit expense information, delete expense record

**7.4 Income Analysis**
1. Navigate to "Financial Management" → "Income Analysis"
2. View income overview (Total income, daily average income, year-over-year growth)
3. Analysis charts: Income trend analysis, income source distribution, time period income distribution, payment method distribution, daily income details

**7.5 Expense Analysis**
1. Navigate to "Financial Management" → "Expense Analysis"
2. View expense statistics overview (Total expenses, daily average expenses, year-over-year growth)
3. Analysis charts: Daily expense trend, expense category distribution, vehicle maintenance cost analysis, expense type monthly trend, expense details table

**7.6 Profit Analysis**
1. Navigate to "Financial Management" → "Profit Analysis"
2. Analysis charts: Revenue and expense balance trend analysis (waterfall chart), marginal cost and marginal revenue analysis, profit margin change trend, profit source analysis

**7.7 User Consumption Analysis**
1. Navigate to "Financial Management" → "User Consumption Analysis"
2. Analysis charts: User consumption distribution, payment method analysis, user recharge and consumption correlation analysis (bubble chart), unit mileage revenue analysis (box plot)

#### 8. Coupon Management Module

**Function Description:**
Manage coupon packages, coupon types, and user-held coupons to support marketing activities.

**Usage:**

**8.1 Coupon Package Management**
1. Navigate to "Coupon Management" → "Coupon Packages"
2. View package list (card layout), including package name, description, price, discount, status, number of included coupons, validity period, sales statistics
3. Available operations: Add package, view details, edit package, user purchase
4. Package configuration supports dynamically adding or removing coupon types and quantities

**8.2 Coupon Type Management**
1. Navigate to "Coupon Management" → "Coupon Types"
2. View type list (table format), including coupon type information
3. Available operations: Add type, edit type, delete type
4. Configure detailed coupon parameters (type, face value, usage threshold, etc.)

**8.3 Coupon List Management**
1. Navigate to "Coupon Management" → "Coupon List"
2. View user coupon list (table format)
3. Available operations: Void unused coupons, extend validity period (requires operation confirmation)

#### 9. Dashboard Module

**Function Description:**
System entry point and information overview center, providing real-time overview of key operational data and quick operation entries.

**Usage:**
1. Enter dashboard homepage after login
2. View core data cards: Running vehicle ratio, today's order volume, today's income, today's active users (including year-over-year/month-over-month data, percentage increase/decrease, trend indicators)
3. View key operational charts: Daily average order amount chart (line chart), vehicle utilization chart (line chart), vehicle type financial analysis chart (composite chart)
4. View warning information: Display system, vehicle, order-related warnings; urgent warnings highlighted with special styling

#### 10. Data Analysis Module

**Function Description:**
Provide data support for operational decisions through multi-dimensional data visualization and analysis, presenting operational status, user behavior, and potential issues.

**Usage:**

**10.1 Vehicle Operational Efficiency Analysis**
1. Navigate to "Data Analysis" → "Vehicle Operational Efficiency"
2. View core indicators: Daily revenue per vehicle, vehicle turnover rate, vehicle daily average mileage
3. Analysis charts: Vehicle daily average mileage distribution chart, cumulative completed orders ranking by vehicle type, cumulative mileage ranking by vehicle type

**10.2 Charging and Battery Management Analysis**
1. Navigate to "Data Analysis" → "Charging and Battery Management"
2. View core indicators: Income/charging station expense ratio, vehicle daily average charging frequency
3. Analysis charts: Charging station real-time utilization dashboard, vehicle battery level distribution histogram, charging peak time heatmap, vehicle average battery level geographic distribution map, city charging demand vs. capacity comparison chart

**10.3 Vehicle Maintenance Analysis**
1. Navigate to "Data Analysis" → "Vehicle Maintenance"
2. View core indicators: Vehicle maintenance frequency, vehicle cost ratio
3. Analysis charts: Current maintenance status vehicle proportion chart, upcoming maintenance vehicle remaining time distribution, average remaining time to maintenance by vehicle type chart, average maintenance frequency per vehicle by model chart, vehicle age distribution chart

**10.4 Service Quality Analysis**
1. Navigate to "Data Analysis" → "Service Quality"
2. View core indicators: Order completion rate, average order amount, average order completion time
3. Analysis charts: Average order completion time by city bar chart, order peak time distribution heatmap, order mileage distribution histogram, order amount distribution word cloud, pending order real-time geographic hotspot map

**10.5 User Behavior and Marketing Analysis**
1. Navigate to "Data Analysis" → "User Behavior and Marketing"
2. View core indicators: User repeat usage rate, new user conversion rate, average order amount
3. Analysis charts: User activity conversion funnel chart, coupon issuance to usage conversion Sankey diagram, user tag co-occurrence relationship heatmap, first order time distribution chart, user lifetime value distribution chart, coupon usage preference radar chart, active time comparison chart by registration channel, user repurchase interval time distribution chart

**10.6 Financial and Overall Health Analysis**
1. Navigate to "Data Analysis" → "Financial and Overall Health"
2. View core indicators: Operating profit margin, average vehicle investment return period, fleet average age, system warning rate
3. Analysis charts: Revenue and expense balance dynamic dashboard, cost structure and cash flow Sankey diagram, key financial indicator future trend prediction chart, income contribution radar chart and bubble chart by different cities and user groups

## II. Autonomous Taxi Booking Platform (User-side WeChat Mini Program)

### Platform Overview

The Autonomous Taxi Booking Platform is a mobile application for general users, providing convenient autonomous taxi booking and management services. The platform integrates Tencent Map services and supports operations in 11 cities including Shenyang, Shanghai, Beijing, Guangzhou, and Shenzhen.

### Core Functions

#### 1. User Login and Registration Module

![Authentication](images/Authentication.png)

**Function Description:**

- Supports both password login and verification code login
- Provides complete user registration process with email verification
- Uses NetEase email service to send verification codes, ensuring user information authenticity

**Usage:**

1. First-time users need to click the "Register" button
2. Fill in basic information such as username, password, email, etc.
3. Click "Get Verification Code", the system will send a verification code to the registered email
4. Enter the verification code to complete registration
5. After successful registration, you can log in with username and password, or choose verification code login

#### 2. Homepage Taxi Booking Module

![Home](images/Home.png)

**Function Description:**

- Integrates Tencent Map service, real-time display of vehicle locations and operating areas
- Supports setting start and end points by clicking on the map
- Automatically calculates distance and estimates price
- Real-time display of vehicle movement trajectory

**Usage:**

1. After entering the homepage, the map displays available vehicles in the current city
2. Click on the map to set pickup point (start point)
3. Click on the map again to set drop-off point (end point)
4. System automatically calculates distance and estimates price (considering city coefficient, vehicle type coefficient, etc.)
5. After confirming order information, click "Confirm Order"
6. After successful order assignment, you can view vehicle location in real-time on the map
7. Click "Vehicle Information" button to view detailed vehicle information
8. The vehicle will first go to the start point to pick up passengers, then proceed to the end point for drop-off

#### 3. Personal Information Module

![Profile](images/Profile.png)

**Function Description:**

- View and edit personal basic information
- Change login password
- Manage user tags and preference settings

**Usage:**

1. Click the sidebar button in the upper left corner, select "Personal Information"
2. View current personal information, including avatar, username, real name, contact information, etc.
3. Click "Edit Profile" to modify basic information
4. Click "Change Password" to change login password (requires original password verification)

#### 4. My Orders Module

![Orders](images/Orders.png)

**Function Description:**

- View orders by status (All/Pending/In Progress/Completed/Cancelled)
- Cancel pending orders
- Report abnormalities for in-progress orders
- Rate completed orders

**Usage:**

1. Select "My Orders" in the sidebar
2. Switch between different tabs to view orders in various statuses
3. **Pending Orders**: Click "Cancel Order" to cancel unassigned orders
4. **In Progress Orders**: Click "Report Abnormality" to select abnormality type and fill in description; system will notify administrators for handling
5. **Completed Orders**: Click "Rate" to give 1-5 star rating and write text review
6. View order details to learn about start/end point locations, vehicle information, fee breakdown, payment method, etc.

#### 5. My Reviews Module

![Reviews](images/Reviews.png)

**Function Description:**

- View pending review order list
- View reviewed order history
- Review data used for vehicle service quality statistics

**Usage:**

1. Select "My Reviews" in the sidebar
2. **Pending Reviews**: Display all completed but unreviewed orders; click "Rate" to enter review page
3. **Reviewed**: Display all reviewed orders and review content
4. Each order can only be reviewed once; reviews affect the vehicle's average rating

#### 6. My Wallet Module

![Wallet](images/Wallet.png)

**Function Description:**

- Real-time display of account balance
- View transaction records (Income/Expenses/All records)
- Support recharge and withdrawal operations

**Usage:**

1. Select "My Wallet" in the sidebar
2. Top displays current account balance
3. **Recharge**: Click "Recharge" button, enter amount, select payment method to complete recharge
4. **Withdrawal**: Click "Withdrawal" button, enter amount, select receiving method to complete withdrawal
5. **Income Records**: View refunds, recharges, and other balance increase records
6. **Expense Records**: View fares, coupon purchases, withdrawals, and other expense records
7. **All Records**: View all balance change details

#### 7. My Notifications Module

![Notifications](images/Notifications.png)

**Function Description:**

- Receive various notifications sent by system administrators
- Manage by read/unread status

**Usage:**

1. Select "My Notifications" in the sidebar
2. **Unread Notifications**: Display all unread notifications; click to mark as read
3. **Read Notifications**: Display all read notifications and reading time
4. Notifications include order status updates, promotional activities, system announcements, etc.

#### 8. Coupons Module

![Coupons](images/Coupons.png)

**Function Description:**

- Browse coupon mall to purchase coupon packages
- Manage personal coupons (Unused/Used/Expired)
- Automatically match optimal coupon when placing orders

**Usage:**

1. Select "Coupons" in the sidebar
2. **Coupon Mall**: Browse available coupon packages, view package details, prices, included coupons
3. Click "Purchase" to select payment method (Balance payment/WeChat payment) to complete purchase
4. **Available Coupons**: View usable coupons, including face value, usage conditions, validity period
5. **Used Coupons**: View used coupon history
6. **Expired Coupons**: View expired coupons
7. System automatically matches the most suitable coupon when placing orders

#### 9. My Credit Module

![Credit](images/Credit.png)

**Function Description:**

- Display current credit score and credit level
- View credit level benefits and restrictions
- View credit score change rules and historical records

**Usage:**

1. Select "My Credit" in the sidebar
2. **Credit Level**: View current credit score, level, and corresponding benefits and restrictions
3. **Change Rules**: Understand which behaviors will increase or decrease credit score
4. **Change Records**: View credit score historical changes, including change time, reason, score change

**Credit Score Influencing Factors:**

- Order completion: Increases credit score
- Violations (such as malicious order cancellation): Decreases credit score
- System rewards: Increases credit score
- Periodic recovery: Automatically recovers part of credit score

#### 10. Data Statistics Module

![Statistics](images/Statistics.png)

**Function Description:**

- Multi-dimensional analysis of personal travel data
- Order analysis, consumption analysis, travel habit analysis

**Usage:**

1. Select "Data Statistics" in the sidebar
2. **Order Analysis**: View order status distribution, time trends, daily average orders, etc.
3. **Consumption Analysis**: View fee statistics, payment method distribution, consumption trends
4. **Travel Analysis**: Understand personal travel peak times, frequently used cities, average travel distance, etc.

#### 11. Intelligent Customer Service Module

![Support](images/Support.png)

**Function Description:**

- AI intelligent customer service built on Coze platform
- 7×24 hours online service
- Supports platform business consultation and life assistant functions

**Usage:**

1. Select "Intelligent Customer Service" in the sidebar
2. Enter chat interface, you can see common question shortcut buttons
3. Click shortcut buttons or directly enter questions
4. AI customer service will query knowledge base and provide accurate answers
5. Click "History" to view past conversations
6. Support filtering historical conversation records by date

**Consultable Question Types:**

- Order placement process, billing rules, vehicle type information
- City service coverage, account management
- Coupon usage, other life assistant questions

---

## Technical Architecture

### System Architecture
- **Front-end and Back-end Separation Architecture**: Frontend uses HTML, CSS, JavaScript, and Bootstrap 5; backend uses Flask framework
- **Database**: MySQL relational database with 19 core data tables defined
- **Map Services**: User-side integrates Tencent Maps; management-side supports simulated maps and Amap
- **AI Services**: Intelligent customer service system built on Coze platform

### Core Algorithms
- **Order Allocation Algorithm**: Uses Hungarian algorithm for optimal vehicle-order matching
- **Intelligent Scoring Mechanism**: Comprehensively considers spatial distance, real-time traffic conditions, vehicle battery level, type, performance characteristics, user historical preferences, reviews, regional order density, and other multi-dimensional factors

### Deployment Solution
- **Cloud Service**: Alibaba Cloud Linux server
- **Deployment URL**: http://112.124.2.50/

---

## System Features

1. **Modular Design**: The system is divided into functional modules such as vehicle management, order management, user management, and charging station management. Modules communicate through clear interfaces, reducing coupling

2. **Intelligent Order Allocation**: Uses Hungarian algorithm to achieve globally optimal vehicle-order matching, comprehensively considering distance, battery level, vehicle type, and other factors

3. **Real-time Monitoring**: Uses WebSocket technology for real-time data push; key information such as vehicle location and order status is updated in real-time

4. **User Credit System**: Establishes a comprehensive user credit scoring system with flexible configuration of credit rules for quantitative assessment of user behavior

5. **Multi-dimensional Data Analysis**: Provides data analysis in multiple dimensions including vehicle operational efficiency, charging management, service quality, user behavior, and financial health

6. **AI Intelligent Customer Service**: AI customer service built on Coze platform, 7×24 hours online service, supports platform business consultation

7. **Multi-city Operations**: Supports independent parameter configuration for multiple cities, adapting to different cities' operational characteristics and price levels

8. **Coupon Marketing**: Complete coupon package and type management, supports discount coupons and percentage-off coupons, automatically matches optimal coupon when placing orders

---

**Note**: This system is an academic research project aimed at exploring technical solutions and implementation methods for autonomous taxi operation management.
