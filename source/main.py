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

from pathlib import Path
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
from faebryk.library.core import Component, Interface
from faebryk.library.library.components import Resistor
from faebryk.library.library.footprints import SMDTwoPin
from faebryk.library.library.interfaces import Power, Electrical
from faebryk.library.library.parameters import Constant, TBD
from faebryk.library.trait_impl.component import (
    has_symmetric_footprint_pinmap,
    can_bridge_defined,
)

from faebryk.library.util import get_all_components, times

# Project library imports
from library.library.components import (
    MMBT2N3904,
    MMBT2N3906,
    PJ398SM,
    Capacitor,
    Potentiometer,
    Transistor,
)

K = 1000
M = 1000_000
G = 1000_000_000

n = 0.001 * 0.001 * 0.001
u = 0.001 * 0.001


class EurorackPower(Interface):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.IFs.hv = Electrical()
        self.IFs.gnd = Electrical()
        self.IFs.lv = Electrical()

    def connect(self, other: Interface) -> Interface:
        assert type(other) is EurorackPower, "can't connect to non eurorack power"
        for s, d in zip(self.IFs.get_all(), other.IFs.get_all()):
            s.connect(d)

        return self

    def connect_pos(self, other: Power) -> Interface:
        assert type(other) is Power, "can't connect to non power"
        self.IFs.hv.connect(other.IFs.hv)
        self.IFs.gnd.connect(other.IFs.lv)

        return self

    def connect_neg(self, other: Power) -> Interface:
        assert type(other) is Power, "can't connect to non power"
        self.IFs.gnd.connect(other.IFs.hv)
        self.IFs.lv.connect(other.IFs.lv)

        return self

    def connect_full(self, other: Power) -> Interface:
        assert type(other) is Power, "can't connect to non power"
        self.IFs.hv.connect(other.IFs.hv)
        self.IFs.lv.connect(other.IFs.lv)

        return self


# reverse avalanche oscilator core with lineair to exponential converter (1v/oct) input
class osc_core(Component):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        self.IFs.vcc = Electrical()
        self.IFs.wave_out = Electrical()
        self.IFs.pitch_in = Electrical()

        # components
        self.CMPs.current_limiting_resistor = Resistor(Constant(1 * K))
        self.CMPs.reverse_avalanche_transistor = MMBT2N3904()
        self.CMPs.charge_capacitor = Capacitor(Constant(10 * n))

        # oscillator core: bridge open gate transistor with cap
        #  reverse avalanche has to have cut off leg
        self.CMPs.reverse_avalanche_transistor.IFs.emitter.connect(self.IFs.vcc)
        self.CMPs.reverse_avalanche_transistor.IFs.collector.connect_via(
            self.CMPs.charge_capacitor,
            self.CMPs.reverse_avalanche_transistor.IFs.emitter,
        )

        # output transistor collector has oscillating voltage
        self.IFs.wave_out.connect(self.CMPs.reverse_avalanche_transistor.IFs.collector)
        self.IFs.pitch_in.connect_via(
            self.CMPs.current_limiting_resistor,
            self.CMPs.reverse_avalanche_transistor.IFs.collector,
        )

        self.add_trait(can_bridge_defined(self.IFs.pitch_in, self.IFs.wave_out))


class expo_converter(Component):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        self.IFs.power = EurorackPower()
        self.IFs.pitch_out = Electrical()
        self.IFs.freq_in = Electrical()
        self.IFs.freq_offset_in = Electrical()

        # comps
        self.CMPs.current_sink = MMBT2N3904()
        self.CMPs.buffer = MMBT2N3906()
        self.CMPs.frequency_offset_trimmer = Potentiometer(TBD)
        self.CMPs.frequency_offset_current_min_resistor = Resistor(Constant(100 * K))

        # aliases
        vcc = self.IFs.power.IFs.hv
        gnd = self.IFs.power.IFs.gnd
        vdd = self.IFs.power.IFs.lv

        # in/out
        self.IFs.freq_in.connect(self.CMPs.buffer.IFs.base)
        self.IFs.pitch_out.connect(self.CMPs.current_sink.IFs.collector)
        self.IFs.freq_offset_in.connect(self.CMPs.current_sink.IFs.base)
        self.add_trait(can_bridge_defined(self.IFs.freq_in, self.IFs.pitch_out))

        # function

        self.CMPs.frequency_offset_current_min_resistor.IFs._unnamed[1].connect(
            self.CMPs.buffer.IFs.emitter
        )
        self.CMPs.buffer.IFs.emitter.connect(self.CMPs.current_sink.IFs.base)
        self.CMPs.buffer.IFs.collector.connect(vdd)
        self.CMPs.current_sink.IFs.emitter.connect(gnd)

        self.CMPs.frequency_offset_trimmer.connect_as_voltage_divider(
            vcc, gnd, self.CMPs.frequency_offset_current_min_resistor.IFs._unnamed[0]
        )


