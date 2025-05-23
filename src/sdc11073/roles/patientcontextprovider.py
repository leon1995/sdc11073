"""Implementation of patient provider functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .contextprovider import GenericContextProvider

if TYPE_CHECKING:
    from sdc11073.mdib.descriptorcontainers import AbstractOperationDescriptorProtocol
    from sdc11073.mdib.mdibprotocol import ProviderMdibProtocol
    from sdc11073.provider.operations import OperationDefinitionBase
    from sdc11073.provider.sco import AbstractScoOperationsRegistry

    from .providerbase import OperationClassGetter


class GenericPatientContextProvider(GenericContextProvider):
    """Example for handling of SetContextState operations.

    This Provider instantiates a SetContextState operation if the operation target is a PatientContextDescriptor.
    Nothing is added to the mdib. If the mdib does not contain these operations, the functionality is not available.
    """

    def __init__(self, mdib: ProviderMdibProtocol, log_prefix: str | None):
        super().__init__(mdib, log_prefix=log_prefix)
        self._patient_context_entity = None
        self._set_patient_context_operations = []

    def init_operations(self, sco: AbstractScoOperationsRegistry):
        """Find the PatientContextDescriptor."""
        super().init_operations(sco)
        pm_names = self._mdib.data_model.pm_names
        entities = self._mdib.entities.by_node_type(pm_names.PatientContextDescriptor)
        if len(entities) == 1:
            self._patient_context_entity = entities[0]

    def make_operation_instance(self,
                                operation_descriptor_container: AbstractOperationDescriptorProtocol,
                                operation_cls_getter: OperationClassGetter) -> OperationDefinitionBase | None:
        """Add Operation Handler if operation target is the previously found PatientContextDescriptor."""
        if self._patient_context_entity is not None and \
                operation_descriptor_container.OperationTarget == self._patient_context_entity.handle:
            pc_operation = self._mk_operation_from_operation_descriptor(operation_descriptor_container,
                                                                        operation_cls_getter,
                                                                        operation_handler=self._set_context_state)
            self._set_patient_context_operations.append(pc_operation)
            return pc_operation
        return None


class PatientContextProvider(GenericPatientContextProvider):
    """PatientContextProvider adds operations to mdib if they do not exist."""

    def make_missing_operations(self, sco: AbstractScoOperationsRegistry) -> list[OperationDefinitionBase]:
        """Add operation to mdib if it does not exist."""
        pm_names = self._mdib.data_model.pm_names
        ops = []
        operation_cls_getter = sco.operation_cls_getter
        if self._patient_context_entity is not None  and not self._set_patient_context_operations:
            op_cls = operation_cls_getter(pm_names.SetContextStateOperationDescriptor)
            pc_operation = op_cls('opSetPatCtx',
                                  self._patient_context_entity.handle,
                                  self._set_context_state,
                                  coded_value=None)
            ops.append(pc_operation)
        return ops
