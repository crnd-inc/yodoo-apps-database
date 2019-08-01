from odoo.addons.generic_resource.tools.migration_utils import (
    convert_object_to_resource,
)


def migrate(cr, installed_version):
    convert_object_to_resource(
        cr, 'yodoo_apps_database.generic_resource_type_yodoo_module',
        'yodoo.module', 'yodoo_module', visibility='internal')
