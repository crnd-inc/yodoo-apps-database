import logging

from odoo.tests.common import SavepointCase
from odoo import exceptions

_logger = logging.getLogger(__name__)


class TestModule(SavepointCase):

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
        self.assertEqual(module_version.name, 'My Super Module')
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

        # Test module info
        module = module_version.module_id
        self.assertEqual(module.system_name, 'my_super_module')
        self.assertEqual(module.name, 'My Super Module')
        self.assertEqual(module.summary, 'Test module info')
        self.assertEqual(module.version, '12.0.1.2.3')
        self.assertFalse(module.license_id)
        self.assertFalse(module.author_ids)
        self.assertFalse(module.application)
        self.assertTrue(module.installable)
        self.assertFalse(module.auto_install)
        self.assertFalse(module.website)
        self.assertEqual(module.price, 0.0)
        self.assertEqual(module.version_count, 1)
        self.assertEqual(module.serie_count, 1)
        self.assertEqual(module.last_version_id, module_version)

        # Test module serie
        module_serie = module_version.module_serie_id
        self.assertEqual(module_serie.serie_id.name, '12.0')
        self.assertEqual(module_serie.version_count, 1)
        self.assertEqual(module_serie.last_version_id, module_version)

        # Try to updae module with same version and check that module versiion
        # info updated
        # (arg 'no_update' is set to False by default)
        module_version2 = self.env['yodoo.module'].create_or_update_module(
            'my_super_module', {
                'name': 'My Super Module',
                'summary': 'Test module info 2',
                'version': '12.0.1.2.3',
            })

        # Test that module no new module version created
        self.assertEqual(module_version2, module_version)

        # Nest that version info was updated
        self.assertEqual(module_version2._name, 'yodoo.module.version')
        self.assertEqual(module_version2.system_name, 'my_super_module')
        self.assertEqual(module_version2.name, 'My Super Module')
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

        # Test that module info updated too
        self.assertEqual(module.system_name, 'my_super_module')
        self.assertEqual(module.name, 'My Super Module')
        self.assertEqual(module.summary, 'Test module info 2')
        self.assertEqual(module.version, '12.0.1.2.3')
        self.assertFalse(module.license_id)
        self.assertFalse(module.author_ids)
        self.assertFalse(module.application)
        self.assertTrue(module.installable)
        self.assertFalse(module.auto_install)
        self.assertFalse(module.website)
        self.assertEqual(module.price, 0.0)
        self.assertEqual(module.version_count, 1)
        self.assertEqual(module.serie_count, 1)
        self.assertEqual(module.last_version_id, module_version)

        # Test module serie info
        self.assertEqual(module_serie.serie_id.name, '12.0')
        self.assertEqual(module_serie.version_count, 1)
        self.assertEqual(module_serie.last_version_id, module_version)

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

        # Test that no new version created
        self.assertEqual(module_version2, module_version3)

        # Test that version info was not updated
        self.assertEqual(module_version3._name, 'yodoo.module.version')
        self.assertEqual(module_version3.system_name, 'my_super_module')
        self.assertEqual(module_version3.name, 'My Super Module')
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

        # Test that module info was not updated
        self.assertEqual(module.system_name, 'my_super_module')
        self.assertEqual(module.name, 'My Super Module')
        self.assertEqual(module.summary, 'Test module info 2')
        self.assertEqual(module.version, '12.0.1.2.3')
        self.assertFalse(module.license_id)
        self.assertFalse(module.author_ids)
        self.assertFalse(module.application)
        self.assertTrue(module.installable)
        self.assertFalse(module.auto_install)
        self.assertFalse(module.website)
        self.assertEqual(module.price, 0.0)
        self.assertEqual(module.version_count, 1)
        self.assertEqual(module.serie_count, 1)
        self.assertEqual(module.last_version_id, module_version)

        # Test module serie info
        self.assertEqual(module_serie.serie_id.name, '12.0')
        self.assertEqual(module_serie.version_count, 1)
        self.assertEqual(module_serie.last_version_id, module_version)

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

        # Test that new module version was creatd
        self.assertNotEqual(module_version2, module_version4)

        # Test that version info is correct
        self.assertEqual(module_version4._name, 'yodoo.module.version')
        self.assertEqual(module_version4.system_name, 'my_super_module')
        self.assertEqual(module_version4.name, 'My Super Module')
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

        # Test that module info was updated
        self.assertEqual(module.system_name, 'my_super_module')
        self.assertEqual(module.name, 'My Super Module')
        self.assertEqual(module.summary, 'Test module info 3')
        self.assertEqual(module.version, '12.0.1.2.4')
        self.assertFalse(module.license_id)
        self.assertFalse(module.author_ids)
        self.assertFalse(module.application)
        self.assertTrue(module.installable)
        self.assertFalse(module.auto_install)
        self.assertFalse(module.website)
        self.assertEqual(module.price, 0.0)
        self.assertEqual(module.version_count, 2)
        self.assertEqual(module.serie_count, 1)
        self.assertEqual(module.last_version_id, module_version4)

        # Test module serie info updated
        self.assertEqual(module_serie.serie_id.name, '12.0')
        self.assertEqual(module_serie.version_count, 2)
        self.assertEqual(module_serie.last_version_id, module_version4)

        # Try to update module with 'no_update' set to True (different version)
        # Also, provide additional module info
        module_version5 = self.env['yodoo.module'].create_or_update_module(
            'my_super_module',
            {
                'name': "My Super Module",
                'summary': "This module do cool things.",
                'author': "Center of Research and Development",
                'website': "https://crnd.pro",
                'category': 'Yodoo Apps',
                'version': '12.0.2.1.0',
                'depends': [
                    'crm',
                    'website',
                ],
                'installable': True,
                'application': True,
                'license': 'LGPL-3',
                'price': 500,
                'currency': 'EUR',
            },
            no_update=True)

        # Test that new module version was created
        self.assertNotEqual(module_version4, module_version5)

        # Test that version info is correct
        self.assertEqual(module_version5._name, 'yodoo.module.version')
        self.assertEqual(module_version5.system_name, 'my_super_module')
        self.assertEqual(module_version5.name, 'My Super Module')
        self.assertEqual(
            module_version5.summary,
            'This module do cool things.')
        self.assertEqual(module_version5.version, '12.0.2.1.0')
        self.assertEqual(module_version5.license_id.code, 'LGPL-3')
        self.assertEqual(len(module_version5.author_ids), 1)
        self.assertEqual(
            module_version5.author_ids.name,
            "Center of Research and Development")
        self.assertTrue(module_version5.application)
        self.assertTrue(module_version5.installable)
        self.assertFalse(module_version5.auto_install)
        self.assertEqual(module_version5.website, "https://crnd.pro")
        self.assertEqual(module_version5.price, 500.0)
        self.assertEqual(module_version5.currency_id.name, 'EUR')
        self.assertEqual(module_version5.serie_major, 12)
        self.assertEqual(module_version5.serie_minor, 0)
        self.assertEqual(module_version5.version_major, 2)
        self.assertEqual(module_version5.version_minor, 1)
        self.assertEqual(module_version5.version_patch, 0)
        self.assertFalse(module_version5.version_non_standard)

        # Test that module info was updated
        module.invalidate_cache(ids=module.ids)
        self.assertEqual(module.system_name, 'my_super_module')
        self.assertEqual(module.summary, 'This module do cool things.')
        self.assertEqual(module.version, '12.0.2.1.0')
        self.assertEqual(module.license_id.code, 'LGPL-3')
        self.assertEqual(len(module.author_ids), 1)
        self.assertEqual(
            module.author_ids.name,
            "Center of Research and Development")
        self.assertTrue(module.application)
        self.assertTrue(module.installable)
        self.assertFalse(module.auto_install)
        self.assertEqual(module.website, "https://crnd.pro")
        self.assertEqual(module.price, 500.0)
        self.assertEqual(module.currency_id.name, 'EUR')
        self.assertEqual(module.version_count, 3)
        self.assertEqual(module.serie_count, 1)
        self.assertEqual(module.last_version_id, module_version5)

        # Test module serie info updated
        self.assertEqual(module_serie.serie_id.name, '12.0')
        self.assertEqual(module_serie.version_count, 3)
        self.assertEqual(module_serie.last_version_id, module_version5)

        # Assume that we have ported that module to serie 13.0,
        # let's try to notify Yodoo Apps about this version
        module_version6 = self.env['yodoo.module'].create_or_update_module(
            'my_super_module',
            {
                'name': "My Super Module",
                'summary': "This module do cool things.",
                'author': "Center of Research and Development",
                'website': "https://crnd.pro",
                'category': 'Yodoo Apps',
                'version': '13.0.2.1.0',
                'depends': [
                    'crm',
                    'website',
                ],
                'external_dependencies': {
                    'python': [
                        'html2text',
                        'pdf2image',
                    ],
                    'bin': [
                        'pdftoppm',
                    ],
                },
                'installable': True,
                'application': True,
                'license': 'LGPL-3',
                'price': 500,
                'currency': 'EUR',
            },
            no_update=True)

        # Test that new module version was created
        self.assertNotEqual(module_version5, module_version6)

        # Test that version info is correct
        self.assertEqual(module_version6._name, 'yodoo.module.version')
        self.assertEqual(module_version6.system_name, 'my_super_module')
        self.assertEqual(module_version6.name, 'My Super Module')
        self.assertEqual(
            module_version6.summary, 'This module do cool things.')
        self.assertEqual(module_version6.version, '13.0.2.1.0')
        self.assertEqual(module_version6.license_id.code, 'LGPL-3')
        self.assertEqual(len(module_version6.author_ids), 1)
        self.assertEqual(
            module_version6.author_ids.name,
            "Center of Research and Development")
        self.assertTrue(module_version6.application)
        self.assertTrue(module_version6.installable)
        self.assertFalse(module_version6.auto_install)
        self.assertEqual(module_version6.website, "https://crnd.pro")
        self.assertEqual(module_version6.price, 500.0)
        self.assertEqual(module_version6.currency_id.name, 'EUR')
        self.assertEqual(module_version6.serie_major, 13)
        self.assertEqual(module_version6.serie_minor, 0)
        self.assertEqual(module_version6.version_major, 2)
        self.assertEqual(module_version6.version_minor, 1)
        self.assertEqual(module_version6.version_patch, 0)
        self.assertEqual(len(module_version6.dependency_python_ids), 2)
        self.assertIn(
            'html2text', module_version6.dependency_python_ids.mapped('name'))
        self.assertIn(
            'pdf2image', module_version6.dependency_python_ids.mapped('name'))
        self.assertEqual(len(module_version6.dependency_bin_ids), 1)
        self.assertIn(
            'pdftoppm', module_version6.dependency_bin_ids.mapped('name'))
        self.assertFalse(module_version6.version_non_standard)

        # Test that module info was updated
        module.invalidate_cache(ids=module.ids)
        self.assertEqual(module.system_name, 'my_super_module')
        self.assertEqual(module.summary, 'This module do cool things.')
        self.assertEqual(module.version, '13.0.2.1.0')
        self.assertEqual(module.license_id.code, 'LGPL-3')
        self.assertEqual(len(module.author_ids), 1)
        self.assertEqual(
            module.author_ids.name,
            "Center of Research and Development")
        self.assertTrue(module.application)
        self.assertTrue(module.installable)
        self.assertFalse(module.auto_install)
        self.assertEqual(module.website, "https://crnd.pro")
        self.assertEqual(module.price, 500.0)
        self.assertEqual(module.currency_id.name, 'EUR')
        self.assertEqual(len(module.dependency_python_ids), 2)
        self.assertIn(
            'html2text', module.dependency_python_ids.mapped('name'))
        self.assertIn(
            'pdf2image', module.dependency_python_ids.mapped('name'))
        self.assertEqual(len(module.dependency_bin_ids), 1)
        self.assertIn(
            'pdftoppm', module.dependency_bin_ids.mapped('name'))
        self.assertEqual(module.version_count, 4)
        self.assertEqual(module.serie_count, 2)
        self.assertEqual(module.last_version_id, module_version6)

        # Test module serie for version 12 was not updated, but instead
        # new module serie was created
        self.assertEqual(module_serie.serie_id.name, '12.0')
        self.assertEqual(module_serie.version_count, 3)
        self.assertEqual(module_serie.last_version_id, module_version5)
        self.assertNotEqual(module_serie.last_version_id, module_version6)

        # Next new module serie
        module_serie_13 = module_version6.module_serie_id
        self.assertEqual(module_serie_13.serie_id.name, '13.0')
        self.assertEqual(module_serie_13.version_count, 1)
        self.assertEqual(module_serie_13.last_version_id, module_version6)

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
