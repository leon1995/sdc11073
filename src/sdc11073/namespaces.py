"""A helper for xml name space handling."""

from __future__ import annotations

import pathlib
from enum import Enum
from typing import NamedTuple

from lxml import etree

from sdc11073 import xml_utils


class PrefixNamespace(NamedTuple):
    """Represents a namespace with an optional prefix and schema location."""

    prefix: str
    namespace: str
    schema_location_url: str | None
    local_schema_file: pathlib.Path | None

    def tag(self, localname: str) -> xml_utils.QName:
        """Create a QName for the given localname."""
        return xml_utils.QName(self.namespace, localname)

    def doc_name(self, localname: str) -> str:
        """Get the string representation with an optional prefix."""
        if self.prefix:
            return f'{self.prefix}:{localname}'
        return localname


schema_folder = pathlib.Path(__file__).parent.joinpath('xsd')


class PrefixesEnum(PrefixNamespace, Enum):
    """Enum for various XML namespaces with prefixes."""

    MSG = PrefixNamespace(
        'msg',
        'http://standards.ieee.org/downloads/11073/11073-10207-2017/message',
        'http://standards.ieee.org/downloads/11073/11073-10207-2017/BICEPS_MessageModel.xsd',
        schema_folder.joinpath('BICEPS_MessageModel.xsd'),
    )
    PM = PrefixNamespace(
        'dom',
        'http://standards.ieee.org/downloads/11073/11073-10207-2017/participant',
        'http://standards.ieee.org/downloads/11073/11073-10207-2017/BICEPS_ParticipantModel.xsd',
        schema_folder.joinpath('BICEPS_ParticipantModel.xsd'),
    )
    EXT = PrefixNamespace(
        'ext',
        'http://standards.ieee.org/downloads/11073/11073-10207-2017/extension',
        'http://standards.ieee.org/downloads/11073/11073-10207-2017/ExtensionPoint.xsd',
        schema_folder.joinpath('ExtensionPoint.xsd'),
    )
    MDPWS = PrefixNamespace('mdpws', 'http://standards.ieee.org/downloads/11073/11073-20702-2016', None, None)
    SDC = PrefixNamespace('sdc', 'http://standards.ieee.org/downloads/11073/11073-20701-2018', None, None)
    WSE = PrefixNamespace(
        'wse',
        'http://schemas.xmlsoap.org/ws/2004/08/eventing',
        'http://schemas.xmlsoap.org/ws/2004/08/eventing',
        schema_folder.joinpath('eventing.xsd'),
    )
    XSD = PrefixNamespace('xsd', 'http://www.w3.org/2001/XMLSchema', None, None)
    XSI = PrefixNamespace('xsi', 'http://www.w3.org/2001/XMLSchema-instance', None, None)
    WSA = PrefixNamespace(
        'wsa',
        'http://www.w3.org/2005/08/addressing',
        'http://www.w3.org/2006/03/addressing/ws-addr.xsd',
        schema_folder.joinpath('ws-addr.xsd'),
    )
    WSX = PrefixNamespace(
        'wsx',  # Meta Data Exchange
        'http://schemas.xmlsoap.org/ws/2004/09/mex',
        'http://schemas.xmlsoap.org/ws/2004/09/mex',
        schema_folder.joinpath('MetadataExchange.xsd'),
    )
    DPWS = PrefixNamespace(
        'dpws',
        'http://docs.oasis-open.org/ws-dd/ns/dpws/2009/01',
        'http://docs.oasis-open.org/ws-dd/ns/dpws/2009/01',
        schema_folder.joinpath('wsdd-dpws-1.1-schema-os.xsd'),
    )
    WSD = PrefixNamespace(
        'wsd',
        'http://docs.oasis-open.org/ws-dd/ns/discovery/2009/01',
        'http://docs.oasis-open.org/ws-dd/discovery/1.1/os/wsdd-discovery-1.1-schema-os.xsd',
        schema_folder.joinpath('wsdd-discovery-1.1-schema-os.xsd'),
    )
    S12 = PrefixNamespace(
        's12',
        'http://www.w3.org/2003/05/soap-envelope',
        'http://www.w3.org/2003/05/soap-envelope',
        schema_folder.joinpath('soap-envelope.xsd'),
    )
    XML = PrefixNamespace(
        'xml',
        'http://www.w3.org/XML/1998/namespace',
        'http://www.w3.org/2001/xml.xsd',
        schema_folder.joinpath('xml.xsd'),
    )
    WXF = PrefixNamespace(
        'wxf',  # ws-transfer
        'http://schemas.xmlsoap.org/ws/2004/09/transfer',
        None,
        None,
    )
    WSDL = PrefixNamespace(
        'wsdl',
        'http://schemas.xmlsoap.org/wsdl/',
        'http://schemas.xmlsoap.org/wsdl/',
        schema_folder.joinpath('wsdl.xsd'),
    )
    WSDL12 = PrefixNamespace(
        'wsdl12',
        'http://schemas.xmlsoap.org/wsdl/soap12/',
        None,
        None,
    )  # old soap 12 namespace, used in wsdl 1.1. only for wsdl
    WSP = PrefixNamespace('wsp', 'http://www.w3.org/ns/ws-policy', None, None)


