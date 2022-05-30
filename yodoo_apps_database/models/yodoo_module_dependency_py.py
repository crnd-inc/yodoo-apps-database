import re
import datetime

import requests

from odoo import models, fields, api, tools

PYPI_CHECK_INTERVAL = 72  # days
PYPI_CHECK_CHUNK_SIZE = 5


class YodooModuleDependencyPython(models.Model):
    _name = 'yodoo.module.dependency.python'
    _inherit = 'generic.mixin.namesearch.by.fields'
    _description = "Yodoo Module Python Dependency"
    _order = 'name'
    _log_access = False

    _generic_namesearch_fields = ['name', 'pypi_package']

    name = fields.Char(index=True, required=True, readonly=True)
    pypi_package = fields.Char(index=True)
    pypi_url = fields.Char(
        compute='_compute_pypi_url',
        readonly=True)
    pypi_last_check = fields.Datetime()

    module_ids = fields.Many2manyView(
        comodel_name='yodoo.module',
        relation='yodoo_module_dependency_python_rel_view',
        column1='dependency_id',
        column2='module_id',
        string="Yodoo Modules",
        readonly=True)
    module_count = fields.Integer(
        compute='_compute_module_count', readonly=True)

    active = fields.Boolean(default=True, index=True)

    @api.depends('pypi_package')
    def _compute_pypi_url(self):
        for record in self:
            if record.pypi_package:
                record.pypi_url = "https://pypi.org/project/%s/" % (
                    record.pypi_package)
            else:
                record.pypi_url = False

    @api.depends('module_ids')
    def _compute_module_count(self):
        for record in self:
            record.module_count = len(record.module_ids)

    def name_get(self):
        res = []
        for record in self:
            if record.pypi_package:
                res += [
                    (record.id, "%s [%s]" % (record.name, record.pypi_package))
                ]
            else:
                res += [(record.id, record.name)]
        return res

    @api.model
    @tools.ormcache('name')
    def _get_python_dependency(self, name):
        dependency = self.with_context(active_test=False).search(
            [('name', '=', name)], limit=1)
        if dependency:
            return dependency.id
        return False

    @api.model
    def get_or_create(self, name):
        dependency_id = self._get_python_dependency(name)
        if not dependency_id:
            dependency_id = self.create({
                'name': name,
            }).id
            self._get_python_dependency.clear_cache(self)
        return dependency_id

    def action_check_pypi(self):
        """ Check if this package is available on PyPI
        """
        for record in self:
            # Try to split version from specifications like
            # algoliasearch>=2.0,<3.0
            #
            # TODO: may be it have sense to add version specification as
            # separate fields to this model?
            m = re.match(r'([\w\-\+\.]+)(?:[><=~]+.*)?', record.name)
            if m:
                package_name = m.groups()[0]
            else:
                package_name = record.name

            res = requests.head(
                "https://pypi.org/project/%s/" % package_name,
                allow_redirects=True,
                timeout=5)
            if res.status_code == 200:
                m = re.match("https://pypi.org/project/(.+)/", res.url)
                if m:
                    record.pypi_package = m.groups()[0]
        self.write({'pypi_last_check': fields.Datetime.now()})

    def action_show_modules(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'yodoo_apps_database.action_yodoo_module_view',
            domain=[('dependency_python_ids.id', '=', self.id)])

    @api.model
    def scheduler_find_pypi_packages(self):
        search_date = datetime.datetime.now() - datetime.timedelta(
            days=PYPI_CHECK_INTERVAL)

        self.search(
            [('pypi_package', '=', False),
             '|',
             ('pypi_last_check', '=', False),
             ('pypi_last_check', '<=', search_date)],
            limit=PYPI_CHECK_CHUNK_SIZE,
            order='pypi_last_check'
        ).action_check_pypi()
