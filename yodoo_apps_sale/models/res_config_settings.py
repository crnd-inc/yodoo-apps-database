from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    yodoo_default_product_category_id = fields.Many2one(
        'product.category', readonly=False,
        related="company_id.yodoo_default_product_category_id",
        help="Default product category for modules")