# cv input with frequency control and volt per octave offset inputs
class cv_input(Component):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        self.IFs.power = EurorackPower()
        self.IFs.freq_out = Electrical()

        # alliases
        vcc = self.IFs.power.IFs.hv
        gnd = self.IFs.power.IFs.gnd
        vdd = self.IFs.power.IFs.lv

        # components
        self.CMPs.input_jack = PJ398SM()
        self.CMPs.frequency_control_potentiometer = Potentiometer(TBD)
        self.CMPs.input_impendace_resistor = Resistor(Constant(100 * K))
        self.CMPs.negative_bias_resistor = Resistor(Constant(220 * K))
        self.CMPs.voct_min_resistor = Resistor(Constant(1500))
        self.CMPs.freq_devider_mix_resistor = Resistor(Constant(150 * K))

        # connections
        self.CMPs.input_jack.IFs.sleeve.connect(gnd)
        self.CMPs.voct_min_resistor.IFs._unnamed[1].connect_via(
            self.CMPs.frequency_control_potentiometer.CMPs.resistors[0], gnd
        )
        self.CMPs.negative_bias_resistor.IFs._unnamed[1].connect(vdd)
        self.CMPs.frequency_control_potentiometer.connect_as_voltage_divider(
            vcc, gnd, self.CMPs.negative_bias_resistor.IFs._unnamed[1]
        )
        for i in [
            self.CMPs.negative_bias_resistor.IFs._unnamed[0],
            self.CMPs.freq_devider_mix_resistor.IFs._unnamed[0],
            self.CMPs.voct_min_resistor.IFs._unnamed[0],
            self.IFs.freq_out,
        ]:
            self.CMPs.input_jack.IFs.tip.connect_via(
                self.CMPs.input_impendace_resistor, i
            )


class output_buffer(Component):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        self.IFs.power = Power()
        self.IFs.wave_buffered_out = Electrical()
        self.IFs.wave_unbuffered_in = Electrical()

        # alliases
        vcc = self.IFs.power.IFs.hv
        vdd = self.IFs.power.IFs.lv

        # components
        self.CMPs.stages = times(2, MMBT2N3904)
        self.CMPs.current_limiting_resistor = Resistor(Constant(10 * K))

        # in/out
        self.IFs.wave_unbuffered_in.connect(self.CMPs.stages[0].IFs.base)
        self.IFs.wave_buffered_out.connect(self.CMPs.stages[-1].IFs.emitter)
        self.add_trait(
            can_bridge_defined(self.IFs.wave_unbuffered_in, self.IFs.wave_buffered_out)
        )

        # function -------

        # current path
        for stage in self.CMPs.stages:
            stage.IFs.collector.connect(vcc)
        self.CMPs.stages[-1].IFs.emitter.connect_via(
            self.CMPs.current_limiting_resistor, vdd
        )

        # chain
        self.CMPs.stages[0].IFs.emitter.connect(self.CMPs.stages[1].IFs.base)


class audio_output(Component):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        self.IFs.gnd = Electrical()
        self.IFs.wave_buffered_in = Electrical()

        # aliases
        gnd = self.IFs.gnd

        # components
        self.CMPs.pull_down_resistor = Resistor(Constant(10 * K))
        self.CMPs.ac_coupling_capacitor = Capacitor(Constant(10 * u))
        self.CMPs.jack = PJ398SM()

        # I/O
        self.IFs.wave_buffered_in.connect_via(
            self.CMPs.ac_coupling_capacitor, self.CMPs.jack.IFs.tip
        )

        # function
        self.CMPs.jack.IFs.tip.connect_via(self.CMPs.pull_down_resistor, gnd)
        self.CMPs.jack.IFs.sleeve.connect(gnd)


class Kassutronics_Avalance_VCO(Component):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        self.IFs.power = EurorackPower()

        # components
        self.CMPs.cv_input = cv_input()
        self.CMPs.expo_converter = expo_converter()
        self.CMPs.osc_core = osc_core()
        self.CMPs.output_buffer = output_buffer()
        self.CMPs.audio_output = audio_output()

        # power
        self.IFs.power.connect(self.CMPs.cv_input.IFs.power)
        self.IFs.power.connect(self.CMPs.expo_converter.IFs.power)
        self.IFs.power.IFs.hv.connect(self.CMPs.osc_core.IFs.vcc)
        self.IFs.power.connect_full(self.CMPs.output_buffer.IFs.power)
        self.IFs.power.IFs.gnd.connect(self.CMPs.audio_output.IFs.gnd)

        # function
        self.CMPs.cv_input.IFs.freq_out.connect_via_chain(
            [
                self.CMPs.expo_converter,
                self.CMPs.osc_core,
                self.CMPs.output_buffer,
            ],
            self.CMPs.audio_output.IFs.wave_buffered_in,
        )


G = Kassutronics_Avalance_VCO()

CMPs = [G]

# Hack footprints
ALL_CMPS = [comp for i in CMPs for comp in get_all_components(i)] + CMPs
for r in ALL_CMPS:
    r.add_trait(has_symmetric_footprint_pinmap())

t1_ = make_t1_netlist_from_graph(make_graph_from_components(CMPs))

netlist = from_faebryk_t2_netlist(make_t2_netlist_from_t1(t1_))

path = Path("./build/faebryk.net")
logger.info("Writing Experiment netlist to {}".format(path.absolute()))
path.write_text(netlist)

from faebryk.exporters.netlist import render_graph

render_graph(t1_)
