{
    'name': "Yodoo Apps Sale",

    'summary': """Apps Sales""",

    'author': "Center of Research and Development",
    'website': "https://crnd.pro",

    'category': 'Yodoo Apps',
    'version': '12.0.0.0.5',

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
    'installable': True,
    'application': False,
    'license': 'Other proprietary',
    'post_init_hook': '_post_init_hook',
}
