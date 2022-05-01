from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    yodoo_default_product_category_id = fields.Many2one('product.category')
