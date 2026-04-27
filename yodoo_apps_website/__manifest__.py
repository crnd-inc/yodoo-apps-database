{
    'name': 'Yodoo Apps Website',

    'summary': 'Display Odoo modules catalog on website',

    'author': 'Center of Research and Development',
    'website': 'https://crnd.pro',

    'category': 'Yodoo Apps',
    'version': '18.0.1.5.3',

    'depends': [
        'website',
        'yodoo_apps_database',
        'yodoo_apps_git_source',
        'kw_html_image2attachment',
        'generic_task_queue',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/yodoo_module_views.xml',
        'views/yodoo_module_category_views.xml',
        'views/yodoo_module_author_views.xml',
        'views/yodoo_git_source_views.xml',
        'views/templates_list.xml',
        'views/templates_detail.xml',
        'data/website_menu.xml',
        'data/image_task.xml',
    ],

    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
