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
        required=True, readonly=True, store=True)
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

    # External dependencies
    dependency_python_ids = fields.Many2many(
        comodel_name='yodoo.module.dependency.python',
        relation='yodoo_module_version_dependency_python_rel',
        column1='module_version_id',
        column2='dependency_id',
        string="Python dependencies",
        readonly=True)
    dependency_bin_ids = fields.Many2many(
        comodel_name='yodoo.module.dependency.binary',
        relation='yodoo_module_version_dependency_binary_rel',
        column1='module_version_id',
        column2='dependency_id',
        string="Binary dependencies",
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

    # Module Serie info
    is_odoo_community_addon = fields.Boolean(
        related='module_serie_id.is_odoo_community_addon', readonly=True)

    # Date added & updated
    date_added = fields.Datetime(
        default=fields.Datetime.now, readonly=True)
    date_updated = fields.Datetime(
        default=fields.Datetime.now, readonly=True)

    _sql_constraints = [
        ('module_version_uniq',
         'unique(module_id, version)',
         '(version, module) pair must be unique!')
    ]

    @api.model
    def init(self):
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
        create_sql_view(
            self.env.cr, 'yodoo_module_serie_dependency_rel_view',
            """
                SELECT DISTINCT
                    mos.id   AS module_serie_id,
                    mosd.id  AS dependency_module_serie_id
                FROM yodoo_module_version_dependency_rel AS vd_rel
                LEFT JOIN yodoo_module_version AS mv
                    ON mv.id = vd_rel.module_version_id
                LEFT JOIN yodoo_module_serie AS mos
                    ON mv.module_serie_id = mos.id
                LEFT JOIN yodoo_module AS mod
                    ON vd_rel.dependency_module_id = mod.id
                LEFT JOIN yodoo_module_serie AS mosd
                    ON mod.id = mosd.module_id AND mv.serie_id = mosd.serie_id
                WHERE mv.id = mos.last_version_id
            """)
        create_sql_view(
            self.env.cr, 'yodoo_module_serie_dependency_all_rel_view',
            """
                WITH RECURSIVE all_deps AS (
                    SELECT module_serie_id,
                           dependency_module_serie_id
                    FROM yodoo_module_serie_dependency_rel_view

                    UNION

                    SELECT DISTINCT v.module_serie_id,
                        all_deps.dependency_module_serie_id
                    FROM yodoo_module_serie_dependency_rel_view AS v
                    JOIN all_deps
                        ON (all_deps.module_serie_id =
                            v.dependency_module_serie_id)
                )
                SELECT * FROM all_deps
            """)

        # External dependencies (module)
        create_sql_view(
            self.env.cr, 'yodoo_module_dependency_binary_rel_view',
            """
                SELECT DISTINCT
                    mv.module_id,
                    vd_rel.dependency_id AS dependency_id
                FROM yodoo_module_version_dependency_binary_rel AS vd_rel
                LEFT JOIN yodoo_module_version AS mv
                    ON mv.id = vd_rel.module_version_id
                LEFT JOIN yodoo_module AS mod
                    ON mv.module_id = mod.id
                WHERE mv.id = mod.last_version_id
            """)
        create_sql_view(
            self.env.cr, 'yodoo_module_dependency_python_rel_view',
            """
                SELECT DISTINCT
                    mv.module_id,
                    vd_rel.dependency_id AS dependency_id
                FROM yodoo_module_version_dependency_python_rel AS vd_rel
                LEFT JOIN yodoo_module_version AS mv
                    ON mv.id = vd_rel.module_version_id
                LEFT JOIN yodoo_module AS mod
                    ON mv.module_id = mod.id
                WHERE mv.id = mod.last_version_id
            """)

        # External dependencies (module serie)
        create_sql_view(
            self.env.cr, 'yodoo_module_serie_dependency_binary_rel_view',
            """
                SELECT DISTINCT
                    mv.module_serie_id,
                    vd_rel.dependency_id AS dependency_id
                FROM yodoo_module_version_dependency_binary_rel AS vd_rel
                LEFT JOIN yodoo_module_version AS mv
                    ON mv.id = vd_rel.module_version_id
                LEFT JOIN yodoo_module_serie AS mos
                    ON mv.module_serie_id = mos.id
                WHERE mv.id = mos.last_version_id
            """)
        create_sql_view(
            self.env.cr, 'yodoo_module_serie_dependency_python_rel_view',
            """
                SELECT DISTINCT
                    mv.module_serie_id,
                    vd_rel.dependency_id AS dependency_id
                FROM yodoo_module_version_dependency_python_rel AS vd_rel
                LEFT JOIN yodoo_module_version AS mv
                    ON mv.id = vd_rel.module_version_id
                LEFT JOIN yodoo_module_serie AS mos
                    ON mv.module_serie_id = mos.id
                WHERE mv.id = mos.last_version_id
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

    def _prepare_python_dependencies(self, python_dependencies):
        if not python_dependencies:
            return []

        if not isinstance(python_dependencies, (list, tuple, set)):
            _logger.warning(
                "Cannot parse python dependencies: %r", python_dependencies)
            return []

        return [
            self.env['yodoo.module.dependency.python'].get_or_create(py_dep)
            for py_dep in python_dependencies
            if py_dep.strip()
        ]

    def _prepare_binary_dependencies(self, bin_dependencies):
        if not bin_dependencies:
            return []

        return [
            self.env['yodoo.module.dependency.binary'].get_or_create(bin_dep)
            for bin_dep in bin_dependencies
            if bin_dep.strip()
        ]

    def _prepare_external_dependencies(self, data):
        """ Parse external dependencies and return dictionary with
            write-ready info about dependencies
        """
        external_dependencies = data.get('external_dependencies', {})
        if not external_dependencies:
            return {}
        if not isinstance(external_dependencies, dict):
            _logger.warning(
                "Cannot parse external dependencies (%r) in manifest:\n%r".
                external_dependencies, data)
            return {}

        try:
            py_deps = self._prepare_python_dependencies(
                external_dependencies.get('python', []))
        except Exception:
            _logger.warning(
                "Cannot parse python dependencies (%r) in manifest:\n%r",
                external_dependencies.get('python', []), data, exc_info=True)
            py_deps = []

        try:
            bin_deps = self._prepare_binary_dependencies(
                external_dependencies.get('bin', []))
        except Exception:
            _logger.warning(
                "Cannot parse binary dependencies (%r) in manifest:\n%r",
                external_dependencies.get('bin', []), data, exc_info=True)
            bin_deps = []

        res = {}
        if py_deps:
            res['dependency_python_ids'] = [(6, 0, py_deps)]
        if bin_deps:
            res['dependency_bin_ids'] = [(6, 0, bin_deps)]
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

    def name_get(self):
        result = []
        for record in self:
            result += [
                (record.id, "%s [%s]" % (
                    record.module_id.display_name, record.version)),
            ]
        return result

    def _create_or_update_prepare_parse_version(self, module, data,
                                                enforce_serie=None):
        """ Parse version and prepare version info suitable for write
        """
        version_name = data['version']

        # add version info to data
        parsed_version = self._parse_version(version_name)
        if enforce_serie:
            # In case of enforce seria, we apply additional checks, to ensure
            # that we parsed version correctly.
            # If version has standard format, everything seems to be ok,
            # because odoo serie is first two numbers of version.
            # But in case of non-standard versions, we have to manually add
            # odoo serie to such version to parse it properly. Also, we have to
            # note that we do it in this way to be compatible with version
            # numbers provided by odoo itself:
            # see adapt_version func in odoo code:
            # https://github.com/odoo/odoo/blob/15.0/odoo/modules/module.py
            if parsed_version and parsed_version['serie'] != enforce_serie:
                version_name = "%(serie)s.%(version)s" % {
                    'serie': enforce_serie,
                    'version': data['version'],
                }
                parsed_version = self._parse_version(version_name)
            elif not parsed_version:
                version_name = "%(serie)s.%(version)s" % {
                    'serie': enforce_serie,
                    'version': data['version'],
                }
                parsed_version = self._parse_version(version_name)
        if parsed_version:
            serie_id = self.env['yodoo.serie'].get_or_create(
                parsed_version['serie'])
            module_serie = self.env['yodoo.module.serie'].get_or_create(
                module.id, serie_id)
            return {
                'module_serie_id': module_serie.id,
                'module_id': module.id,
                'serie_id': serie_id,
                'serie': module_serie.serie_id.name,
                'serie_major': module_serie.serie_id.major,
                'serie_minor': module_serie.serie_id.minor,
                'version': version_name,
                'version_major': parsed_version['version_major'],
                'version_minor': parsed_version['version_minor'],
                'version_patch': parsed_version['version_patch'],
                'version_extra': parsed_version['version_extra'],
                'version_non_standard': parsed_version['version_non_standard'],
            }
        raise exceptions.ValidationError(_(
            'Cannot parse version (%(version)s) '
            'for module %(module_display_name)s [%(module_system_name)s]'
        ) % {
            'version': data['version'],
            'module_display_name': module.display_name,
            'module_system_name': module.system_name,
        })

    def _create_or_update_prepare_version_data(self, module, data):
        version_data = {
            'module_id': module.id,
            'system_name': module.system_name,
        }

        # TODO: wrap parsing of each param in try/except
        version_data.update({
            'name': data.get('name', False),
            'license_id': self._prepare_license(data.get('license')),
            'category_id': self._prepare_category(data.get('category')),
            'author_ids': [(6, 0, self._prepare_author(data.get('author')))],
            'summary': data.get('summary', False),
            'application': data.get('application', False),
            'installable': data.get('installable', True),
            'auto_install': data.get('auto_install', False),
            'website': data.get('website', False),
            'price': self._prepare_price(data.get('price')),
            'currency_id': self._prepare_currency(data.get('currency')),
            'dependency_ids': [
                (6, 0, self._prepare_depends(data.get('depends', [])))],
        })
        version_data.update(self._prepare_external_dependencies(data))
        return version_data

    def _choose_last_version(self, for_obj, old_version, new_version):
        """ Determine last version between provided versions

            :param Record for_obj: compute last version for this object
            :param Record old_version: Record that represents old version
            :param Record new_version: Record that represents new version
            :returns Record: Record of computed last version
        """
        if not old_version:
            return new_version
        if V(old_version.version) < V(new_version.version):
            return new_version
        return old_version

    def _create_or_update_prepare_module_data(self, module,
                                              version, version_data):
        new_version = self._choose_last_version(
            module, module.last_version_id, version)

        module_data = {}
        if module.last_version_id != new_version:
            module_data = {
                'last_version_id': new_version.id
            }

        if module_data:
            module_data['version_count'] = self.search_count(
                [('module_id', '=', module.id)])
            for field_name in VERSION_TO_MODULE_SYNC_FIELDS:
                module_data[field_name] = version_data[field_name]
        return module_data

    def _create_or_update_prepare_module_serie_data(self, module_serie,
                                                    version, version_data):
        new_version = self._choose_last_version(
            module_serie, module_serie.last_version_id, version)
        serie_data = {}
        if module_serie.last_version_id != new_version:
            serie_data['last_version_id'] = new_version.id

        if serie_data:
            serie_data['version_count'] = self.search_count(
                [('module_serie_id', '=', module_serie.id)])
        return serie_data

    def _preprocess_module_data(self, data):
        version = data.get('version', '0.0.0')
        if not version:
            version = '0.0.0'
        return {
            'name': data.get('name', False),
            'version': version,
            'author': data.get('author', False),
            'summary': data.get('summary', False),
            'license': data.get('license', False),
            'application': data.get('application', False),
            'installable': data.get('installable', True),
            'auto_install': data.get('auto_install', False),
            'category': data.get('category', False),
            'icon': data.get('icon'),
            'website': data.get('website', False),
            'sequence': data.get('sequence', False),
            'price': data.get('price'),
            'currency': data.get('currency'),
            'depends': data.get('depends', []),
            'external_dependencies': data.get('external_dependencies', []),
        }

    @api.model
    def create_or_update_version(self, module, data, no_update=False,
                                 enforce_serie=None):
        """ This method have to be the single point to
            delete/update module versions

            For performance reason this method also updates following models:
                - module
                - module serie

            :param str module: Recordset of single module to update
            :param dict data: dictionary with data to update module with
            :param bool no_update: do not update version if it is exists
            :param str enforce_serie: suggest odoo serie to better detect
                 odoo version
            :return: Instance of created version
        """
        data = self._preprocess_module_data(data)
        version_info = self._create_or_update_prepare_parse_version(
            module, data, enforce_serie=enforce_serie)
        version = self.with_context(active_test=False).search(
            [('module_id', '=', module.id),
             ('version', '=', version_info['version'])],
            limit=1)
        if version and no_update:
            return version

        version_data = {}
        version_data.update(version_info)
        version_data.update(
            self._create_or_update_prepare_version_data(module, data))

        if version:
            version.write(
                dict(version_data, date_updated=fields.Datetime.now()))
        else:
            version = self.create(version_data)

        module_data = self._create_or_update_prepare_module_data(
            module, version, version_data)
        if module_data:
            module.write(module_data)

        serie_data = self._create_or_update_prepare_module_serie_data(
            version.module_serie_id, version, version_data)
        if serie_data:
            version.module_serie_id.write(serie_data)

        return version
