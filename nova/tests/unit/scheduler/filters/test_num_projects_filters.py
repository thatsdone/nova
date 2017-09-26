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

import mock

from nova import objects
from nova.scheduler.filters import num_projects_filter
from nova import test
from nova.tests.unit.scheduler import fakes
from nova.tests import uuidsentinel as uuids


class TestNumProjectsFilter(test.NoDBTestCase):

    @mock.patch('nova.objects.instance.InstanceList.get_by_filters')
    def test_filter_num_projects_passes(self, inst_list_mock):
        self.flags(max_projects_per_host=2, group='filter_scheduler')
        self.filt_cls = num_projects_filter.NumProjectsFilter()
        host = fakes.FakeHostState('host1', 'node1', {})
        inst1 = objects.Instance(uuid=uuids.inst1, project_id=uuids.proj1)
        spec_obj = objects.RequestSpec()
        spec_obj.project_id = uuids.proj2
        inst_list_mock.return_value = objects.InstanceList()
        inst_list_mock.return_value.objects.append(inst1)
        self.assertTrue(self.filt_cls.host_passes(host, spec_obj))

    @mock.patch('nova.objects.instance.InstanceList.get_by_filters')
    def test_filter_num_projects_fails(self, inst_list_mock):
        self.flags(max_projects_per_host=2, group='filter_scheduler')
        self.filt_cls = num_projects_filter.NumProjectsFilter()
        host = fakes.FakeHostState('host1', 'node1', {})
        inst1 = objects.Instance(uuid=uuids.inst1, project_id=uuids.proj1)
        inst2 = objects.Instance(uuid=uuids.inst2, project_id=uuids.proj2)
        spec_obj = objects.RequestSpec()
        spec_obj.project_id = uuids.proj3
        inst_list_mock.return_value = objects.InstanceList()
        inst_list_mock.return_value.objects.append(inst1)
        inst_list_mock.return_value.objects.append(inst2)
        self.assertFalse(self.filt_cls.host_passes(host, spec_obj))

    @mock.patch('nova.scheduler.filters.utils.aggregate_values_from_key')
    @mock.patch('nova.objects.instance.InstanceList.get_by_filters')
    def test_filter_aggregate_num_projects_pass(self, inst_mock, agg_mock):
        self.flags(max_projects_per_host=2, group='filter_scheduler')
        self.filt_cls = num_projects_filter.AggregateNumProjectsFilter()
        host = fakes.FakeHostState('host1', 'node1', {})
        inst1 = objects.Instance(uuid=uuids.inst1, project_id=uuids.proj1)
        spec_obj = objects.RequestSpec()
        spec_obj.project_id = uuids.proj2
        inst_mock.return_value = objects.InstanceList()
        inst_mock.return_value.objects.append(inst1)
        agg_mock.return_value = None
        # No aggregate defined for that host.
        self.assertTrue(self.filt_cls.host_passes(host, spec_obj))
        #agg_mock.assert_called_once_with(host, 'max_projects_per_host')
        agg_mock.return_value = '2'
        # Aggregate defined for that host.
        self.assertTrue(self.filt_cls.host_passes(host, spec_obj))

    @mock.patch('nova.scheduler.filters.utils.aggregate_values_from_key')
    @mock.patch('nova.objects.instance.InstanceList.get_by_filters')
    def test_filter_aggregate_num_projects_fail(self, inst_mock, agg_mock):
        self.flags(max_projects_per_host=2, group='filter_scheduler')
        self.filt_cls = num_projects_filter.AggregateNumProjectsFilter()
        host = fakes.FakeHostState('host1', 'node1', {})
        inst1 = objects.Instance(uuid=uuids.inst1, project_id=uuids.proj1)
        inst2 = objects.Instance(uuid=uuids.inst2, project_id=uuids.proj2)
        spec_obj = objects.RequestSpec()
        spec_obj.project_id = uuids.proj3
        inst_mock.return_value = objects.InstanceList()
        inst_mock.return_value.objects.append(inst1)
        inst_mock.return_value.objects.append(inst2)
        #agg_mock.return_value = set([])
        # No aggregate defined for that host.
        #self.assertFalse(self.filt_cls.host_passes(host, spec_obj))
        #agg_mock.assert_called_once_with(host, 'max_projects_per_host')
        agg_mock.return_value = '2'
        # Aggregate defined for that host.
        self.assertFalse(self.filt_cls.host_passes(host, spec_obj))
