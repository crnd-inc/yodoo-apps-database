import contextlib
from unittest.mock import patch

import requests

from odoo import SUPERUSER_ID, exceptions
from odoo.addons.yodoo_apps_git_source.utils import GithubWrapper
from odoo.tests.common import TransactionCase


@contextlib.contextmanager
def _same_transaction(self, lock=False, no_raise=False):
    yield self


class TestSchedulerGithubAuth(TransactionCase):
    """ scheduler_sync_git_sources must not enqueue sync tasks for GitHub
        sources while GitHub rejects the configured credentials.
    """

    def setUp(self):
        super().setUp()
        self.Source = self.env['yodoo.git.source']
        self.Task = self.env['generic.task.queue.task']
        self.Source.search([]).write({'enable_sync': False})
        self.github_source = self.Source.create({
            'name': 'Test GitHub Source',
            'source_type': 'github',
            'github_owner': 'test-owner',
            'github_repository': 'test-repo',
            'enable_sync': True,
        })
        self.generic_source = self.Source.create({
            'name': 'Test Generic Source',
            'source_type': 'generic',
            'generic_git_scheme': 'https',
            'generic_git_host': 'example.com',
            'generic_git_path': 'test/repo.git',
            'enable_sync': True,
        })

    def _run_scheduler(self, connect_side_effect=None):
        with patch.object(
            type(self.Source), '_in_new_transaction', _same_transaction,
        ), patch.object(
            GithubWrapper, 'connect', side_effect=connect_side_effect,
        ):
            self.Source.scheduler_sync_git_sources()

    def _task_for(self, source):
        return self.Task.search([
            ('unique_key', '=', 'source_sync:%d' % source.id)])

    def test_auth_failure_skips_github_sources(self):
        self._run_scheduler(exceptions.UserError('Cannot authenticate'))

        self.assertFalse(self._task_for(self.github_source))
        self.assertTrue(self._task_for(self.generic_source))

    def test_network_failure_skips_github_sources(self):
        self._run_scheduler(requests.ConnectionError('Connection refused'))

        self.assertFalse(self._task_for(self.github_source))
        self.assertTrue(self._task_for(self.generic_source))

    def test_auth_failure_logs_single_warning(self):
        with self.assertLogs(
            'odoo.addons.yodoo_apps_website.models.yodoo_git_source',
            level='WARNING',
        ) as logs:
            self._run_scheduler(exceptions.UserError('Cannot authenticate'))

        self.assertEqual(len(logs.records), 1)
        self.assertIn(
            'GitHub is unavailable or rejected the token, '
            'GitHub sources are skipped: Cannot authenticate',
            logs.output[0])

    def test_auth_ok_syncs_all_sources(self):
        self._run_scheduler()

        self.assertTrue(self._task_for(self.github_source))
        self.assertTrue(self._task_for(self.generic_source))

    def test_enqueue_limit_param_caps_selection(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'yodoo_apps_website.scheduler_enqueue_limit', '1')

        self._run_scheduler()

        self.assertEqual(
            len(self._task_for(self.github_source)
                | self._task_for(self.generic_source)), 1)


class TestActionSyncAccess(TransactionCase):
    """ action_sync reuses an active task even when another user created
        it; a user who cannot read that task must get a notification
        instead of an action opening its form.
    """

    def setUp(self):
        super().setUp()
        self.user = self.env['res.users'].create({
            'name': 'Apps Manager Without Task Queue',
            'login': 'apps_manager_no_tq',
            'groups_id': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref(
                    'yodoo_apps_database.group_yodoo_apps_manager').id,
            ])],
        })
        self.source = self.env['yodoo.git.source'].create({
            'name': 'Test Source Access',
        })

    def test_foreign_task_returns_notification(self):
        self.source.with_user(SUPERUSER_ID).action_sync()

        action = self.source.with_user(self.user).action_sync()

        self.assertEqual(action['type'], 'ir.actions.client')
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(
            action['params']['message'], 'Synchronization is already running')

    def test_own_task_returns_form_action(self):
        action = self.source.with_user(self.user).action_sync()

        task = self.env['generic.task.queue.task'].search([
            ('unique_key', '=', 'source_sync:%d' % self.source.id)])
        self.assertEqual(task.create_uid, self.user)
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_id'], task.id)
