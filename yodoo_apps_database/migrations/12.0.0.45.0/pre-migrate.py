from odoo.addons.yodoo_apps_database.tools.migration_utils import (
    sync_module_info_data,
)
from odoo.addons.generic_mixin.tools.migration_utils import ensure_version


@ensure_version('0.45.0')
def migrate(cr, installed_version):
    sync_module_info_data(cr)
    cr.execute("""
        UPDATE yodoo_module_serie
        SET is_odoo_community_addon = False
        WHERE module_id = (
            SELECT id
            FROM yodoo_module
            WHERE system_name = 'website_animate');
        UPDATE yodoo_module
        SET is_odoo_community_addon = False
        WHERE system_name = 'website_animate';
    """)
