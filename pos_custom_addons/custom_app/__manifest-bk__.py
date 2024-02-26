# -*- coding: utf-8 -*-
{
    'name': "Custom App",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Galaxy Weblinks Ltd",
    'website': "https://www.galaxyweblinks.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '1.0',
    # any module necessary for this one to work correctly
    'depends': ['website', 'website_sale'],

    # always loaded
    'data': [
        'views/header.xml',
        'views/footer.xml',
        'views/assets.xml',
        'views/homepage.xml',
        'views/contact.xml',
        'views/about-us.xml',
        'views/subscribe.xml',
        'views/products.xml',
        'views/product_view.xml',
        'views/shop.xml',
        'views/testimonials.xml',
        'views/mycart.xml',
        'views/snippets/custom_snippets.xml',
        'views/snippets/shop_banner.xml',
        'views/snippets/snippets.xml',
        'views/snippets/s_cart_products.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable':True,
    'auto_install': False,
}
