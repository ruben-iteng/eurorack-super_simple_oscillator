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
from faebryk.exporters.netlist.kicad.netlist_kicad import (
    from_faebryk_t2_netlist,
)
from faebryk.exporters.netlist.netlist import make_t2_netlist_from_t1
from faebryk.exporters.netlist.graph import (
    make_graph_from_components,
    make_t1_netlist_from_graph,
)

# library imports
from faebryk.library.core import Component, Interface
from faebryk.library.library.components import (
    Resistor,
    Capacitor,
)
from faebryk.library.library.interfaces import Power, Electrical
from faebryk.library.library.parameters import Constant, TBD
from faebryk.library.library.footprints import SMDTwoPin
from faebryk.library.traits.component import has_footprint
from faebryk.library.trait_impl.component import (
    has_symmetric_footprint_pinmap,
    has_defined_footprint,
    can_bridge_defined,
    has_defined_footprint_pinmap,
)

from faebryk.library.kicad import KicadFootprint, has_kicad_manual_footprint

from faebryk.library.util import get_all_components, times

# Project library imports
from library.library.components import (
    Potentiometer,
    _2N3904,  # MMBT2N3904,
    _2N3906,  # MMBT2N3906,
    AudioJack2_Ground,
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
        self.CMPs.reverse_avalanche_transistor = _2N3904()
        self.CMPs.charge_capacitor = Capacitor(Constant(10 * n))

        # oscillator core: bridge open gate transistor with cap
        #  reverse avalanche has to have cut off leg
        self.CMPs.reverse_avalanche_transistor.IFs.E.connect(self.IFs.vcc)
        self.CMPs.reverse_avalanche_transistor.IFs.C.connect_via(
            self.CMPs.charge_capacitor,
            self.CMPs.reverse_avalanche_transistor.IFs.E,
        )

        # output transistor C has oscillating voltage
        self.IFs.wave_out.connect(self.CMPs.reverse_avalanche_transistor.IFs.C)
        self.IFs.pitch_in.connect_via(
            self.CMPs.current_limiting_resistor,
            self.CMPs.reverse_avalanche_transistor.IFs.C,
        )

        self.add_trait(can_bridge_defined(self.IFs.pitch_in, self.IFs.wave_out))

        # footprints
        for r in [self.CMPs.current_limiting_resistor, self.CMPs.charge_capacitor]:
            r.add_trait(has_defined_footprint(SMDTwoPin(SMDTwoPin.Type._0805)))
            r.add_trait(has_symmetric_footprint_pinmap())


class expo_converter(Component):
    def __init__(self) -> None:
        super().__init__()

        # interfaces
        self.IFs.power = EurorackPower()
        self.IFs.pitch_out = Electrical()
        self.IFs.freq_in = Electrical()
        # self.IFs.freq_offset_in = Electrical()

        # comps
        self.CMPs.current_sink = _2N3904()
        self.CMPs.buffer = _2N3906()
        self.CMPs.frequency_offset_trimmer = Potentiometer(Constant(10 * K))
        self.CMPs.frequency_offset_current_min_resistor = Resistor(Constant(100 * K))

        # aliases
        vcc = self.IFs.power.IFs.hv
        gnd = self.IFs.power.IFs.gnd
        vdd = self.IFs.power.IFs.lv

        # in/out
        self.IFs.freq_in.connect(self.CMPs.buffer.IFs.B)
        self.IFs.pitch_out.connect(self.CMPs.current_sink.IFs.C)
        # self.IFs.freq_offset_in.connect(self.CMPs.current_sink.IFs.B)
        self.add_trait(can_bridge_defined(self.IFs.freq_in, self.IFs.pitch_out))

        # function

        self.CMPs.frequency_offset_current_min_resistor.IFs.unnamed[0].connect(
            self.CMPs.buffer.IFs.E
        )
        self.CMPs.buffer.IFs.E.connect(self.CMPs.current_sink.IFs.B)
        self.CMPs.buffer.IFs.C.connect(vdd)
        self.CMPs.current_sink.IFs.E.connect(gnd)
        self.CMPs.current_sink.IFs.B.connect(
            self.CMPs.frequency_offset_current_min_resistor.IFs.unnamed[0]
        )

        self.CMPs.frequency_offset_trimmer.connect_as_voltage_divider(
            vcc, gnd, self.CMPs.frequency_offset_current_min_resistor.IFs.unnamed[1]
        )

        # footprints
        self.CMPs.frequency_offset_trimmer.add_trait(
            has_defined_footprint(
                KicadFootprint(
                    "Potentiometer_THT:Potentiometer_Alpha_RD902F-40-00D_Dual_Vertical_CircularHoles"
                )
            )
        )
        self.CMPs.frequency_offset_trimmer.add_trait(
            has_defined_footprint_pinmap(
                {
                    1: self.CMPs.frequency_offset_trimmer.IFs.resistors[0],
                    2: self.CMPs.frequency_offset_trimmer.IFs.wiper,
                    3: self.CMPs.frequency_offset_trimmer.IFs.resistors[1],
                }
            )
        )
        for r in [self.CMPs.frequency_offset_current_min_resistor]:
            r.add_trait(has_defined_footprint(SMDTwoPin(SMDTwoPin.Type._0805))),
            r.add_trait(has_symmetric_footprint_pinmap()),


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
        self.CMPs.input_jack = AudioJack2_Ground()
        self.CMPs.frequency_control_potentiometer = Potentiometer(Constant(100 * K))
        self.CMPs.voct_scale_trimmer = Potentiometer(Constant(1 * K))
        self.CMPs.input_impendace_resistor = Resistor(Constant(100 * K))
        self.CMPs.negative_bias_resistor = Resistor(Constant(220 * K))
        self.CMPs.voct_min_resistor = Resistor(Constant(1.5 * K))
        self.CMPs.freq_devider_mix_resistor = Resistor(Constant(150 * K))

        # connections
        self.CMPs.input_jack.IFs.S.connect(gnd)
        self.CMPs.voct_min_resistor.IFs.unnamed[1].connect_via(
            self.CMPs.voct_scale_trimmer.CMPs.resistors[0], gnd
        )
        self.CMPs.negative_bias_resistor.IFs.unnamed[1].connect(vdd)
        self.CMPs.frequency_control_potentiometer.connect_as_voltage_divider(
            vcc, gnd, self.CMPs.freq_devider_mix_resistor.IFs.unnamed[1]
        )
        for i in [
            self.CMPs.negative_bias_resistor.IFs.unnamed[0],
            self.CMPs.freq_devider_mix_resistor.IFs.unnamed[0],
            self.CMPs.voct_min_resistor.IFs.unnamed[0],
            self.IFs.freq_out,
        ]:
            self.CMPs.input_jack.IFs.T.connect_via(
                self.CMPs.input_impendace_resistor, i
            )

        # footprints
        for r in [
            self.CMPs.input_impendace_resistor,
            self.CMPs.negative_bias_resistor,
            self.CMPs.voct_min_resistor,
            self.CMPs.freq_devider_mix_resistor,
        ]:
            r.add_trait(has_defined_footprint(SMDTwoPin(SMDTwoPin.Type._0805)))
            r.add_trait(has_symmetric_footprint_pinmap())

        for r in [
            self.CMPs.voct_scale_trimmer,
            self.CMPs.frequency_control_potentiometer,
        ]:
            r.add_trait(
                has_defined_footprint(
                    KicadFootprint(
                        "Potentiometer_THT:Potentiometer_Alpha_RD902F-40-00D_Dual_Vertical_CircularHoles"
                    )
                )
            )
            r.add_trait(
                has_defined_footprint_pinmap(
                    {
                        1: r.IFs.resistors[0],
                        2: r.IFs.wiper,
                        3: r.IFs.resistors[1],
                    }
                )
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
        self.CMPs.stages = times(2, _2N3904)
        self.CMPs.current_limiting_resistor = Resistor(Constant(10 * K))

        # in/out
        self.IFs.wave_unbuffered_in.connect(self.CMPs.stages[0].IFs.B)
        self.IFs.wave_buffered_out.connect(self.CMPs.stages[1].IFs.E)
        self.add_trait(
            can_bridge_defined(self.IFs.wave_unbuffered_in, self.IFs.wave_buffered_out)
        )

        # function -------

        # current path
        for stage in self.CMPs.stages:
            stage.IFs.C.connect(vcc)
        self.CMPs.stages[1].IFs.E.connect_via(self.CMPs.current_limiting_resistor, vdd)

        # chain
        self.CMPs.stages[0].IFs.E.connect(self.CMPs.stages[1].IFs.B)

        # footprints
        for r in [self.CMPs.current_limiting_resistor]:
            r.add_trait(has_defined_footprint(SMDTwoPin(SMDTwoPin.Type._0805))),
            r.add_trait(has_symmetric_footprint_pinmap()),


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
        self.CMPs.jack = AudioJack2_Ground()

        # I/O
        self.IFs.wave_buffered_in.connect_via(
            self.CMPs.ac_coupling_capacitor, self.CMPs.jack.IFs.T  # tip
        )

        # function
        self.CMPs.jack.IFs.T.connect_via(self.CMPs.pull_down_resistor, gnd)  # tip
        self.CMPs.jack.IFs.S.connect(gnd)  # sleeve

        # footprints
        for r in [
            self.CMPs.ac_coupling_capacitor,
            self.CMPs.pull_down_resistor,
        ]:
            r.add_trait(has_defined_footprint(SMDTwoPin(SMDTwoPin.Type._0805)))
            r.add_trait(has_symmetric_footprint_pinmap())


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

        # hack footprints
        for r in self.CMPs.get_all():
            if not r.has_trait(has_footprint):
                r.add_trait(has_symmetric_footprint_pinmap())

        self.add_trait(has_symmetric_footprint_pinmap())


G = Kassutronics_Avalance_VCO()
CMPs = [G]


t1_ = make_t1_netlist_from_graph(make_graph_from_components(CMPs))
netlist = from_faebryk_t2_netlist(make_t2_netlist_from_t1(t1_))

Path("./build/faebryk/").mkdir(parents=True, exist_ok=True)
path = Path("./build/faebryk/faebryk.net")
logger.info("Writing Experiment netlist to {}".format(path.resolve()))
path.write_text(netlist, encoding="utf-8")

from faebryk.exporters.netlist.netlist import render_graph

render_graph(t1_)
