import re
import logging
from pkg_resources import parse_version as V
from odoo import models, fields, api, tools, exceptions, _
from ..tools import create_sql_view

_logger = logging.getLogger(__name__)

RE_VERSION = re.compile(
    r"^"
    r"(?P<serie>\d+\.\d+)\."
    r"(?P<version_major>\d+)\.(?P<version_minor>\d+)"
    r"(\.(?P<version_patch>\d+))?"
    r"$")

RE_VERSION_EXT = re.compile(
    r"^"
    r"(?P<serie>\d+\.\d+)\."
    r"(?P<version_major>\d+)\.(?P<version_minor>\d+)"
    r"(\.(?P<version_patch>\d+))?"
    r"(\.(?P<version_extra>[a-zA-Z0-9\.\-_]+))?"
    r"$")
RE_VERSION_NOT_STANDARD = re.compile(
    r"^"
    r"(?P<serie>\d+\.\d+)\.?"
    r"(?P<version>.+)"
    r"$")

# List of fields to sync from last version to module
VERSION_TO_MODULE_SYNC_FIELDS = [
    'license_id',
    'category_id',
    'name',
    'version',
    'summary',
    'application',
    'installable',
    'auto_install',
    # 'icon',
    'website',
    'price',
    'currency_id',
]


class OdooModuleVersion(models.Model):
    _name = 'yodoo.module.version'
    _description = 'Odoo Module Version'
    _log_acces = False
    _order = (
        "module_id, serie_major DESC, serie_minor DESC, "
        "version_major DESC, version_minor DESC, version_patch DESC"
    )

    module_serie_id = fields.Many2one(
        'yodoo.module.serie', required=True, readonly=True, index=True,
        ondelete='cascade')
    # Updated when version created
    module_id = fields.Many2one(
        'yodoo.module',
        store=True, index=True, readonly=True, required=True)
    serie_id = fields.Many2one(
        'yodoo.serie',
        store=True, index=True, readonly=True, required=True)

    # Odoo Serie info
    # Updated when version created
    system_name = fields.Char(
        related='module_serie_id.module_id.system_name',
        readonly=True, store=True)
    serie = fields.Char(
        store=True, index=True, readonly=True)
    serie_major = fields.Integer(
        store=True, index=True, readonly=True)
    serie_minor = fields.Integer(
        store=True, index=True, readonly=True)

    # Version parts
    version = fields.Char(readonly=True, index=True)
    version_major = fields.Integer(index=True, readonly=True)
    version_minor = fields.Integer(index=True, readonly=True)
    version_patch = fields.Integer(index=True, readonly=True)
    version_extra = fields.Char(readonly=True)
    version_non_standard = fields.Boolean(readonly=True)

    # References
    license_id = fields.Many2one(
        'yodoo.module.license', readonly=True, ondelete='restrict')
    category_id = fields.Many2one(
        'yodoo.module.category', readonly=True, ondelete='restrict')
    author_ids = fields.Many2many(
        comodel_name='yodoo.module.author',
        relation='yodoo_module_version_author_rel',
        column1='version_id', column2='author_id',
        readonly=True)
    dependency_ids = fields.Many2many(
        comodel_name='yodoo.module',
        relation='yodoo_module_version_dependency_rel',
        column1='module_version_id',
        column2='dependency_module_id',
        readonly=True)

    # Module info
    name = fields.Char(readonly=True)
    summary = fields.Char(readonly=True)
    application = fields.Boolean(readonly=True)
    installable = fields.Boolean(readonly=True)
    auto_install = fields.Boolean(readonly=True)
    website = fields.Char(readonly=True)
    price = fields.Monetary(readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)
    icon = fields.Binary(attachment=True)

    _sql_constraints = [
        ('module_version_uniq',
         'unique(module_id, version)',
         '(version, module) pair must be unique!')
    ]

    @api.model_cr
    def init(self):
        create_sql_view(
            self.env.cr, 'yodoo_module_version_dependency_all_rel_view',
            """
                SELECT DISTINCT
                    mv.module_id,
                    vd_rel.dependency_module_id AS dependency_id
                FROM yodoo_module_version_dependency_rel AS vd_rel
                LEFT JOIN yodoo_module_version AS mv
                    ON mv.id = vd_rel.module_version_id
                LEFT JOIN yodoo_module AS mod
                    ON mv.module_id = mod.id
                WHERE mv.id = mod.last_version_id
            """)
        create_sql_view(
            self.env.cr, 'yodoo_module_dependency_rel_view',
            """
                SELECT DISTINCT
                    mv.module_id,
                    vd_rel.dependency_module_id AS dependency_id
                FROM yodoo_module_version_dependency_rel AS vd_rel
                LEFT JOIN yodoo_module_version AS mv
                    ON mv.id = vd_rel.module_version_id
                LEFT JOIN yodoo_module AS mod
                    ON mv.module_id = mod.id
                WHERE mv.id = mod.last_version_id
            """)
        create_sql_view(
            self.env.cr, 'yodoo_module_dependency_all_rel_view',
            """
                WITH RECURSIVE all_deps AS (
                    SELECT module_id,
                           dependency_id
                    FROM yodoo_module_dependency_rel_view

                    UNION

                    SELECT DISTINCT v.module_id,
                        all_deps.dependency_id
                    FROM yodoo_module_dependency_rel_view AS v
                    JOIN all_deps ON all_deps.module_id = v.dependency_id
                )
                SELECT * FROM all_deps
            """)
        return super(OdooModuleVersion, self).init()

    @api.model
    def _parse_version(self, version):
        """ Parse version string and return dict with following fields:
            - serie
            - version_major
            - version_minor
            - version_patch
            - version_extra
            - version_non_standard : bool
        """
        res = RE_VERSION.match(version)
        if res:
            groups = res.groupdict()
            return {
                'serie': groups['serie'],
                'version_major': groups['version_major'],
                'version_minor': groups['version_minor'],
                'version_patch': groups.get('version_patch', 0),
                'version_extra': False,
                'version_non_standard': False,
            }
        res = RE_VERSION_EXT.match(version)
        if res:
            groups = res.groupdict()
            return {
                'serie': groups['serie'],
                'version_major': groups['version_major'],
                'version_minor': groups['version_minor'],
                'version_patch': groups.get('version_patch', 0),
                'version_extra': groups.get('version_extra', False),
                'version_non_standard': False,
            }

        res = RE_VERSION_NOT_STANDARD.match(version)
        if res:
            groups = res.groupdict()
            return {
                'serie': groups['serie'],
                'version_major': False,
                'version_minor': False,
                'version_patch': False,
                'version_extra': False,
                'version_non_standard': True,
            }

        return False

    def _prepare_author(self, author):
        if not author:
            return []

        if isinstance(author, str):
            author_names = author.split(',')
        elif isinstance(author, (list, tuple, set)):
            author_names = author
        else:
            author_names = [str(author)]

        res = []
        for author_name in author_names:
            if author_name.strip():
                author_id = self.env['yodoo.module.author'].get_or_create(
                    author_name.strip())
                res.append(author_id)
        return res

    def _prepare_license(self, license_name):
        if license_name:
            return self.env['yodoo.module.license'].get_or_create(license_name)
        return False

    def _prepare_category(self, category):
        if category:
            return self.env['yodoo.module.category'].get_or_create(category)
        return False

    @api.model
    @tools.ormcache()
    def _get_default_currency_id(self):
        return self.env['res.currency'].with_context(active_test=False).search(
            [('name', '=', 'EUR')], limit=1).id

    @api.model
    def get_default_currency(self):
        return self.env['res.currency'].browse(self._get_default_currency_id())

    @api.model
    @tools.ormcache('currency_name')
    def _get_currency_id_by_name(self, currency_name):
        return self.env['res.currency'].sudo().with_context(
            active_test=False
        ).search([('name', '=ilike', currency_name)], limit=1).id

    def _prepare_currency(self, currency_name):
        if currency_name:
            currency_id = self._get_currency_id_by_name(currency_name)
            if currency_id:
                return currency_id
        return self._get_default_currency_id()

    def _prepare_price(self, price):
        if not price:
            return 0.0
        try:
            price = float(price)
        except (ValueError, TypeError):
            price = 0.0
        return price

    def _prepare_depends(self, depends):
        if not isinstance(depends, (list, tuple)):
            _logger.warning(
                "Cannot parse dependencies for version: %s",
                self.display_name)
        res = []
        for dep in depends:
            module = self.env['yodoo.module'].get_or_create_module(dep)
            res += [module.id]
        return res

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result += [
                (record.id, "%s [%s]" % (
                    record.module_id.display_name, record.version)),
            ]
        return result

    def _create_or_update_prepare_version_data(self, module, data):
        version_data = {
            'module_id': module.id,
            'version': data['version'],
        }

        # add version info to data
        parsed_version = self._parse_version(data['version'])
        if parsed_version:
            serie_id = self.env['yodoo.serie'].get_or_create(
                parsed_version['serie'])
            module_serie = self.env['yodoo.module.serie'].get_or_create(
                module.id, serie_id)
            version_data.update({
                'module_serie_id': module_serie.id,
                'module_id': module.id,
                'serie_id': serie_id,
                'serie': module_serie.serie_id.name,
                'serie_major': module_serie.serie_id.major,
                'serie_minor ': module_serie.serie_id.minor,
                'version_major': parsed_version['version_major'],
                'version_minor': parsed_version['version_minor'],
                'version_patch': parsed_version['version_patch'],
                'version_extra': parsed_version['version_extra'],
                'version_non_standard': parsed_version['version_non_standard'],
            })
        else:
            raise exceptions.validationerror(_(
                'cannot parse version (%s) for module %s [%s]') % (
                    data['version'], module.display_name, module.system_name))

        version_data.update({
            'name': data.get('name', False),
            'license_id': self._prepare_license(data.get('license')),
            'category_id': self._prepare_category(data.get('category')),
            'author_ids': [(6, 0, self._prepare_author(data.get('author')))],
            'summary': data.get('summary', False),
            'application': data.get('application', False),
            'installable': data.get('installable', False),
            'auto_install': data.get('auto_install', False),
            'website': data.get('website', False),
            'price': self._prepare_price(data.get('price')),
            'currency_id': self._prepare_currency(data.get('currency')),
            'dependency_ids': [
                (6, 0, self._prepare_depends(data.get('depends', [])))],
        })
        return version_data

    def _create_or_update_prepare_module_data(self, module,
                                              version, version_data):
        module_data = {}
        if not module.last_version_id:
            module_data['last_version_id'] = version.id
        elif V(module.last_version_id.version) < V(version.version):
            module_data['last_version_id'] = version.id

        if module_data:
            module_data['version_count'] = self.search_count(
                [('module_id', '=', module.id)])
            for field_name in VERSION_TO_MODULE_SYNC_FIELDS:
                module_data[field_name] = version_data[field_name]
        return module_data

    def _create_or_update_prepare_module_serie_data(self, module_serie,
                                                    version, version_data):
        serie_data = {}
        if not module_serie.last_version_id:
            serie_data['last_version_id'] = version.id
        elif V(module_serie.last_version_id.version) < V(version.version):
            serie_data['last_version_id'] = version.id

        if serie_data:
            serie_data['version_count'] = self.search_count(
                [('module_serie_id', '=', module_serie.id)])
        return serie_data

    @api.model
    def create_or_update_version(self, module, data, no_update=False):
        """ This method have to be the single point to
            delete/update module versions

            For performance reason this method also updates following models:
                - module
                - module serie

            :param module: Recordset of single module to update
            :param data: dictionary with data to update module with
            :param no_update: do not update version if it is exists
        """
        version = self.with_context(active_test=False).search(
            [('module_id', '=', module.id),
             ('version', '=', data['version'])],
            limit=1)
        if version and no_update:
            return version

        version_data = self._create_or_update_prepare_version_data(
            module, data)

        if version:
            version.write(version_data)
        else:
            version = self.create(version_data)

        module_data = self._create_or_update_prepare_module_data(
            module, version, version_data)
        if module_data:
            module.write(module_data)

        serie_data = self._create_or_update_prepare_module_serie_data(
            version.module_serie_id, version, version_data)
        if serie_data:
            version.module_serie_id.update(serie_data)

        return version
