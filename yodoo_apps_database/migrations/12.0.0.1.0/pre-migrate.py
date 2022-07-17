from odoo.addons.generic_resource.tools.migration_utils import (
    convert_object_to_resource,
)
from odoo.addons.generic_mixin.tools.migration_utils import ensure_version


@ensure_version('0.1.0')
def migrate(cr, installed_version):
    convert_object_to_resource(
        cr, 'yodoo_apps_database.generic_resource_type_yodoo_module',
        'yodoo.module', 'yodoo_module', visibility='internal')
