import re
import logging
from odoo import models, fields, api, exceptions, _

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
    r"(?P<serie>\d+\.\d+)\."
    r"(?P<version>.+)"
    r"$")


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
    module_id = fields.Many2one(
        'yodoo.module', related='module_serie_id.module_id',
        store=True, index=True, readonly=True)
    serie_id = fields.Many2one(
        'yodoo.serie', related='module_serie_id.serie_id',
        store=True, index=True, readonly=True)

    # Odoo Serie info
    system_name = fields.Char(
        related='module_serie_id.module_id.system_name',
        readonly=True, store=True)
    serie = fields.Char(
        related='module_serie_id.serie_id.name', store=True,
        index=True, readonly=True)
    serie_major = fields.Integer(
        related='module_serie_id.serie_id.major', store=True,
        index=True, readonly=True)
    serie_minor = fields.Integer(
        related='module_serie_id.serie_id.minor', store=True,
        index=True, readonly=True)

    # Version parts
    version = fields.Char(readonly=True, index=True)
    version_major = fields.Integer(index=True, readonly=True)
    version_minor = fields.Integer(index=True, readonly=True)
    version_patch = fields.Integer(index=True, readonly=True)
    version_extra = fields.Char(readonly=True)
    version_non_standard = fields.Boolean(readonly=True)

    # License
    license_id = fields.Many2one(
        'yodoo.module.license', readonly=True, ondelete='restrict')
    category_id = fields.Many2one(
        'yodoo.module.category', readonly=True, ondelete='restrict')
    author_ids = fields.Many2many(
        comodel_name='yodoo.module.author',
        relation='yodoo_module_version_author_rel',
        column1='version_id', column2='author_id',
        readonly=True)

    # Module info
    name = fields.Char(readonly=True)
    summary = fields.Char(readonly=True)
    application = fields.Boolean(readonly=True)
    installable = fields.Boolean(readonly=True)
    auto_install = fields.Boolean(readonly=True)
    website = fields.Char(readonly=True)

    _sql_constraints = [
        ('module_version_uniq',
         'unique(module_id, version)',
         '(version, module) pair must be unique!')
    ]

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

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result += [
                (record.id, "%s [%s]" % (
                    record.module_id.display_name, record.version)),
            ]
        return result

    @api.model
    def create_or_update_version(self, module, data, no_update=False):
        version = self.with_context(active_test=False).search(
            [('module_id', '=', module.id),
             ('version', '=', data['version'])],
            limit=1)
        if version and no_update:
            return version

        version_data = {
            'module_id': module.id,
            'version': data['version'],
        }

        # Add version info to data
        parsed_version = self._parse_version(data['version'])
        if parsed_version:
            serie_id = self.env['yodoo.serie'].get_or_create(
                parsed_version['serie'])
            module_serie = self.env['yodoo.module.serie'].get_or_create(
                module.id, serie_id)
            version_data.update({
                'module_serie_id': module_serie.id,
                'version_major': parsed_version['version_major'],
                'version_minor': parsed_version['version_minor'],
                'version_patch': parsed_version['version_patch'],
                'version_extra': parsed_version['version_extra'],
                'version_non_standard': parsed_version['version_non_standard'],
            })
        else:
            version_data.update({
                'module_serie_id': module_serie.id,
                'version_major': 0,
                'version_minor': 0,
                'version_patch': 0,
                'version_extra': 0,
                'version_non_standard': True,
            })

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
        })

        if version:
            version.write(version_data)
            return version

        return self.create(version_data)
