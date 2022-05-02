from odoo import api, SUPERUSER_ID


def migrate(cr, installed_version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['ir.config_parameter'].set_param(
        'yodoo_apps_database.select_last_version_as', 'latest')
