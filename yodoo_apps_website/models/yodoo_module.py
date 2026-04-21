from odoo import models, fields, api


class YodooModule(models.Model):
    _name = 'yodoo.module'
    _inherit = [
        'yodoo.module',
        'website.published.mixin',
        'website.seo.metadata',
    ]

    yodoo_apps_website_description_html = fields.Html(
        string='Website Description',
        sanitize=False,
        help='HTML content from static/description/index.html',
    )
    yodoo_apps_website_icon = fields.Binary(
        string='Website Icon',
        attachment=True,
        help='Module icon from static/description/icon.png',
    )
    yodoo_apps_website_cover = fields.Binary(
        string='Website Cover',
        attachment=True,
        help='Module cover image from static/description/cover.png',
    )

    @api.depends('system_name')
    def _compute_website_url(self):
        for record in self:
            if record.id and record.system_name:
                record.website_url = '/modules/%s' % record.system_name
            else:
                record.website_url = '#'
