# Delivery Route Optimizer - Web Application

A beautiful web-based delivery routing system that solves the Traveling Salesperson Problem (TSP) with enhanced address handling and multiple optimization options.

## 🌟 Features

- **Beautiful Web Interface**: Modern, responsive design with Bootstrap
- **Enhanced Address Handling**: Supports exact house numbers and detailed addresses
- **Dual Optimization**: Choose between shortest time or shortest distance
- **Real-time Geocoding**: Accurate address-to-coordinate conversion
- **Interactive Maps**: Visual route display with Folium
- **Mobile Responsive**: Works on all devices

## 🚀 Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python app.py
   ```

3. **Open Browser**: Navigate to `http://localhost:5000`

## 💡 How to Use

1. **Enter Addresses**: Add 2-8 delivery addresses with full details
   - Include house numbers, street names, city, state, zip
   - Example: "123 Main St, New York, NY 10001"

2. **Choose Optimization**: Select between:
   - **Shortest Time**: Minimize travel duration
   - **Shortest Distance**: Minimize total distance

3. **Get Results**: View optimized route with:
   - Step-by-step directions
   - Total time and distance
   - Interactive map visualization

## 🔧 Key Improvements

- **Better Address Recognition**: Handles house numbers and detailed addresses
- **Dual Metrics**: Shows both time (minutes/hours) and distance (km/miles)
- **Enhanced Geocoding**: Fallback mechanisms for better address resolution
- **Professional UI**: Modern gradient design with intuitive controls
- **Real-time Feedback**: Loading states and error handling

## 📱 Responsive Design

- Desktop: Full-featured interface
- Tablet: Optimized layout
- Mobile: Touch-friendly controls

## 🌐 Deployment Ready

The application is ready for deployment on platforms like:
- Heroku
- AWS
- Google Cloud
- DigitalOcean