class NamespaceHelper:
    """A helper class for managing XML namespaces and their prefixes."""

    def __init__(self, prefixes_enum: type[PrefixesEnum], default_ns: str | None = None):
        self.prefix_enum = prefixes_enum
        self._lookup = {}
        for enum_item in prefixes_enum:
            self._lookup[enum_item.name] = enum_item.value

        self._default_ns = default_ns

        self._prefix_map = {x.namespace: x.prefix for x in self._lookup.values()}  # map namespace to prefix
        self.ns_map = {x.prefix: x.namespace for x in self._lookup.values()}  # map prefix to namespace

    @property
    def MSG(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['MSG']

    @property
    def PM(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['PM']

    @property
    def EXT(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['EXT']

    @property
    def SDC(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['SDC']

    @property
    def WSE(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['WSE']

    @property
    def XSI(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['XSI']

    @property
    def WSA(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['WSA']

    @property
    def WSX(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['WSX']

    @property
    def DPWS(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['DPWS']

    @property
    def MDPWS(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['MDPWS']

    @property
    def WSD(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['WSD']

    @property
    def S12(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['S12']

    @property
    def XML(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['XML']

    @property
    def WSDL(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['WSDL']

    @property
    def WSDL12(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['WSDL12']

    @property
    def WSP(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['WSP']

    @property
    def WXF(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['WXF']

    @property
    def XSD(self) -> PrefixNamespace:  # noqa: D102, N802
        return self._lookup['XSD']

    def partial_map(self, *prefix: PrefixNamespace) -> dict:
        """Get a dictionary with prefix as key, namespace as value."""
        ret = {}
        for p in prefix:
            if p.namespace == self._default_ns:
                ret[None] = p.namespace
            ret[p.prefix] = p.namespace
        return ret

    def doc_name_from_qname(self, qname: etree.QName) -> str:
        """Get the prefix:name string, or only name (if default namespace is used)."""
        if qname.namespace is not None and qname.namespace == self._default_ns:
            return qname.localname
        prefix = self._prefix_map[qname.namespace]
        return f'{prefix}:{qname.localname}'

    def text_to_qname(self, text: str, nsmap: dict[str, str] | None = None) -> etree.QName:
        """Convert a text to a qname."""
        ns_map = nsmap or self.ns_map
        return text_to_qname(text, ns_map)


default_ns_helper = NamespaceHelper(PrefixesEnum)

# some constants from ws-addressing
WSA_ANONYMOUS = PrefixesEnum.WSA.namespace + '/anonymous'
WSA_NONE = PrefixesEnum.WSA.namespace + '/none'


def docname_from_qname(qname: etree.QName, ns_map: dict) -> str:
    """Get a prefix:name string, or only name (if default namespace is used)."""
    prefixmap = {v: k for k, v in ns_map.items()}
    prefix = prefixmap.get(qname.namespace)
    if prefix is None:
        return qname.localname
    return f'{prefix}:{qname.localname}'


def text_to_qname(text: str, doc_nsmap: dict[str, str]) -> xml_utils.QName:
    """Convert a text to a qname."""
    elements = text.split(':')
    prefix = None if len(elements) == 1 else elements[0]
    name = elements[-1]
    try:
        return xml_utils.QName(doc_nsmap[prefix], name)
    except KeyError as ex:
        raise KeyError(f'Cannot make QName for {text}, prefix is not in nsmap: {doc_nsmap.keys()}') from ex  # noqa: EM102


QN_TYPE = etree.QName(PrefixesEnum.XSI.namespace, 'type')  # frequently used QName, central definition


class EventingActions:
    """Constants for eventing actions."""

    Subscribe = PrefixesEnum.WSE.namespace + '/Subscribe'
    SubscribeResponse = PrefixesEnum.WSE.namespace + '/SubscribeResponse'
    SubscriptionEnd = PrefixesEnum.WSE.namespace + '/SubscriptionEnd'
    Unsubscribe = PrefixesEnum.WSE.namespace + '/Unsubscribe'
    UnsubscribeResponse = PrefixesEnum.WSE.namespace + '/UnsubscribeResponse'
    Renew = PrefixesEnum.WSE.namespace + '/Renew'
    RenewResponse = PrefixesEnum.WSE.namespace + '/RenewResponse'
    GetStatus = PrefixesEnum.WSE.namespace + '/GetStatus'
    GetStatusResponse = PrefixesEnum.WSE.namespace + '/GetStatusResponse'
