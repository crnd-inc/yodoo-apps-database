{
    'name': "Yodoo Apps Sale",

    'summary': """Apps Sales""",

    'author': "Center of Research and Development",
    'website': "https://crnd.pro",

    'category': 'Yodoo Apps',
    'version': '13.0.0.2.0',

    # any module necessary for this one to work correctly
    'depends': [
        'sale',
        'yodoo_apps_database',
    ],

    # always loaded
    'data': [
        'data/product_attribute.xml',
        'views/yodoo_module.xml',
        'views/yodoo_module_serie.xml',
        'views/res_config_settings.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'post_init_hook': '_post_init_hook',
}
