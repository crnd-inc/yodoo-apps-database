from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError
from werkzeug.exceptions import NotFound


class YodooAppsWebsite(http.Controller):

    @http.route([
        '/modules',
        '/modules/page/<int:page>',
    ], type='http', auth='public', website=True,
        sitemap=True, readonly=True)
    def modules_list(self, page=1, category=None, serie=None,
                     author=None, search=None, **kwargs):
        Module = request.env['yodoo.module'].sudo()
        domain = [('is_published', '=', True)]

        if category:
            domain.append(('category_id', '=', int(category)))
        if serie:
            domain.append(('serie_ids', 'in', [int(serie)]))
        if author:
            domain.append(('author_ids', 'in', [int(author)]))
        if search:
            domain.extend([
                '|', '|',
                ('name', 'ilike', search),
                ('system_name', 'ilike', search),
                ('summary', 'ilike', search),
            ])

        step = 12
        module_count = Module.search_count(domain)
        pager = request.website.pager(
            url='/modules',
            total=module_count,
            page=page,
            step=step,
            url_args={
                'category': category,
                'serie': serie,
                'author': author,
                'search': search,
            },
        )
        modules = Module.search(
            domain, limit=step, offset=pager['offset'],
            order='name ASC')

        categories = request.env['yodoo.module.category'].sudo().search([])
        series = request.env['yodoo.serie'].sudo().search([])
        authors = request.env['yodoo.module.author'].sudo().search([])

        values = {
            'modules': modules,
            'pager': pager,
            'categories': categories,
            'series': series,
            'authors': authors,
            'current_category': int(category) if category else None,
            'current_serie': int(serie) if serie else None,
            'current_author': int(author) if author else None,
            'search': search or '',
        }
        return request.render(
            'yodoo_apps_website.modules_list', values)

    @http.route([
        '''/modules/<model("yodoo.module"):module>''',
    ], type='http', auth='public', website=True,
        sitemap=True, readonly=True)
    def module_detail(self, module, **kwargs):
        try:
            module = module.sudo()
        except AccessError:
            raise NotFound()

        if not module.is_published and not request.env.user.has_group(
                'website.group_website_designer'):
            raise NotFound()

        values = {
            'module': module,
            'main_object': module,
        }
        return request.render(
            'yodoo_apps_website.module_detail', values)
