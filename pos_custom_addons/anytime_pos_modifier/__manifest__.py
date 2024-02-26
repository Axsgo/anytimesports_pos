# -*- coding: utf-8 -*-
{
    "name": "Anytime Sports POS Modifier",
    "description": "POS Customization for Anytime Sports",
    "summary": "POS Customization for Anytime Sports",
    "version": "1.0",
    "category": "Sales/Point of Sale",
    "author": "AntsyZ/Saravanakumar",
    "website": "https://antsyz.com",
    "license": "AGPL-3",
    "depends": ["point_of_sale", "acc_stock"],
    "data": [
        "views/assets.xml",
        "views/product_view.xml",
        "views/pos_config_view.xml",
    ],
    'qweb': [
        'static/src/xml/Chrome.xml',
        'static/src/xml/pos_ticket_view.xml',
    ],
    "installable": True,
    "application": True,
}
