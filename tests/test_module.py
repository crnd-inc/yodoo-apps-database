from odoo.tests.common import SavepointCase


class TestModule(SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestModule, cls).setUpClass()

        cls.module_account = cls.env.ref(
            'yodoo_apps_database.odoo_community_module__base')

    def test_module_active(self):
        self.assertTrue(self.module_account.active)
