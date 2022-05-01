from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_yodoo_apps_assembly = fields.Boolean(
        "Manage Yodoo Assemblies")
    module_yodoo_apps_sale = fields.Boolean(
        "Sale Yodoo Modules")
    module_yodoo_apps_assembly_sale = fields.Boolean(
        "Sale Yodoo Assemblies")

    yodoo_select_last_version_as = fields.Selection(
        [('latest', 'Latest')],
        default='latest',
        required=True,
        config_parameter='yodoo_apps_database.select_last_version_as')
