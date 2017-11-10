{
    'name': 'Project Shop',
    'category': 'vuhai',
    'author': 'vuhai',
    'description': 'Customize Product',
    'depends': [
        'sale',
        'stock_account',
        # 'users_inherit',
        'point_of_sale',
    ],
    'data': [
        'security/res_group.xml',
        'views/product.xml',
        'views/stock.xml',
        'views/pos.xml',
        'views/web_title.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'qweb':[
        'static/src/xml/base.xml',
        'static/src/xml/web.xml',
        # 'static/src/xml/web_title.xml',
    ],
    # 'css': ['static/src/css/*.css'],
}