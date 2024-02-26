# -*- coding: utf-8 -*-
###############################################################################
#
#    Meghsundar Private Limited(<https://www.meghsundar.com>).
#
###############################################################################
{
    'name': 'Show Product Quantity in POS',
    'version': '14.0.1',
    'summary': 'Show Product Quantity in POS',
    'description': 'Show Product Quantity in POS',
    'license': 'AGPL-3',
    'category': 'Point of Sale',
    'author': 'Meghsundar Private Limited',
    'website': 'https://meghsundar.com',
    'depends': ['web', 'point_of_sale', 'stock'],
    'data': [
        'views/assets.xml',
        'views/pos_config_view.xml',
    ],
    'qweb': [
        'static/src/xml/product_qty_show.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/banner.gif'],
}
