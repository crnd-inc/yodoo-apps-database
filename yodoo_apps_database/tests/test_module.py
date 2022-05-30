import logging

from odoo.tests.common import TransactionCase
from odoo import exceptions

_logger = logging.getLogger(__name__)


class TestModule(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestModule, cls).setUpClass()

        cls.module_base = cls.env.ref(
            'yodoo_apps_database.odoo_community_module__base')

    def test_module_base(self):
        self.assertTrue(self.module_base.active)
        self.assertTrue(self.module_base.is_odoo_community_addon)
        self.assertEqual(self.module_base.total_price, 0)

    def test_module_create_update(self):
        # pylint: disable=too-many-statements
        module_version = self.env['yodoo.module'].create_or_update_module(
            'my_super_module', {
                'name': 'My Super Module',
                'summary': 'Test module info',
                'version': '12.0.1.2.3',
            })

        self.assertEqual(module_version._name, 'yodoo.module.version')
        self.assertEqual(module_version.system_name, 'my_super_module')
        self.assertEqual(module_version.summary, 'Test module info')
        self.assertEqual(module_version.version, '12.0.1.2.3')
        self.assertFalse(module_version.license_id)
        self.assertFalse(module_version.author_ids)
        self.assertFalse(module_version.application)
        self.assertTrue(module_version.installable)
        self.assertFalse(module_version.auto_install)
        self.assertFalse(module_version.website)
        self.assertEqual(module_version.price, 0.0)
        self.assertEqual(module_version.serie_major, 12)
        self.assertEqual(module_version.serie_minor, 0)
        self.assertEqual(module_version.version_major, 1)
        self.assertEqual(module_version.version_minor, 2)
        self.assertEqual(module_version.version_patch, 3)
        self.assertFalse(module_version.version_non_standard)

        module_serie = module_version.module_serie_id
        self.assertEqual(module_serie.serie_id.name, '12.0')
        self.assertEqual(module_serie.version_count, 1)

        # Try to updae module with same version and check that module versiion
        # info updated
        # (arg 'no_update' is set to False by default)
        module_version2 = self.env['yodoo.module'].create_or_update_module(
            'my_super_module', {
                'name': 'My Super Module',
                'summary': 'Test module info 2',
                'version': '12.0.1.2.3',
            })

        self.assertEqual(module_version2, module_version)
        self.assertEqual(module_version2._name, 'yodoo.module.version')
        self.assertEqual(module_version2.system_name, 'my_super_module')
        self.assertEqual(module_version2.summary, 'Test module info 2')
        self.assertEqual(module_version2.version, '12.0.1.2.3')
        self.assertFalse(module_version2.license_id)
        self.assertFalse(module_version2.author_ids)
        self.assertFalse(module_version2.application)
        self.assertTrue(module_version2.installable)
        self.assertFalse(module_version2.auto_install)
        self.assertFalse(module_version2.website)
        self.assertEqual(module_version2.price, 0.0)
        self.assertEqual(module_version2.serie_major, 12)
        self.assertEqual(module_version2.serie_minor, 0)
        self.assertEqual(module_version2.version_major, 1)
        self.assertEqual(module_version2.version_minor, 2)
        self.assertEqual(module_version2.version_patch, 3)
        self.assertFalse(module_version2.version_non_standard)
        self.assertEqual(module_serie.version_count, 1)

        # Try to update module with 'no_update' set to True (same version)
        # If version not changed, then module data will not be updated
        module_version3 = self.env['yodoo.module'].create_or_update_module(
            'my_super_module',
            {
                'name': 'My Super Module',
                'summary': 'Test module info 3',
                'version': '12.0.1.2.3',
            },
            no_update=True)

        self.assertEqual(module_version2, module_version3)
        self.assertEqual(module_version3._name, 'yodoo.module.version')
        self.assertEqual(module_version3.system_name, 'my_super_module')
        self.assertEqual(module_version3.summary, 'Test module info 2')
        self.assertEqual(module_version3.version, '12.0.1.2.3')
        self.assertFalse(module_version3.license_id)
        self.assertFalse(module_version3.author_ids)
        self.assertFalse(module_version3.application)
        self.assertTrue(module_version3.installable)
        self.assertFalse(module_version3.auto_install)
        self.assertFalse(module_version3.website)
        self.assertEqual(module_version3.price, 0.0)
        self.assertEqual(module_version3.serie_major, 12)
        self.assertEqual(module_version3.serie_minor, 0)
        self.assertEqual(module_version3.version_major, 1)
        self.assertEqual(module_version3.version_minor, 2)
        self.assertEqual(module_version3.version_patch, 3)
        self.assertFalse(module_version3.version_non_standard)
        self.assertEqual(module_serie.version_count, 1)

        # Try to update module with 'no_update' set to True (different version)
        # The version was changed, so module info have to be updated
        module_version4 = self.env['yodoo.module'].create_or_update_module(
            'my_super_module',
            {
                'name': 'My Super Module',
                'summary': 'Test module info 3',
                'version': '12.0.1.2.4',
            },
            no_update=True)

        self.assertNotEqual(module_version2, module_version4)
        self.assertEqual(module_version4._name, 'yodoo.module.version')
        self.assertEqual(module_version4.system_name, 'my_super_module')
        self.assertEqual(module_version4.summary, 'Test module info 3')
        self.assertEqual(module_version4.version, '12.0.1.2.4')
        self.assertFalse(module_version4.license_id)
        self.assertFalse(module_version4.author_ids)
        self.assertFalse(module_version4.application)
        self.assertTrue(module_version4.installable)
        self.assertFalse(module_version4.auto_install)
        self.assertFalse(module_version4.website)
        self.assertEqual(module_version4.price, 0.0)
        self.assertEqual(module_version4.serie_major, 12)
        self.assertEqual(module_version4.serie_minor, 0)
        self.assertEqual(module_version4.version_major, 1)
        self.assertEqual(module_version4.version_minor, 2)
        self.assertEqual(module_version4.version_patch, 4)
        self.assertFalse(module_version4.version_non_standard)
        self.assertEqual(module_serie.version_count, 2)

    def test_module_version_without_serie_error(self):
        with self.assertRaises(exceptions.ValidationError):
            # We cannot handle versions without series
            self.env['yodoo.module'].create_or_update_module(
                'my_super_module', {
                    'name': 'My Super Module',
                    'summary': 'Test module info',
                    'version': '1.2',
                })

    def test_module_version_without_serie(self):
        module_version = self.env['yodoo.module'].create_or_update_module(
            'my_super_module', {
                'name': 'My Super Module',
                'summary': 'Test module info',
                'version': '1.2',
            },
            enforce_serie='12.0')

        self.assertEqual(module_version._name, 'yodoo.module.version')
        self.assertEqual(module_version.system_name, 'my_super_module')
        self.assertEqual(module_version.summary, 'Test module info')
        self.assertEqual(module_version.version, '12.0.1.2')
        self.assertEqual(module_version.serie_major, 12)
        self.assertEqual(module_version.serie_minor, 0)
        self.assertEqual(module_version.version_major, 1)
        self.assertEqual(module_version.version_minor, 2)
        self.assertEqual(module_version.version_patch, 0)
        self.assertFalse(module_version.version_non_standard)

        module_version2 = self.env['yodoo.module'].create_or_update_module(
            'my_super_module', {
                'name': 'My Super Module',
                'summary': 'Test module info 2',
                'version': '1.2.3',
            },
            enforce_serie='12.0')

        self.assertEqual(module_version2._name, 'yodoo.module.version')
        self.assertEqual(module_version2.system_name, 'my_super_module')
        self.assertEqual(module_version2.summary, 'Test module info 2')
        self.assertEqual(module_version2.version, '12.0.1.2.3')
        self.assertEqual(module_version2.serie_major, 12)
        self.assertEqual(module_version2.serie_minor, 0)
        self.assertEqual(module_version2.version_major, 1)
        self.assertEqual(module_version2.version_minor, 2)
        self.assertEqual(module_version2.version_patch, 3)
        self.assertFalse(module_version2.version_non_standard)

        module_version3 = self.env['yodoo.module'].create_or_update_module(
            'my_super_module',
            {
                'name': 'My Super Module',
                'summary': 'Test module info 3',
                'version': '13.0.1.2.4',
            },
            enforce_serie='12.0')

        self.assertEqual(module_version3._name, 'yodoo.module.version')
        self.assertEqual(module_version3.system_name, 'my_super_module')
        self.assertEqual(module_version3.summary, 'Test module info 3')
        self.assertEqual(module_version3.version, '12.0.13.0.1.2.4')
        self.assertEqual(module_version3.serie_major, 12)
        self.assertEqual(module_version3.serie_minor, 0)
        self.assertEqual(module_version3.version_major, 13)
        self.assertEqual(module_version3.version_minor, 0)
        self.assertEqual(module_version3.version_patch, 1)
        self.assertEqual(module_version3.version_extra, '2.4')

    def test_module_version_non_standard(self):
        module_version = self.env['yodoo.module'].create_or_update_module(
            'my_super_module', {
                'name': 'My Super Module',
                'summary': 'Test module info',
                'version': '15.21.10.06.0',
            },
            enforce_serie='15.0')

        self.assertEqual(module_version._name, 'yodoo.module.version')
        self.assertEqual(module_version.system_name, 'my_super_module')
        self.assertEqual(module_version.summary, 'Test module info')
        self.assertEqual(module_version.serie_major, 15)
        self.assertEqual(module_version.serie_minor, 0)
        self.assertEqual(module_version.version_major, 15)
        self.assertEqual(module_version.version_minor, 21)
        self.assertEqual(module_version.version_patch, 10)
        self.assertEqual(module_version.version_extra, '06.0')
        self.assertEqual(module_version.version, '15.0.15.21.10.06.0')
        self.assertFalse(module_version.version_non_standard)

    def test_module_version_without_serie_2(self):
        # We have to test case when at first version is added with serie
        # in version and then without serie in version
        module_version = self.env['yodoo.module'].create_or_update_module(
            'my_super_module', {
                'name': 'My Super Module',
                'summary': 'Test module info',
                'version': '12.0.1.2',
            },)

        self.assertEqual(module_version._name, 'yodoo.module.version')
        self.assertEqual(module_version.system_name, 'my_super_module')
        self.assertEqual(module_version.summary, 'Test module info')
        self.assertEqual(module_version.version, '12.0.1.2')
        self.assertEqual(module_version.serie_major, 12)
        self.assertEqual(module_version.serie_minor, 0)
        self.assertEqual(module_version.version_major, 1)
        self.assertEqual(module_version.version_minor, 2)
        self.assertEqual(module_version.version_patch, 0)
        self.assertFalse(module_version.version_non_standard)

        module_version2 = self.env['yodoo.module'].create_or_update_module(
            'my_super_module', {
                'name': 'My Super Module',
                'summary': 'Test module info 2',
                'version': '1.2',
            },
            enforce_serie='12.0')

        self.assertEqual(module_version2._name, 'yodoo.module.version')
        self.assertEqual(module_version2.system_name, 'my_super_module')
        self.assertEqual(module_version2.summary, 'Test module info 2')
        self.assertEqual(module_version2.version, '12.0.1.2')
        self.assertEqual(module_version2.serie_major, 12)
        self.assertEqual(module_version2.serie_minor, 0)
        self.assertEqual(module_version2.version_major, 1)
        self.assertEqual(module_version2.version_minor, 2)
        self.assertEqual(module_version2.version_patch, 0)
        self.assertFalse(module_version2.version_non_standard)
