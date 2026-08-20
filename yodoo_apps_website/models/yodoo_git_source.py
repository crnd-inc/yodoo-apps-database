import logging

from odoo import _, fields, models

from ..tools.odoo_requirements import parse_odoo_requirements

_logger = logging.getLogger(__name__)

try:
    import gitlab as gitlab_lib
except (ImportError, IOError):
    gitlab_lib = None

try:
    import github as github_lib
except (ImportError, IOError):
    github_lib = None

SOURCE_SYNC_TASK_TYPE = 'yodoo_apps_website.source_sync'


class YodooGitSource(models.Model):
    _inherit = 'yodoo.git.source'

    # Restores the constant removed from BaseModel in Odoo 18; referenced
    # by generic.mixin.refresh.view._auto_refresh_view_on_field_changes_system.
    CONCURRENCY_CHECK_FIELD = '__last_update'

    last_sync_task_id = fields.Many2one(
        comodel_name='generic.task.queue.task',
        string='Last Sync Task',
        readonly=True,
        copy=False,
        help='Background task record of the most recent Sync click.',
    )
    # These related fields exist so the gtq_task_auto_refresh widget's
    # state_field/progress_field options can name a plain field on this
    # record: task_auto_refresh_field.js reads record.data[key] literally
    # and does not resolve dotted paths like "last_sync_task_id.state".
    last_sync_task_state = fields.Selection(
        related='last_sync_task_id.state',
        string='Last Sync Task State',
    )
    last_sync_task_progress = fields.Integer(
        related='last_sync_task_id.progress',
        string='Last Sync Task Progress',
    )

    def action_sync(self):
        """ Override upstream: enqueue a background task instead of
            running sync inline in the HTTP request.

            ``unique_key`` collapses concurrent triggers (manual click +
            scheduler_sync_git_sources cron + queue retry) into one active
            parent task per source — without it, multiple parents would
            race on yodoo_git_source.last_time_synced in
            _g_task__finalize_sync, returning SerializationFailure and
            poisoning the worker connection pool.
        """
        Task = self.env['generic.task.queue.task'].sudo()
        for source in self:
            task = Task.create_task(
                SOURCE_SYNC_TASK_TYPE,
                name=_('Sync %s') % source.display_name,
                params={'source_id': source.id},
                unique_key='source_sync:%d' % source.id,
                on_conflict='reuse-running',
            )
            source.sudo().last_sync_task_id = task
        if len(self) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'generic.task.queue.task',
                'res_id': self.last_sync_task_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'title': _('Sync enqueued'),
                'message': _(
                    '%s source(s) queued for background sync.') % len(self),
                'sticky': False,
            },
        }

    def _g_task__prepare_sync(self, branch_names=None):
        """ Connect to git, discover branches, write connection metadata.
            Returns IDs of scannable branches to fan out into child tasks. """
        self.ensure_one()
        if self.source_type == 'github':
            return self._g_task__prepare_github(branch_names)
        if self.source_type == 'crnd':
            return self._g_task__prepare_gitlab(branch_names)
        # generic git: no per-branch parallelism available
        self._action_sync(branch_names=branch_names)
        return []

    def _g_task__prepare_github(self, branch_names=None):
        from odoo.addons.yodoo_apps_git_source.utils import GithubWrapper
        git = GithubWrapper(self.env)
        git.connect()
        try:
            git.open_repo(self.github_owner, self.github_repository)
        except github_lib.GithubException:
            self.add_tag('error-no-repo')
            return []
        self.remove_tag('error-no-repo')
        self._sync_git_source_branches(git)
        self.write({
            'git_url': git.get_repo_url(),
            'github_is_private': git.gh_repo.private,
        })
        return self._g_task__scannable_branch_ids(branch_names)

    def _g_task__prepare_gitlab(self, branch_names=None):
        from odoo.addons.yodoo_apps_git_source.utils import GitlabWrapper
        git = GitlabWrapper(self.env)
        git.connect()
        try:
            repo = git.open_repo(self.gitlab_project_id)
        except gitlab_lib.exceptions.GitlabGetError:
            self.add_tag('error-no-repo')
            return []
        self.remove_tag('error-no-repo')
        self._sync_git_source_branches(git)
        self.write({
            'git_url': git.get_repo_url(),
            'gitlab_project_path': repo.path_with_namespace,
        })
        return self._g_task__scannable_branch_ids(branch_names)

    def _g_task__scannable_branch_ids(self, branch_names=None):
        scannable_names = self._get_scannable_branches(branch_names)
        return self.git_branch_ids.filtered(
            lambda b: b.name in scannable_names).ids

    def _g_task__sync_one_branch(self, branch):
        """ Per-branch worker: sync modules + fetch descriptions. """
        self.ensure_one()
        if self.source_type == 'github':
            self._g_task__sync_github_branch(branch)
        elif self.source_type == 'crnd':
            self._g_task__sync_gitlab_branch(branch)

    def _g_task__sync_github_branch(self, branch):
        from odoo.addons.yodoo_apps_git_source.utils import GithubWrapper
        git = GithubWrapper(self.env)
        git.connect()
        git.open_repo(self.github_owner, self.github_repository)
        modules = dict(git.iter_modules(branch.name))
        branch._sync_modules(modules)

    def _g_task__sync_gitlab_branch(self, branch):
        from odoo.addons.yodoo_apps_git_source.utils import GitlabWrapper
        git = GitlabWrapper(self.env)
        git.connect()
        git.open_repo(self.gitlab_project_id)
        modules = dict(git.iter_modules(branch.name))
        branch._sync_modules(modules)

    def _g_task__finalize_sync(self):
        """ Called from parent task's on_all_children_done hook.

            Description fetching iterates all branches sequentially here
            to avoid `yodoo.module` row-write contention between parallel
            branch tasks (a module often exists on several branches and
            every branch would race on the same description/icon/cover).
        """
        self.ensure_one()
        if self.source_type == 'github' and (
                self.github_owner and self.github_repository):
            self._yodoo_apps_website_fetch_descriptions_github()
            self._yodoo_apps_website_sync_odoo_requirements_github()
        elif self.source_type == 'crnd' and self.gitlab_project_path:
            self._yodoo_apps_website_fetch_descriptions_gitlab()
            self._yodoo_apps_website_sync_odoo_requirements_gitlab()
        self.write({'last_time_synced': fields.Datetime.now()})

    def _action_sync_gitlab(self, branch_names=None):
        super()._action_sync_gitlab(branch_names=branch_names)
        if not self.gitlab_project_path:
            return
        self._yodoo_apps_website_fetch_descriptions_gitlab(branch_names)
        self._yodoo_apps_website_sync_odoo_requirements_gitlab()

    def _action_sync_github(self, branch_names=None):
        super()._action_sync_github(branch_names=branch_names)
        if not self.github_owner or not self.github_repository:
            return
        self._yodoo_apps_website_fetch_descriptions_github(branch_names)
        self._yodoo_apps_website_sync_odoo_requirements_github()

    def _yodoo_apps_website_iter_branches_oldest_first(
            self, branch_names=None):
        # Default _order on branches is version DESC; iterating in that order
        # makes the OLDEST branch the last writer for module description /
        # icon / cover, which leaves stale assets after a series upgrade.
        # Reverse to oldest-first so the newest branch wins; older branches
        # serve as fallback when newer ones lack static/description files.
        branches = self.git_branch_ids.filtered(
            lambda b: b.scan and b.is_standard)
        if branch_names:
            branches = branches.filtered(lambda b: b.name in branch_names)
        return branches.sorted(
            key=lambda b: (b.yodoo_serie_major, b.yodoo_serie_minor))

    def _yodoo_apps_website_fetch_descriptions_gitlab(self, branch_names=None):
        from odoo.addons.yodoo_apps_git_source.utils import GitlabWrapper
        try:
            git = GitlabWrapper(self.env)
            git.connect()
            git.open_repo(self.gitlab_project_id)
        except Exception:
            _logger.warning(
                'Cannot connect to GitLab for description fetch: %s',
                self.name)
            return

        for branch in self._yodoo_apps_website_iter_branches_oldest_first(
                branch_names):
            branch._yodoo_apps_website_fetch_branch_descriptions_gitlab(
                git, self.gitlab_project_path)

    def _yodoo_apps_website_fetch_descriptions_github(self, branch_names=None):
        from odoo.addons.yodoo_apps_git_source.utils import GithubWrapper
        try:
            git = GithubWrapper(self.env)
            git.connect()
            git.open_repo(self.github_owner, self.github_repository)
        except Exception:
            _logger.warning(
                'Cannot connect to GitHub for description fetch: %s',
                self.name)
            return

        for branch in self._yodoo_apps_website_iter_branches_oldest_first(
                branch_names):
            branch._yodoo_apps_website_fetch_branch_descriptions_github(
                git)

    def _yodoo_apps_website_sync_odoo_requirements_gitlab(self):
        from odoo.addons.yodoo_apps_git_source.utils import GitlabWrapper
        try:
            git = GitlabWrapper(self.env)
            git.connect()
            git.open_repo(self.gitlab_project_id)
        except Exception:
            return

        branch = self.git_branch_ids.filtered(
            lambda b: b.scan and b.is_standard)[:1]
        if not branch:
            return

        try:
            f = git.gl_project.files.get(
                ref=branch.name, file_path='odoo_requirements.txt')
            content = f.decode().decode('utf-8')
        except Exception:
            return

        requirements = parse_odoo_requirements(content)
        self._yodoo_apps_website_ensure_git_sources(
            requirements, git.connection)

    def _yodoo_apps_website_sync_odoo_requirements_github(self):
        from odoo.addons.yodoo_apps_git_source.utils import GithubWrapper
        try:
            git = GithubWrapper(self.env)
            git.connect()
            git.open_repo(self.github_owner, self.github_repository)
        except Exception:
            return

        branch = self.git_branch_ids.filtered(
            lambda b: b.scan and b.is_standard)[:1]
        if not branch:
            return

        try:
            file_content = git.gh_repo.get_contents(
                'odoo_requirements.txt', ref=branch.name)
            content = file_content.decoded_content.decode('utf-8')
        except Exception:
            return

        requirements = parse_odoo_requirements(content)
        self._yodoo_apps_website_ensure_git_sources(requirements)

    def _yodoo_apps_website_ensure_git_sources(
            self, requirements, gl_connection=None):
        GitSource = self.env['yodoo.git.source'].sudo()
        for req in requirements:
            try:
                if req['type'] == 'github':
                    self._yodoo_apps_website_ensure_github_source(
                        GitSource, req['owner'], req['repo'])
                elif req['type'] == 'gitlab' and gl_connection:
                    self._yodoo_apps_website_ensure_gitlab_source(
                        GitSource, gl_connection, req['path'])
            except Exception:
                _logger.warning(
                    'Cannot create git source for requirement: %s',
                    req, exc_info=True)

    def _yodoo_apps_website_ensure_github_source(
            self, GitSource, owner, repo):
        existing = GitSource.search([
            ('source_type', '=', 'github'),
            ('github_owner', '=', owner),
            ('github_repository', '=', repo),
        ], limit=1)
        if existing:
            return existing

        _logger.info(
            'Auto-creating GitHub git source: %s/%s', owner, repo)
        return GitSource.create({
            'name': '%s/%s' % (owner, repo),
            'source_type': 'github',
            'github_owner': owner,
            'github_repository': repo,
            'enable_sync': True,
        })

    def _yodoo_apps_website_ensure_gitlab_source(
            self, GitSource, gl_connection, path):
        existing = GitSource.search([
            ('source_type', '=', 'crnd'),
            ('gitlab_project_path', '=', path),
        ], limit=1)
        if existing:
            return existing

        try:
            project = gl_connection.projects.get(path)
        except Exception:
            _logger.warning(
                'GitLab project not found: %s', path)
            return GitSource

        existing_by_id = GitSource.search([
            ('source_type', '=', 'crnd'),
            ('gitlab_project_id', '=', project.id),
        ], limit=1)
        if existing_by_id:
            return existing_by_id

        _logger.info(
            'Auto-creating GitLab git source: %s (ID: %s)',
            path, project.id)
        return GitSource.create({
            'name': project.attributes.get('name', path),
            'source_type': 'crnd',
            'gitlab_project_id': project.id,
            'gitlab_project_path': project.path_with_namespace,
            'enable_sync': True,
        })
