import logging
from faebryk.library.traits import component

from faebryk.library.trait_impl.component import (
    contructable_from_component,
    has_defined_footprint,
    has_defined_footprint_pinmap,
    has_defined_type_description,
    has_footprint_pinmap,
    has_symmetric_footprint_pinmap,
    has_type_description,
)
from faebryk.library.traits.interface import contructable_from_interface_list
from faebryk.library.traits.parameter import is_representable_by_single_value

logger = logging.getLogger("local_library")

from faebryk.library.core import Component, ComponentTrait, Interface, Parameter
from faebryk.library.library.components import Transistor
from faebryk.library.library.interfaces import Electrical, Power
from faebryk.library.library.parameters import Constant, Range
from faebryk.library.trait_impl.component import can_bridge_defined
from faebryk.library.util import get_all_interfaces, times, unit_map

from faebryk.libs.exceptions import FaebrykException

import typing


class MMBT2N3904(Transistor):
    pass


class MMBT2N3906(Transistor):
    pass
