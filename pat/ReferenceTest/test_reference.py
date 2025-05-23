"""Periodic updates of metrics and alert states."""

import os
import threading
import time
import traceback
import unittest
from collections import defaultdict
from concurrent import futures
from decimal import Decimal

from pat.ReferenceTest import reference_provider
from sdc11073 import observableproperties
from sdc11073.consumer import SdcConsumer
from sdc11073.definitions_sdc import SdcV1Definitions
from sdc11073.mdib import ConsumerMdib
from sdc11073.wsdiscovery import ScopesType, WSDiscovery
from sdc11073.xml_types import msg_types
from sdc11073.xml_types import pm_qnames as pm


class DeviceActivity(threading.Thread):
    """Feed the device with periodic updates of metrics and alert states."""

    daemon = True

    def __init__(self, device):  # noqa: ANN001
        super().__init__()
        self.device = device
        self.running = None

    def run(self):  # noqa: C901, D102, PLR0912
        self.running = True
        descs = list(self.device.mdib.descriptions.objects)
        descs.sort(key=lambda x: x.Handle)
        metric = None
        alertCondition = None  # noqa: N806
        stringOperation = None  # noqa: N806
        valueOperation = None  # noqa: N806
        for oneContainer in descs:  # noqa: N806
            if oneContainer.Handle == 'numeric.ch1.vmd0':
                metric = oneContainer
            if oneContainer.Handle == 'ac0.mds0':
                alertCondition = oneContainer  # noqa: N806
            if oneContainer.Handle == 'numeric.ch0.vmd1_sco_0':
                valueOperation = oneContainer  # noqa: N806
            if oneContainer.Handle == 'enumstring.ch0.vmd1_sco_0':
                stringOperation = oneContainer  # noqa: N806
        with self.device.mdib.metric_state_transaction() as mgr:
            state = mgr.get_state(valueOperation.OperationTarget)
            if not state.MetricValue:
                state.mk_metric_value()
            state = mgr.get_state(stringOperation.OperationTarget)
            if not state.MetricValue:
                state.mk_metric_value()
        print('DeviceActivity running...')
        try:
            currentValue = Decimal(0)  # noqa: N806
            while True:
                if metric:
                    with self.device.mdib.metric_state_transaction() as mgr:
                        state = mgr.get_state(metric.Handle)
                        if not state.MetricValue:
                            state.mk_metric_value()
                        state.MetricValue.Value = currentValue
                        print(f'set metric to {currentValue}')
                        currentValue += 1  # noqa: N806
                else:
                    print('Metric not found in MDIB!')
                if alertCondition:
                    with self.device.mdib.alert_state_transaction() as mgr:
                        state = mgr.get_state(alertCondition.Handle)
                        state.Presence = not state.Presence
                        print(f'set alertstate presence to {state.Presence}')
                else:
                    print('Alert not found in MDIB')
                for _ in range(2):
                    if not self.running:
                        print('DeviceActivity stopped.')
                        return
                    time.sleep(1)
        except:  # noqa: E722
            print(traceback.format_exc())
        print('DeviceActivity stopped.')


