{
    'name': 'Yodoo Apps Website',

    'summary': 'Display Odoo modules catalog on website',

    'author': 'Center of Research and Development',
    'website': 'https://crnd.pro',

    'category': 'Yodoo Apps',
    'version': '18.0.1.0.0',

    'depends': [
        'website',
        'yodoo_apps_database',
        'yodoo_apps_git_source',
        'kw_html_image2attachment',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/yodoo_module_views.xml',
        'views/templates_list.xml',
        'views/templates_detail.xml',
        'data/website_menu.xml',
    ],

    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
