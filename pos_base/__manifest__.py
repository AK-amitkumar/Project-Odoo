{
    'name': "POS Base",
    'version': '1.0',
    'category': 'Point of Sale',
    'author': 'TL Technology',
    'sequence': 0,
    'summary': 'POS Base',
    'description': 'This is base pos addons of Bruce Nguyen',
    'depends': ['point_of_sale'],
    'data': [
        '__import__.xml',
        'view/pos_config.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'price': '0',
    'website': 'http://posodoo.com',
    'application': True,
    'images': ['static/description/icon.png'],
    'support': 'thanhchatvn@gmail.com',
    'auto_install': False,
}
