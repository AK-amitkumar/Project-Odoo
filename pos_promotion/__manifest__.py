{
    'name': "POS Promotions",
    'version': '3.0',
    'category': 'Point of Sale',
    'author': 'TL Technology',
    'sequence': 0,
    'summary': 'POS Promotions',
    'description': 'POS Promotions',
    'depends': ['pos_base'],
    'data': [
        'security/ir.model.access.csv',
        'data/product_data.xml',
        '__import__/template.xml',
        'view/pos_promotion.xml',
        'view/pos_config.xml',
        'view/pos_order.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'price': '100',
    'website': 'http://posodoo.com',
    'application': True,
    'images': ['static/description/icon.png'],
    'support': 'thanhchatvn@gmail.com',
    "currency": 'EUR',
}
