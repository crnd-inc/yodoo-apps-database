{
    'name': "Yodoo Apps Database",

    'summary': """Apps database""",

    'author': "Center of Research & Development",
    'website': "https://crnd.pro",

    'category': 'Yodoo Apps',
    'version': '11.0.0.0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'mail',
        'generic_tag',
    ],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/generic_tag_model.xml',
        'views/menu.xml',
        'views/yodoo_module.xml',
        'views/yodoo_module_serie.xml',
        'views/yodoo_module_version.xml',
        'views/yodoo_module_license.xml',
        'views/yodoo_serie.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'application': False,
    'license': 'Other proprietary',
}
