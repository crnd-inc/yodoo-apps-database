import datetime
from unittest import mock

from odoo import exceptions, fields
from odoo.addons.yodoo_apps_git_source.utils import GithubWrapper
from odoo.tests.common import TransactionCase, tagged

LIMIT_PARAM = 'yodoo_apps_website.scheduler_enqueue_limit'


@tagged('post_install', '-at_install')
class TestSchedulerQueue(TransactionCase):
    """ Scheduler only enqueues sync tasks, never more than the configured
        number per run, and never-synced sources are served first.
    """

    def setUp(self):
        super().setUp()
        self.registry.enter_test_mode(self.cr)
        self.addCleanup(self.registry.leave_test_mode)
        self.Source = self.env['yodoo.git.source']
        self.Task = self.env['generic.task.queue.task']
        self.Source.search([]).write({'enable_sync': False})
        self.env['ir.config_parameter'].sudo().set_param(LIMIT_PARAM, '2')

        patcher = mock.patch.object(
            type(self.Source), '_action_sync',
            side_effect=AssertionError('scheduler must not sync inline'))
        self.direct_sync = patcher.start()
        self.addCleanup(patcher.stop)

    def _create_source(self, name, source_type='generic',
                       last_time_synced=False):
        vals = {
            'name': name,
            'source_type': source_type,
            'last_time_synced': last_time_synced,
            'enable_sync': True,
        }
        if source_type == 'github':
            vals.update(github_owner='acme-queue', github_repository=name)
        else:
            vals.update(
                generic_git_scheme='https',
                generic_git_host='example.com',
                generic_git_path='queue/%s.git' % name)
        return self.Source.create(vals)

    def _days_ago(self, days):
        return fields.Datetime.now() - datetime.timedelta(days=days)

    def _tasks_for(self, sources):
        return self.Task.search([
            ('unique_key', 'in', [
                'source_sync:%d' % rec_id for rec_id in sources.ids])])

    def _run_scheduler(self, connect_side_effect=None):
        with mock.patch.object(
            GithubWrapper, 'connect', side_effect=connect_side_effect,
        ):
            self.Source.scheduler_sync_git_sources()

    def test_enqueues_at_most_limit_tasks(self):
        sources = self.Source
        for idx in range(3):
            sources |= self._create_source('cap_%d' % idx)

        self._run_scheduler()

        self.assertEqual(len(self._tasks_for(sources)), 2)
        self.direct_sync.assert_not_called()

    def test_enqueues_all_when_fewer_than_limit(self):
        source = self._create_source('single')

        self._run_scheduler()

        self.assertEqual(len(self._tasks_for(source)), 1)
        self.direct_sync.assert_not_called()

    def test_next_run_skips_fresh_attempts(self):
        sources = self.Source
        for idx in range(3):
            sources |= self._create_source('rerun_%d' % idx)

        self._run_scheduler()
        first = self.Source.search([('last_sync_attempt', '!=', False)])
        self.assertEqual(len(first), 2)

        self._run_scheduler()
        self.assertEqual(len(self._tasks_for(sources)), 3)
        self.assertEqual(
            self.Source.search_count([('last_sync_attempt', '!=', False)]), 3)

        outdated = self._days_ago(2)
        sources.write({'last_sync_attempt': outdated})
        self._run_scheduler()
        self.assertEqual(
            self.Source.search_count([('last_sync_attempt', '>', outdated)]),
            2)
        tasks = self._tasks_for(sources)
        self.assertEqual(len(tasks), 3)
        self.assertEqual(len(set(tasks.mapped('unique_key'))), 3)

    def test_github_failure_excludes_github_keeps_order(self):
        github = self._create_source('gh_down', source_type='github')
        stale = self._create_source(
            'stale_gen', last_time_synced=self._days_ago(5))
        never = self._create_source('never_gen')
        self.env['ir.config_parameter'].sudo().set_param(LIMIT_PARAM, '1')

        self._run_scheduler(exceptions.UserError('Cannot authenticate'))
        self.assertTrue(self._tasks_for(never))
        self.assertFalse(self._tasks_for(stale))

        self._run_scheduler(exceptions.UserError('Cannot authenticate'))
        self.assertTrue(self._tasks_for(stale))

        self._run_scheduler(exceptions.UserError('Cannot authenticate'))
        self.assertFalse(self._tasks_for(github))
        self.assertFalse(github.last_sync_attempt)

    def test_github_connect_called_once_per_run(self):
        for idx in range(3):
            self._create_source('once_%d' % idx)

        with mock.patch.object(GithubWrapper, 'connect') as connect:
            self.Source.scheduler_sync_git_sources()

        connect.assert_called_once()

    def test_limit_default_and_invalid_values(self):
        Param = self.env['ir.config_parameter'].sudo()
        Param.set_param(LIMIT_PARAM, '3')
        self.assertEqual(self.Source._scheduler_sync_git_sources_limit(), 3)

        for value in ('abc', '0', '-5', ''):
            Param.set_param(LIMIT_PARAM, value)
            self.assertEqual(
                self.Source._scheduler_sync_git_sources_limit(), 10, value)

        Param.search([('key', '=', LIMIT_PARAM)]).unlink()
        self.assertEqual(self.Source._scheduler_sync_git_sources_limit(), 10)
