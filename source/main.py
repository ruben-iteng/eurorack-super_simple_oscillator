# This file is part of the faebryk project
# SPDX-License-Identifier: MIT

"""
This file contains a faebryk sample.
Faebryk samples demonstrate the usage by building example systems.
This particular sample creates a netlist with some resistors and a nand ic 
    with no specific further purpose or function.
Thus this is a netlist sample.
Netlist samples can be run directly.
The netlist is printed to stdout.
"""

import logging

logger = logging.getLogger("main")


# function imports
from faebryk.exporters.netlist.kicad.netlist_kicad import from_faebryk_t2_netlist
from faebryk.exporters.netlist import make_t2_netlist_from_t1
from faebryk.exporters.netlist.graph import (
    make_graph_from_components,
    make_t1_netlist_from_graph,
)

# library imports
from faebryk.library.core import Component
from faebryk.library.library.components import Resistor
from faebryk.library.library.footprints import SMDTwoPin
from faebryk.library.library.interfaces import Power
from faebryk.library.library.parameters import Constant
from faebryk.library.traits.component import (
    has_symmetric_footprint_pinmap,
)

# Project library imports
from library.library.components import (
    MMBT2N3904,
    MMBT2N3906,
    PJ398SM,
    Capacitor,
    Potentiometer,
    Transistor,
)


class generic:
    def __init__(self) -> None:
        pass


class module:
    def __init__(self) -> None:
        self.comps = generic()

    def get_comps(self) -> list[Component]:
        return [x for x in vars(self.comps) if issubclass(type(x), Component)]


K = 1000
M = 1000_000
G = 1000_000_000

# power
eurorack_positive_power_rail = Component()
eurorack_positive_power_rail.power = Power()
eurorack_positive_power_rail.add_trait(
    has_defined_interfaces([eurorack_positive_power_rail.power])
)
eurorack_positive_power_rail.power.set_component(eurorack_positive_power_rail)
eurorack_negative_power_rail = Component()
eurorack_negative_power_rail.power = Power()
eurorack_negative_power_rail.add_trait(
    has_defined_interfaces([eurorack_positive_power_rail.power])
)
eurorack_negative_power_rail.power.set_component(eurorack_positive_power_rail)
# aliases
vcc = eurorack_positive_power_rail.power.hv
gnd = eurorack_positive_power_rail.power.lv
eurorack_negative_power_rail.power.hv.connect(gnd)
vdd = eurorack_negative_power_rail.power.lv

# reverse avalanche oscilator core
# components
osc_core = module()
osc_core.comps.current_limiting_resistor = Resistor(Constant(1000))
osc_core.comps.reverse_avalanche_transistor = MMBT2N3904()
osc_core.comps.charge_capacitor = Capacitor(1)
# aliases
osc_core.out = osc_core.comps.reverse_avalanche_transistor.collector
# connections
osc_core.comps.reverse_avalanche_transistor.emitter.connect(vcc)
# reverse_avalanche_transistor.interfaces.collector.connect(osc_core.comps.out)
osc_core.comps.charge_capacitor.interfaces[0].connect(vcc)
osc_core.comps.charge_capacitor.interfaces[1].connect(osc_core.out)
osc_core.comps.current_limiting_resistor.interfaces[0].connect(osc_core.out)

# cv input with lineair to exponential converter (1v/oct)
# components
exponential_converter_transistor = MMBT2N3904()
voct_converter_transistor = MMBT2N3906()
frequency_offset_trimmer = Potentiometer()
expo_converter_current_limiting_resistor = Resistor(100 * K)
input_jack = PJ398SM()
voct_trimmer = Potentiometer()
voct_min_resistor = Resistor(1500)
frequency_control_knob = Potentiometer()
input_impendace_resistor = Resistor(100 * K)
freq_devider_positive_resistor = Resistor(150 * K)
freq_devider_negative_resistor = Resistor(220 * K)
# connections
input_jack.sleeve.connect(gnd)
input_jack.tip.connect(input_impendace_resistor.interfaces[0])
for i in [
    freq_devider_negative_resistor.interfaces[0],
    freq_devider_positive_resistor.interfaces[0],
    voct_min_resistor.interfaces[0],
    voct_converter_transistor.base,
]:
    input_impendace_resistor.interfaces[1].connect(i)
