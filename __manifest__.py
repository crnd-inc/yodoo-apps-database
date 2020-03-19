{
    'name': "Yodoo Apps Database",

    'summary': """Apps database""",

    'author': "Center of Research and Development",
    'website': "https://crnd.pro",

    'category': 'Yodoo Apps',
    'version': '12.0.0.12.4',

    # any module necessary for this one to work correctly
    'depends': [
        'mail',
        'generic_tag',
        'base_field_m2m_view',
        'generic_resource',
    ],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/generic_tag_model.xml',
        'data/ir_cron.xml',
        'data/yodoo_serie.xml',
        'views/menu.xml',
        'views/yodoo_module.xml',
        'views/yodoo_module_serie.xml',
        'views/yodoo_module_version.xml',
        'views/yodoo_module_license.xml',
        'views/yodoo_module_category.xml',
        'views/yodoo_module_author.xml',
        'views/yodoo_serie.xml',
        'views/res_config_settings.xml',
        'data/generic_resource_type.xml',
        'data/yodoo.module.csv',
        'data/yodoo.module.serie.csv',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'application': True,
    'license': 'Other proprietary',
}