class Test_Reference(unittest.TestCase):  # noqa: N801
    """Plugfest Reference tests."""

    def setUp(self) -> None:  # noqa: D102
        # tests fill this list with what they create, teardown cleans up after them.
        self.my_clients = []
        # define how the provider is published on the network and how the client tries to detect the device
        self.loc = reference_provider.get_location()
        self.ip = reference_provider.get_network_adapter().ip

    def tearDown(self) -> None:  # noqa: D102
        for cl in self.my_clients:
            print(f'stopping {cl}')
            cl.stop_all()

    def test_with_created_device(self):
        """The test creates its own device and runs the tests against it.

        A WsDiscovery instance is needed to publish devices on the network.
        In this case we want to publish them only on localhost 127.0.0.1.
        """
        self.provider_discovery = WSDiscovery(self.ip)
        self.provider_discovery.start()
        self.provider = reference_provider.create_reference_provider(ws_discovery=self.provider_discovery)
        reference_provider.set_reference_data(self.provider, loc=self.loc)
        self.device_activity = DeviceActivity(self.provider)
        self.device_activity.start()
        try:
            self._runtest_client_connects()
        finally:
            self.provider_discovery.stop()
            self.device_activity.running = False
            self.device_activity.join()

    @unittest.skipUnless(
        os.getenv('EXTERNAL_DEVICE_RUNNING') == 'true',
        reason='Environment variable EXTERNAL_DEVICE_RUNNING is not "true", '
        'indicating that no external SDC Provider was started to test against.',
    )
    def test_client_connects(self):  # noqa: D102
        # This test needs an externally started SDC Provider to run the tests against.
        print('Start unittest "test_client_connects" against externally started SDC Provider.')
        self._runtest_client_connects()

    def _runtest_client_connects(self):
        """Sequence of client actions."""
        errors = []
        passed = []
        client_discovery = WSDiscovery(self.ip)
        client_discovery.start()

        print(f'looking for device with scope {self.loc.scope_string}')
        services = client_discovery.search_services(
            types=SdcV1Definitions.MedicalDeviceTypesFilter,
            scopes=ScopesType(self.loc.scope_string),
        )
        print('found {} services {}'.format(len(services), ', '.join([s.epr for s in services])))
        client_discovery.stop()
        for s in services:
            print(s.epr)
        self.assertEqual(len(services), 1)  # noqa: PT009
        my_service = services[0]
        print('Test step 1 successful: device discovered')

        ssl_context_container = reference_provider.get_ssl_context()
        print(f'Used ssl context: {ssl_context_container}')

        print('Test step 2: connect to device...')
        client = SdcConsumer.from_wsd_service(my_service, ssl_context_container=ssl_context_container)
        self.my_clients.append(client)
        client.start_all()
        self.assertTrue(client.is_connected)  # noqa: PT009
        print('Test step 2 successful: connected to device')

        print('Test step 3&4: get mdib and subscribe...')
        mdib = ConsumerMdib(client)
        mdib.init_mdib()
        self.assertGreater(len(mdib.descriptions.objects), 0)  # at least one descriptor  # noqa: PT009
        self.assertTrue(client.is_connected)  # at least one descriptor  # noqa: PT009

        # we want to exec. ALL following steps, therefore collect data and do test at the end.
        print('Test step 5: check that at least one patient context exists')
        patients = mdib.context_states.NODETYPE.get(pm.PatientContextState, [])
        if not patients:
            errors.append('### Test 5 ### failed')

        print('Test step 6: check that at least one location context exists')
        locations = mdib.context_states.NODETYPE.get(pm.LocationContextState, [])
        if not locations:
            errors.append('### Test 6 ### failed')
        _passed, _errors = self._test_state_updates(mdib)
        errors.extend(_errors)
        passed.extend(_passed)
        _passed, _errors = self._test_setstring_operation(mdib, client)
        errors.extend(_errors)
        passed.extend(_passed)
        _passed, _errors = self._test_setvalue_operation(mdib, client)
        errors.extend(_errors)
        passed.extend(_passed)
        print(errors)
        print(passed)
        self.assertEqual(len(errors), 0, msg='expected no Errors, got:{}'.format(', '.join(errors)))  # noqa: PT009
        self.assertEqual(len(passed), 4, msg='expected 4 Passed, got :{}'.format(', '.join(passed)))  # noqa: PT009

    @staticmethod
    def _test_state_updates(mdib):  # noqa: ANN001, ANN205, C901
        passed = []
        errors = []
        print('Test step 7&8: count metric state updates and alert state updates')
        metric_updates = defaultdict(list)
        alert_updates = defaultdict(list)

        def onMetricUpdates(metricsbyhandle):  # noqa: ANN001, N802
            print('onMetricUpdates', metricsbyhandle)
            for k, v in metricsbyhandle.items():
                metric_updates[k].append(v)

        def onAlertUpdates(alertsbyhandle):  # noqa: ANN001, N802
            print('onAlertUpdates', alertsbyhandle)
            for k, v in alertsbyhandle.items():
                alert_updates[k].append(v)

        observableproperties.bind(mdib, metrics_by_handle=onMetricUpdates)
        observableproperties.bind(mdib, alert_by_handle=onAlertUpdates)

        sleep_timer = 11
        min_updates = sleep_timer // 5 - 1
        print(
            f'will wait for {sleep_timer} seconds now, expecting at least {metric_updates} updates per handle',
        )
        time.sleep(sleep_timer)
        print(metric_updates)
        print(alert_updates)
        found_error = False
        if not metric_updates:
            print('found no metric state updates at all, test step 8 failed')
            found_error = True
        for k, v in metric_updates.items():
            if len(v) < min_updates:
                print(f'found only {len(v)} updates for {k}, test step 7 failed')
                found_error = True
            else:
                print(f'found {len(v)} updates for {k}, test step 7 ok')
        if found_error:
            errors.append('### Test 7 ### failed')
        else:
            passed.append('### Test 7 ### passed')

        found_error = False
        if not alert_updates:
            print('found no alert state updates at all, test step 8 failed')
            found_error = True
        for k, v in alert_updates.items():
            if len(v) < min_updates:
                print(f'found only {len(v)} updates for {k}, test step 8 failed')
            else:
                print(f'found {len(v)} updates for {k}, test step 8 ok')
        if found_error:
            errors.append('### Test 8 ### failed')
        else:
            passed.append('### Test 8 ### passed')
        return passed, errors

    @staticmethod
    def _test_setstring_operation(mdib, client):  # noqa: ANN001, ANN205
        passed = []
        errors = []
        print('Test step 9: call SetString operation')
        setstring_operations = mdib.descriptions.NODETYPE.get(pm.SetStringOperationDescriptor, [])
        setst_handle = 'string.ch0.vmd1_sco_0'
        if len(setstring_operations) == 0:
            print('Test step 9 failed, no SetString operation found')
            errors.append('### Test 9 ### failed')
        else:
            for s in setstring_operations:
                if s.Handle != setst_handle:
                    continue
                print(f'setString Op ={s}')
                fut = client.set_service_client.set_string(s.Handle, 'hoppeldipop')
                try:
                    res = fut.result(timeout=10)
                    print(res)
                    if res.InvocationInfo.InvocationState != msg_types.InvocationState.FINISHED:
                        print(f'set string operation {s.Handle} did not finish with "Fin":{res}')
                        errors.append('### Test 9 ### failed')
                    else:
                        print(f'set value operation {s.Handle} ok:{res}')
                        passed.append('### Test 9 ### passed')
                except futures.TimeoutError:
                    print('timeout error')
                    errors.append('### Test 9 ### failed')
        return passed, errors

    @staticmethod
    def _test_setvalue_operation(mdib, client):  # noqa: ANN001, ANN205
        passed = []
        errors = []
        print('Test step 10: call SetValue operation')
        setvalue_operations = mdib.descriptions.NODETYPE.get(pm.SetValueOperationDescriptor, [])
        setval_handle = 'numeric.ch0.vmd1_sco_0'
        if len(setvalue_operations) == 0:
            print('Test step 10 failed, no SetValue operation found')
            errors.append('### Test 10 ### failed')
        else:
            for s in setvalue_operations:
                if s.Handle != setval_handle:
                    continue
                print(f'setNumericValue Op ={s}')
                fut = client.set_service_client.set_numeric_value(s.Handle, Decimal(42))
                try:
                    res = fut.result(timeout=10)
                    print(res)
                    if res.InvocationInfo.InvocationState != msg_types.InvocationState.FINISHED:
                        print(f'set value operation {s.Handle} did not finish with "Fin":{res}')
                    else:
                        print(f'set value operation {s.Handle} ok:{res}')
                    passed.append('### Test 10 ### passed')
                except futures.TimeoutError:
                    print('timeout error')
                    errors.append('### Test 10 ### failed')
        return passed, errors