freq_devider_negative_resistor.interfaces[1].connect(vdd)
freq_devider_negative_resistor.interfaces[1].connect(frequency_control_knob.wiper)
frequency_control_knob.resistor0.connect(vcc)
frequency_control_knob.resistor1.connect(gnd)
voct_trimmer.wiper.connect(voct_min_resistor.interfaces[1])
voct_trimmer.resistor1.connect(gnd)
for i in [
    expo_converter_current_limiting_resistor.interfaces[0],
    exponential_converter_transistor.base,
]:
    voct_converter_transistor.collector.connect(i)
voct_converter_transistor.emitter.connect(gnd)
frequency_offset_trimmer.resistor0.connect(vcc)
frequency_offset_trimmer.wiper.connect(
    expo_converter_current_limiting_resistor.interfaces[1]
)
frequency_offset_trimmer.resistor1.connect(gnd)

# output buffer
# components
buffer_transistor_1 = Transistor()  # MMBT2N3904()
buffer_transistor_2 = Transistor()  # MMBT2N3904()
buffer_current_limiting_resistor = Resistor(10000)
output_pull_resistor = Resistor(10000)
ac_coupling_capacitor = Capacitor(10)
output_jack = PJ398SM()
# connections
buffer_transistor_1.base.connect(osc_core.out)
buffer_transistor_1.emitter.connect(buffer_transistor_2.base)
buffer_transistor_1.collector.connect(vcc)
buffer_transistor_2.collector.connect(vcc)
for i in [
    buffer_current_limiting_resistor.interfaces[0],
    ac_coupling_capacitor.interfaces[0],
]:
    buffer_transistor_2.emitter.connect(i)
buffer_current_limiting_resistor.interfaces[1].connect(vdd)
for i in [output_pull_resistor.interfaces[0], output_jack.tip]:
    ac_coupling_capacitor.interfaces[1].connect(i)
output_jack.tip.connect(gnd)


for r in [
    *osc_core.get_comps(),
    buffer_transistor_1,
    buffer_transistor_2,
    buffer_current_limiting_resistor,
    output_pull_resistor,
    ac_coupling_capacitor,
    output_jack,
    exponential_converter_transistor,
    voct_converter_transistor,
    frequency_offset_trimmer,
    expo_converter_current_limiting_resistor,
    input_jack,
    voct_trimmer,
    voct_min_resistor,
    frequency_control_knob,
    input_impendace_resistor,
    freq_devider_positive_resistor,
    freq_devider_negative_resistor,
    eurorack_positive_power_rail,
    eurorack_negative_power_rail,
]:
    r.add_trait(has_symmetric_footprint_pinmap(r))

comps = [
    *osc_core.get_comps(),
    buffer_transistor_1,
    buffer_transistor_2,
    buffer_current_limiting_resistor,
    output_pull_resistor,
    ac_coupling_capacitor,
    output_jack,
    exponential_converter_transistor,
    voct_converter_transistor,
    frequency_offset_trimmer,
    expo_converter_current_limiting_resistor,
    input_jack,
    voct_trimmer,
    voct_min_resistor,
    frequency_control_knob,
    input_impendace_resistor,
    freq_devider_positive_resistor,
    freq_devider_negative_resistor,
    eurorack_positive_power_rail,
    eurorack_negative_power_rail,
]

t1_ = make_t1_netlist_from_graph(make_graph_from_components(comps))

netlist = from_faebryk_t2_netlist(make_t2_netlist_from_t1(t1_))

logger.info("Experiment netlist:")
print(netlist)

from faebryk.exporters.netlist import render_graph

render_graph(t1_)
