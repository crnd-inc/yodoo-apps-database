from odoo.addons.yodoo_apps_database.tools.migration_utils import (
    sync_module_info_data,
)
from odoo.addons.generic_mixin.tools.migration_utils import ensure_version


@ensure_version('0.52.0')
def migrate(cr, installed_version):
    sync_module_info_data(cr)
