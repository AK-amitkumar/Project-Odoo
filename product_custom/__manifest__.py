{
    'name': 'Product Custom',
    'category': 'vuhai',
    'author': 'vuhai',
    'description': 'Add field discount into Product. Create report analysis commission of employee',
    'depends': [
        'sale',
        'point_of_sale',
        'hr_payroll',
        'hr_holidays',
    ],
    'data': [
        'views/product_discount_view.xml',
        'views/pos_order.xml',
        'views/hr_payroll.xml',
        'report/commission_report_view.xml',
        'wizards/financial_report_wizard.xml',
        'report/financial_report.xml',
        'report/pos_reprint.xml',
        'report/report.xml',
    ],
    'installable': True,
}