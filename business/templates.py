# business/templates.py - Predefined configurations for rapid deployment
"""Collection of business templates for quick project setup."""

BUSINESS_TEMPLATES = {
    'low_voltage': {
        'name': 'Low Voltage Installation',
        'categories': [
            {'name': 'Devices', 'icon': '📱', 'color': '#28a745'},
            {'name': 'Hardware', 'icon': '🔧', 'color': '#dc3545'},
            {'name': 'Software', 'icon': '💻', 'color': '#007bff'},
            {'name': 'License', 'icon': '📜', 'color': '#ffc107'},
            {'name': 'Travel', 'icon': '🚗', 'color': '#6c757d'},
        ]
    },
    'yard_cleaning': {
        'name': 'Yard Cleaning Service',
        'categories': [
            {'name': 'Equipment', 'icon': '🚜', 'color': '#28a745'},
            {'name': 'Materials', 'icon': '🗑️', 'color': '#dc3545'},
            {'name': 'Supplies', 'icon': '🧹', 'color': '#007bff'},
            {'name': 'Permits', 'icon': '📋', 'color': '#ffc107'},
            {'name': 'Travel', 'icon': '🚗', 'color': '#6c757d'},
        ]
    },
    'beer_distribution': {
        'name': 'Beer Distribution',
        'categories': [
            {'name': 'Products', 'icon': '🍺', 'color': '#28a745'},
            {'name': 'Inventory', 'icon': '📦', 'color': '#dc3545'},
            {'name': 'Licenses', 'icon': '📜', 'color': '#007bff'},
            {'name': 'Vehicles', 'icon': '🚛', 'color': '#ffc107'},
            {'name': 'Travel', 'icon': '🚗', 'color': '#6c757d'},
        ]
    },
    'handyman': {
        'name': 'Handyman Service',
        'categories': [
            {'name': 'Tools', 'icon': '🛠️', 'color': '#28a745'},
            {'name': 'Materials', 'icon': '🧰', 'color': '#dc3545'},
            {'name': 'Permits', 'icon': '📋', 'color': '#007bff'},
            {'name': 'Labor', 'icon': '💪', 'color': '#ffc107'},
            {'name': 'Travel', 'icon': '🚗', 'color': '#6c757d'},
        ]
    },
    'tshirt_printing': {
        'name': 'T-Shirt Printing',
        'categories': [
            {'name': 'Equipment', 'icon': '👕', 'color': '#28a745'},
            {'name': 'Materials', 'icon': '🎨', 'color': '#dc3545'},
            {'name': 'Designs', 'icon': '🖌️', 'color': '#007bff'},
            {'name': 'Licenses', 'icon': '📜', 'color': '#ffc107'},
            {'name': 'Travel', 'icon': '🚗', 'color': '#6c757d'},
        ]
    }
}
