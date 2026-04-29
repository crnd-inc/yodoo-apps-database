Yodoo Apps Website
==================

Display the Odoo modules catalog on a website.

This module wires ``yodoo_apps_database`` and ``yodoo_apps_git_source``
into a public website front-end:

* Browse a catalog of modules with filters by category, series, and
  author.
* Module detail pages with description, screenshots, dependencies and
  per-series version badges (URL: ``/modules/<system_name>``).
* Background sync of git sources via ``generic_task_queue``: a parent
  task fans out per-branch children, with the description fetch and
  ``odoo_requirements.txt`` reconciliation done sequentially in the
  finalize step.

Visibility flags
----------------

* ``yodoo.module.is_published`` (default ``True``) — when ``False``,
  the module is hidden everywhere on the public website.
* ``yodoo.module.category.is_listed_on_website`` /
  ``yodoo.module.author.is_listed_on_website`` — soft hide from the
  list filter sidebar without 404-ing direct module URLs.

Background sync
---------------

Triggering ``Sync`` on a ``yodoo.git.source`` enqueues a parent
``yodoo_apps_website.source_sync`` task on the default channel. The
parent uses ``unique_key='source_sync:<id>'`` to collapse concurrent
triggers (manual click, ``scheduler_sync_git_sources`` cron, queue
retry) into a single active task per source, preventing finalize-time
``SerializationFailure`` on ``yodoo_git_source.last_time_synced``.
