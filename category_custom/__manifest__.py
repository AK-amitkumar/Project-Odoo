{
    'name': 'Category Custom',
    'category': 'vuhai',
    'author': 'vuhai',
    'description': 'Customize Product Category',
    'depends': [
        'sale',
    ],
    'data': [
        'data/auto_cancel_hold_product_data.xml',
        'views/product_category.xml',
        'views/product_product.xml',
        'views/res_district.xml',
        'views/web_asset.xml',
    ],
    'installable': True,
    'css': ['static/src/css/*.css'],
}