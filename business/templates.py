# business/templates.py - Predefined configurations for rapid deployment

"""Collection of business templates for quick project setup."""

BUSINESS_TEMPLATES = {
    "beer_distribution": {
        "meta": {
            "name": "Beer Distribution Network",
            "deployment_type": "collaborative",
            "target_companies": "Multiple breweries, shared distribution",
        },
        "features": {
            "enables_cross_selling": True,
            "enables_shared_inventory": True,
            "enables_shared_clients": True,
            "enables_shared_workforce": True,
            "requires_commission_tracking": True,
        },
        "categories": [
            {
                "name": "Products",
                "icon": "🍺",
                "tracks_inventory": True,
                "enables_cross_selling": True,
                "requires_supplier_info": True,
            },
            {
                "name": "Vehicles",
                "icon": "🚛",
                "requires_scheduling": True,
                "shared_resource": True,
                "tracks_capacity": True,
            },
        ],
        "workflows": [
            "Order Received → Inventory Check → Route Planning → Delivery → Commission Split",
        ],
    }
}

