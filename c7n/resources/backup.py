# Copyright 2019 Capital One Services, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from c7n.manager import resources
from c7n.filters.kms import KmsRelatedFilter
from c7n.query import QueryResourceManager, TypeInfo
from c7n.tags import universal_augment
from c7n.utils import local_session


@resources.register('backup-plan')
class BackupPlan(QueryResourceManager):

    class resource_type(TypeInfo):
        service = 'backup'
        enum_spec = ('list_backup_plans', 'BackupPlansList', None)
        detail_spec = ('get_backup_plan', 'BackupPlanId', 'BackupPlanId', 'BackupPlan')
        id = 'BackupPlanName'
        name = 'BackupPlanId'
        arn = 'BackupPlanArn'
        universal_taggable = object()

    def augment(self, resources):
        super(BackupPlan, self).augment(resources)
        client = local_session(self.session_factory).client('backup')
        results = []
        for r in resources:
            try:
                tags = client.list_tags(ResourceArn=r['BackupPlanArn']).get('Tags', {})
            except client.exceptions.ResourceNotFoundException:
                continue
            r['Tags'] = [{'Key': k, 'Value': v} for k, v in tags.items()]
            results.append(r)

        return results

    def get_resources(self, resource_ids, cache=True):
        client = local_session(self.session_factory).client('backup')
        resources = []

        for rid in resource_ids:
            try:
                resources.append(
                    client.get_backup_plan(BackupPlanId=rid)['BackupPlan'])
            except client.exceptions.ResourceNotFoundException:
                continue
        return resources


@resources.register('backup-vault')
class BackupVault(QueryResourceManager):

    class resource_type(TypeInfo):
        service = 'backup'
        enum_spec = ('list_backup_vaults', 'BackupVaultList', None)
        name = id = 'BackupVaultName'
        arn = 'BackupVaultArn'
        arn_type = 'backup-vault'
        universal_taggable = object()

    def augment(self, resources):
        return universal_augment(self, super(BackupVault, self).augment(resources))

    def get_resources(self, resource_ids, cache=True):
        client = local_session(self.session_factory).client('backup')
        resources = []
        for rid in resource_ids:
            try:
                resources.append(
                    client.describe_backup_vault(BackupVaultName=rid))
            except client.exceptions.ResourceNotFoundException:
                continue
        return self.augment(resources)


@BackupVault.filter_registry.register('kms-key')
class KmsFilter(KmsRelatedFilter):

    RelatedIdsExpression = 'EncryptionKeyArn'
