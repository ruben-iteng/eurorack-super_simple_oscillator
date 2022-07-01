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
from faebryk.library.library.components import Resistor
from faebryk.library.library.interfaces import Electrical, Power
from faebryk.library.library.parameters import Constant, Range
from faebryk.library.trait_impl.component import can_bridge_defined
from faebryk.library.util import get_all_interfaces, times, unit_map

from faebryk.libs.exceptions import FaebrykException

import typing


class Capacitor(Component):
    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self._setup_traits()
        return self

    def __init__(self, capacitance: Parameter):
        super().__init__()

        self._setup_interfaces()
        self.set_capacitance(capacitance)

    def _setup_traits(self):
        pass

    def _setup_interfaces(self):
        self.IFs.add_all(times(2, Electrical))
        self.add_trait(can_bridge_defined(*self.IFs._unnamed))

    def set_capacitance(self, capacitance: Parameter):
        self.capacitance = capacitance

        if type(capacitance) is not Constant:
            return

        class _has_type_description(has_type_description.impl()):
            @staticmethod
            def get_type_description():
                capacitance = self.capacitance
                return unit_map(
                    capacitance.value, ["µF", "mF", "F", "KF", "MF", "GF"], start="F"
                )

        self.add_trait(_has_type_description())


class Transistor(Component):
    def __new__(cls):
        self = super().__new__(cls)
        self._setup_traits()
        return self

    def __init__(self) -> None:
        super().__init__()
        self._setup_interfaces()

    def _setup_traits(self):
        self.add_trait(has_defined_type_description("Transistor"))

    def _setup_interfaces(self):
        self.IFs.emitter = Electrical()
        self.IFs.base = Electrical()
        self.IFs.collector = Electrical()


class MMBT2N3904(Transistor):
    pass


class MMBT2N3906(Transistor):
    pass


class PJ398SM(Component):
    def __new__(cls):
        self = super().__new__(cls)
        self._setup_traits()
        return self

    def __init__(self) -> None:
        super().__init__()
        self._setup_interfaces()

    def _setup_traits(self):
        self.add_trait(has_defined_type_description("Connector"))

    def _setup_interfaces(self):
        self.IFs.tip = Electrical()
        self.IFs.sleeve = Electrical()
        self.IFs.switch = Electrical()


class Potentiometer(Component):
    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls, *args, **kwargs)
        self._setup_traits()
        return self

    def __init__(self, resistance: Parameter) -> None:
        super().__init__()
        self._setup_interfaces(resistance)

    def _setup_traits(self):
        pass

    def _setup_interfaces(self, resistance):
        self.CMPs.resistors = [Resistor(resistance) for _ in range(2)]
        self.IFs.resistors = times(2, Electrical)
        self.IFs.wiper = Electrical()

        self.IFs.wiper.connect_all(
            [
                self.CMPs.resistors[0].IFs._unnamed[1],
                self.CMPs.resistors[1].IFs._unnamed[1],
            ]
        )

        for i, resistor in enumerate(self.CMPs.resistors):
            self.IFs.resistors[i].connect(resistor.IFs._unnamed[0])

    def connect_as_voltage_divider(self, high, low, out):
        self.IFs.resistors[0].connect(high)
        self.IFs.resistors[1].connect(low)
        self.IFs.wiper.connect(out)
