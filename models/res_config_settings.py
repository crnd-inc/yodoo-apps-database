from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_yodoo_apps_assembly = fields.Boolean(
        "Manage Yodoo Assemblies")
    module_yodoo_apps_sale = fields.Boolean(
        "Sale Yodoo Modules")
