# Copyright (c) 2012 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_log import log as logging

import nova.conf
from nova.i18n import _LW
from nova.scheduler import filters
from nova.scheduler.filters import utils
from nova import objects
from nova import context

LOG = logging.getLogger(__name__)

CONF = nova.conf.CONF


class NumProjectsFilter(filters.BaseHostFilter):
    """Filter out hosts with too many projects."""

    def _get_max_projects_per_host(self):
        return CONF.filter_scheduler.max_projects_per_host

    def host_passes(self, host_state, spec_obj):
        max_projects = self._get_max_projects_per_host()

        LOG.debug("DEBUG: NumProjects filter called. "
                  "spec_obj='%s' host_state='%s'", spec_obj, host_state)
        LOG.debug("DEBUG: host_state.host='%s' project_id='%s'",
                  host_state.host, spec_obj.project_id)

        admin = context.get_admin_context()
        filters = {"host": [host_state.host], "deleted": False}
        instances = objects.InstanceList().get_by_filters(admin, filters)
        LOG.debug("DEBUG: instances='%s'", instances)

        projects = set()
        for instance in instances:
            LOG.debug("DEBUG: uuid='%s', project_id='%s'",
                      instance['uuid'], instance['project_id'])
            projects.add(instance['project_id'])

        if spec_obj.project_id in projects:
            # FIXME(thatsdone):
            # This 'True' allows to run multiple VMs on a sigle host.
            passes = True
        elif len(projects) >= max_projects:
            passes = False
        else:
            passes = True

        if not passes:
            LOG.debug("%(host_state)s fails num_projects check: "
                      "Max projects per host is set to %(max_projects)s",
                      {'host_state': host_state,
                       'max_projects': max_projects})
        return passes


class AggregateNumProjectsFilter(NumProjectsFilter):
    """AggregateNumProjectsFilter with per-aggregate the max num projects.

    Fall back to global max_num_projects_per_host if no per-aggregate setting
    found.
    """

    def _get_max_projects_per_host(self, host_state, spec_obj):
        max_projects_per_host = CONF.filter_scheduler.max_projects_per_host

        aggregate_vals = utils.aggregate_values_from_key(
            host_state,
            'max_projects_per_host')
        try:
            value = utils.validate_num_values(
                aggregate_vals, max_projects_per_host, cast_to=int)
        except ValueError as e:
            LOG.warning(_LW("Could not decode max_projects_per_host: '%s'"),
                        e)
            value = max_projects_per_host

        return value
