{
    'name': 'Hethong Nhadat',
    'category': 'vuhai',
    'author': 'vuhai',
    'description': 'Customize Product Category',
    'depends': [
        'sale',
        'website_helpdesk_form',
    ],
    'data': [
        'security/discuss_group.xml',
        'security/ir.model.access.csv',
        'data/auto_cancel_hold_product_data.xml',
        'data/url_bds_data.xml',
        'views/product_category.xml',
        'views/product_product.xml',
        'views/product_notification.xml',
        'views/res_district.xml',
        'views/web_asset.xml',
        'views/helpdesk_ticket.xml',
        'views/helpdesk_templates.xml',
    ],
    'installable': True,
    'css': ['static/src/css/*.css'],
    'qweb':[
        'static/src/xml/web.xml',
    ],
}
