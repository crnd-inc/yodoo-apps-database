from odoo.tests.common import SavepointCase


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
        self.assertEqual(module_version.summary, 'Test module info')
        self.assertEqual(module_version.version, '12.0.1.2.3')
        self.assertEqual(module_version.license_id.code, 'LGPL-3')
        self.assertFalse(module_version.author_ids, 'LGPL-3')
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

        # Try to updae module with same version
        # (arg 'no_update' is set to False by default)
        module_version2 = self.env['yodoo.module'].create_or_update_module(
            'my_super_module', {
                'name': 'My Super Module',
                'summary': 'Test module info 2',
                'version': '12.0.1.2.3',
            })

        self.assertNotEqual(module_version2, module_version)
        self.assertEqual(module_version._name, 'yodoo.module.version')
        self.assertEqual(module_version.system_name, 'my_super_module')
        self.assertEqual(module_version.summary, 'Test module info 2')
        self.assertEqual(module_version.version, '12.0.1.2.3')
        self.assertEqual(module_version.license_id.code, 'LGPL-3')
        self.assertFalse(module_version.author_ids, 'LGPL-3')
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
        self.assertEqual(module_version._name, 'yodoo.module.version')
        self.assertEqual(module_version.system_name, 'my_super_module')
        self.assertEqual(module_version.summary, 'Test module info 2')
        self.assertEqual(module_version.version, '12.0.1.2.3')
        self.assertEqual(module_version.license_id.code, 'LGPL-3')
        self.assertFalse(module_version.author_ids, 'LGPL-3')
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

        # Try to update module with 'no_update' set to True (same version)
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
        self.assertEqual(module_version._name, 'yodoo.module.version')
        self.assertEqual(module_version.system_name, 'my_super_module')
        self.assertEqual(module_version.summary, 'Test module info 3')
        self.assertEqual(module_version.version, '12.0.1.2.4')
        self.assertEqual(module_version.license_id.code, 'LGPL-3')
        self.assertFalse(module_version.author_ids, 'LGPL-3')
        self.assertFalse(module_version.application)
        self.assertTrue(module_version.installable)
        self.assertFalse(module_version.auto_install)
        self.assertFalse(module_version.website)
        self.assertEqual(module_version.price, 0.0)
        self.assertEqual(module_version.serie_major, 12)
        self.assertEqual(module_version.serie_minor, 0)
        self.assertEqual(module_version.version_major, 1)
        self.assertEqual(module_version.version_minor, 2)
        self.assertEqual(module_version.version_patch, 4)
        self.assertFalse(module_version.version_non_standard)
