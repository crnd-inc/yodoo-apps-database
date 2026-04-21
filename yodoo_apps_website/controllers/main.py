from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request


class YodooAppsWebsite(http.Controller):

    def _modules_listing_domain(self):
        return [
            ('is_published', '=', True),
            '|', ('category_id', '=', False),
            '&', ('category_id.is_published', '=', True),
                 ('category_id.is_listed_on_website', '=', True),
            '|', ('author_ids', '=', False),
            '&', ('author_ids.is_published', '=', True),
                 ('author_ids.is_listed_on_website', '=', True),
        ]

    def _module_is_hidden_hard(self, module):
        if not module.is_published:
            return True
        if module.category_id and not module.category_id.is_published:
            return True
        if module.author_ids and not any(
                a.is_published for a in module.author_ids):
            return True
        return False

    @http.route([
        '/modules',
        '/modules/page/<int:page>',
    ], type='http', auth='public', website=True,
        sitemap=True, readonly=True)
    def modules_list(self, page=1, category=None, serie=None,
                     author=None, search=None, **kwargs):
        Module = request.env['yodoo.module'].sudo()
        domain = self._modules_listing_domain()

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

        listed_domain = [
            ('is_published', '=', True),
            ('is_listed_on_website', '=', True),
        ]
        categories = request.env[
            'yodoo.module.category'].sudo().search(listed_domain)
        series = request.env['yodoo.serie'].sudo().search([])
        authors = request.env[
            'yodoo.module.author'].sudo().search(listed_domain)

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
        '/modules/<string:system_name>',
    ], type='http', auth='public', website=True,
        sitemap=True, readonly=True)
    def module_detail(self, system_name, **kwargs):
        module = request.env['yodoo.module'].sudo().search(
            [('system_name', '=', system_name)], limit=1)
        if not module:
            raise NotFound()

        is_designer = request.env.user.has_group(
            'website.group_website_designer')
        if self._module_is_hidden_hard(module) and not is_designer:
            raise NotFound()

        values = {
            'module': module,
            'main_object': module,
        }
        return request.render(
            'yodoo_apps_website.module_detail', values)
