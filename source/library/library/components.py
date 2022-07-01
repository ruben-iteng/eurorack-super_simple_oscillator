import logging
from faebryk.library.traits import component

from faebryk.library.traits.component import (
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
from faebryk.library.library.interfaces import Electrical, Power
from faebryk.library.library.parameters import Constant
from faebryk.library.traits import *
from faebryk.library.util import get_all_interfaces, times, unit_map

from faebryk.libs.exceptions import FaebrykException

import typing

class Range(Parameter):
    def __init__(self, value_min: typing.Any, value_max: typing.Any) -> None:
        super().__init__()
        self.min = value_min
        self.max = value_max

    def pick(self, value_to_check: typing.Any):
        if not self.min <= value_to_check <= self.max:
            raise FaebrykException(
                f"Value not in range: {value_to_check} not in [{self.min},{self.max}]"
            )

        self.add_trait(is_representable_by_single_value(value_to_check))


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
        class _has_interfaces(has_interfaces):
            @staticmethod
            def get_interfaces() -> list[Interface]:
                return self.interfaces

        class _contructable_from_component(contructable_from_component):
            @staticmethod
            def from_component(comp: Component, capacitance: Parameter) -> Capacitor:
                assert comp.has_trait(has_interfaces)
                interfaces = comp.get_trait(has_interfaces).get_interfaces()
                assert len(interfaces) == 2
                assert len([i for i in interfaces if type(i) is not Electrical]) == 0

                c = Capacitor.__new__(Capacitor)
                c._setup_capacitance(capacitance)
                c.interfaces = interfaces

                return c

        self.add_trait(_has_interfaces())
        self.add_trait(_contructable_from_component())

    def _setup_interfaces(self):
        self.interfaces = [Electrical(), Electrical()]

    def set_capacitance(self, capacitance: Parameter):
        self.capacitance = capacitance

        if type(capacitance) is not Constant:
            return

        class _has_type_description(has_type_description):
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
        self.emitter = Electrical()
        self.base = Electrical()
        self.collector = Electrical()
        self.add_trait(has_defined_interfaces([self.emitter, self.base, self.collector]))


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
        self.tip = Electrical()
        self.sleeve = Electrical()
        self.switch = Electrical()


class Potentiometer(Component):
    def __new__(cls):
        self = super().__new__(cls)
        #self._setup_traits()
        return self

    def __init__(self) -> None:
        super().__init__()
        self._setup_interfaces()

    def _setup_interfaces(self):
        self.resistor0 = Electrical()
        self.wiper = Electrical()
        self.resistor1 = Electrical()