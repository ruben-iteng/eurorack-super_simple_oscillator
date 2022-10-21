import logging
from faebryk.library.traits import component

from faebryk.library.trait_impl.component import (
    has_defined_footprint,
    has_defined_footprint_pinmap,
    has_defined_type_description,
    has_footprint_pinmap,
    has_symmetric_footprint_pinmap,
    has_type_description,
)
from faebryk.library.kicad import (
    has_defined_kicad_ref,
    has_kicad_footprint,
    has_kicad_manual_footprint,
    has_kicad_ref,
    KicadFootprint,
)
from faebryk.library.traits.interface import contructable_from_interface_list
from faebryk.library.traits.parameter import is_representable_by_single_value

logger = logging.getLogger("local_library")

from faebryk.library.core import Component, ComponentTrait, Interface, Parameter
from faebryk.library.library.components import Resistor, BJT
from faebryk.library.library.interfaces import Electrical, Power
from faebryk.library.library.parameters import Constant, Range
from faebryk.library.trait_impl.component import can_bridge_defined
from faebryk.library.util import get_all_interfaces, times, unit_map

from faebryk.libs.exceptions import FaebrykException


class Potentiometer(Component):
    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls, *args, **kwargs)
        self._setup_traits()
        return self

    def __init__(self, resistance: Parameter) -> None:
        super().__init__()
        self._setup_interfaces(resistance)

    def _setup_traits(self):
        # self.add_trait(has_defined_kicad_ref("R"))
        self.add_trait(has_defined_type_description("R"))
        pass

    def _setup_interfaces(self, resistance):
        self.CMPs.resistors = [Resistor(resistance) for _ in range(2)]
        self.IFs.resistors = times(2, Electrical)
        self.IFs.wiper = Electrical()

        self.IFs.wiper.connect_all(
            [
                self.CMPs.resistors[0].IFs.unnamed[1],
                self.CMPs.resistors[1].IFs.unnamed[1],
            ]
        )

        for i, resistor in enumerate(self.CMPs.resistors):
            self.IFs.resistors[i].connect(resistor.IFs.unnamed[0])
            self.CMPs.resistors[i].add_trait(has_symmetric_footprint_pinmap())

    def connect_as_voltage_divider(self, high, low, out):
        self.IFs.resistors[0].connect(high)
        self.IFs.resistors[1].connect(low)
        self.IFs.wiper.connect(out)


class MMBT2N3904(BJT):
    pass


class MMBT2N3906(BJT):
    pass


class AudioJack2_Ground(Component):
    """
    Generated by symbol_converter
    filepath: ./tools/symbol_converter/Connector.kicad_sym
    hash: ee6acb9e5c100cbc618b09d382a2e9d817a011d2
    source:
        (   'symbol',
            'AudioJack2_Ground',
            ('in_bom', 'yes'),
            ('on_board', 'yes'),
            (   'property',
                'Reference',
                'J',
                ('id', 0),
                ('at', 0, 8.89, 0),
                ('effects', ('font', ('size', 1.27, 1.27)))),
            (   'property',
                'Value',
                'AudioJack2_Ground',
                ('id', 1),
                ('at', 0, 6.35, 0),
                ('effects', ('font', ('size', 1.27, 1.27)))),
            (   'property',
                'Footprint',
                '',
                ('id', 2),
                ('at', 0, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), 'hide')),
            (   'property',
                'Datasheet',
                '~',
                ('id', 3),
                ('at', 0, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), 'hide')),
            (   'property',
                'ki_keywords',
                'audio jack receptacle mono phone headphone TS connector',
                ('id', 4),
                ('at', 0, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), 'hide')),
            (   'property',
                'ki_description',
                'Audio Jack, 2 Poles (Mono / TS), Grounded Sleeve',
                ('id', 5),
                ('at', 0, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), 'hide')),
            (   'property',
                'ki_fp_filters',
                'Jack*',
                ('id', 6),
                ('at', 0, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), 'hide')),
            (   'symbol',
                'AudioJack2_Ground_0_1',
                (   'rectangle',
                    ('start', -2.54, -2.54),
                    ('end', -3.81, 0),
                    ('stroke', ('width', 0.254), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'outline'))),
                (   'polyline',
                    (   'pts',
                        ('xy', 0, 0),
                        ('xy', 0.635, -0.635),
                        ('xy', 1.27, 0),
                        ('xy', 2.54, 0)),
                    ('stroke', ('width', 0.254), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'none'))),
                (   'polyline',
                    (   'pts',
                        ('xy', 2.54, 2.54),
                        ('xy', -0.635, 2.54),
                        ('xy', -0.635, 0),
                        ('xy', -1.27, -0.635),
                        ('xy', -1.905, 0)),
                    ('stroke', ('width', 0.254), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'none'))),
                (   'rectangle',
                    ('start', 2.54, 3.81),
                    ('end', -2.54, -2.54),
                    ('stroke', ('width', 0.254), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'background')))),
            (   'symbol',
                'AudioJack2_Ground_1_1',
                (   'pin',
                    'passive',
                    'line',
                    ('at', 0, -5.08, 90),
                    ('length', 2.54),
                    ('name', '~', ('effects', ('font', ('size', 1.27, 1.27)))),
                    ('number', 'G', ('effects', ('font', ('size', 1.27, 1.27))))),
                (   'pin',
                    'passive',
                    'line',
                    ('at', 5.08, 2.54, 180),
                    ('length', 2.54),
                    ('name', '~', ('effects', ('font', ('size', 1.27, 1.27)))),
                    ('number', 'S', ('effects', ('font', ('size', 1.27, 1.27))))),
                (   'pin',
                    'passive',
                    'line',
                    ('at', 5.08, 0, 180),
                    ('length', 2.54),
                    ('name', '~', ('effects', ('font', ('size', 1.27, 1.27)))),
                    ('number', 'T', ('effects', ('font', ('size', 1.27, 1.27)))))))
    """

    def _setup_traits(self):
        self.add_trait(
            has_defined_footprint(
                KicadFootprint(
                    "Connector_Audio:Jack_3.5mm_QingPu_WQP-PJ398SM_Vertical_CircularHoles"
                )
            )
        )
        self.add_trait(
            has_defined_footprint_pinmap(
                {
                    "S": self.IFs.S,
                    "TN": self.IFs.TN,
                    "T": self.IFs.T,
                }
            )
        )
        # self.add_trait(has_defined_kicad_ref("J"))
        self.add_trait(has_defined_type_description("J"))
        return

    def _setup_interfaces(self):
        self.IFs.add_all(times(0, Electrical))
        self.IFs.S = Electrical()
        self.IFs.TN = Electrical()
        self.IFs.T = Electrical()

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        return self

    def __init__(self):
        super().__init__()

        self._setup_interfaces()
        self._setup_traits()


class _2N3904(Component):
    """
    Generated by symbol_converter
    filepath: ./Transistor_BJT.kicad_sym
    hash: 5a6074b533a5e64bf5672a15f73eb456875e8407
    source:
        (   'symbol',
            '2N3904',
            ('pin_names', ('offset', 0), 'hide'),
            ('in_bom', 'yes'),
            ('on_board', 'yes'),
            (   'property',
                'Reference',
                'Q',
                ('id', 0),
                ('at', 5.08, 1.905, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), ('justify', 'left'))),
            (   'property',
                'Value',
                '2N3904',
                ('id', 1),
                ('at', 5.08, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), ('justify', 'left'))),
            (   'property',
                'Footprint',
                'Package_TO_SOT_THT:TO-92_Inline',
                ('id', 2),
                ('at', 5.08, -1.905, 0),
                (   'effects',
                    ('font', ('size', 1.27, 1.27), 'italic'),
                    ('justify', 'left'),
                    'hide')),
            (   'property',
                'Datasheet',
                'https://www.onsemi.com/pub/Collateral/2N3903-D.PDF',
                ('id', 3),
                ('at', 0, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), ('justify', 'left'), 'hide')),
            (   'property',
                'ki_keywords',
                'NPN Transistor',
                ('id', 4),
                ('at', 0, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), 'hide')),
            (   'property',
                'ki_description',
                '0.2A Ic, 40V Vce, Small Signal NPN Transistor, TO-92',
                ('id', 5),
                ('at', 0, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), 'hide')),
            (   'property',
                'ki_fp_filters',
                'TO?92*',
                ('id', 6),
                ('at', 0, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), 'hide')),
            (   'symbol',
                '2N3904_0_1',
                (   'polyline',
                    ('pts', ('xy', 0.635, 0.635), ('xy', 2.54, 2.54)),
                    ('stroke', ('width', 0), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'none'))),
                (   'polyline',
                    ('pts', ('xy', 0.635, -0.635), ('xy', 2.54, -2.54), ('xy', 2.54, -2.54)),
                    ('stroke', ('width', 0), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'none'))),
                (   'polyline',
                    ('pts', ('xy', 0.635, 1.905), ('xy', 0.635, -1.905), ('xy', 0.635, -1.905)),
                    ('stroke', ('width', 0.508), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'none'))),
                (   'polyline',
                    (   'pts',
                        ('xy', 1.27, -1.778),
                        ('xy', 1.778, -1.27),
                        ('xy', 2.286, -2.286),
                        ('xy', 1.27, -1.778),
                        ('xy', 1.27, -1.778)),
                    ('stroke', ('width', 0), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'outline'))),
                (   'circle',
                    ('center', 1.27, 0),
                    ('radius', 2.8194),
                    ('stroke', ('width', 0.254), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'none')))),
            (   'symbol',
                '2N3904_1_1',
                (   'pin',
                    'passive',
                    'line',
                    ('at', 2.54, -5.08, 90),
                    ('length', 2.54),
                    ('name', 'E', ('effects', ('font', ('size', 1.27, 1.27)))),
                    ('number', '1', ('effects', ('font', ('size', 1.27, 1.27))))),
                (   'pin',
                    'passive',
                    'line',
                    ('at', -5.08, 0, 0),
                    ('length', 5.715),
                    ('name', 'B', ('effects', ('font', ('size', 1.27, 1.27)))),
                    ('number', '2', ('effects', ('font', ('size', 1.27, 1.27))))),
                (   'pin',
                    'passive',
                    'line',
                    ('at', 2.54, 5.08, 270),
                    ('length', 2.54),
                    ('name', 'C', ('effects', ('font', ('size', 1.27, 1.27)))),
                    ('number', '3', ('effects', ('font', ('size', 1.27, 1.27)))))))
    """

    def _setup_traits(self):
        self.add_trait(
            has_defined_footprint(KicadFootprint("Package_TO_SOT_THT:TO-92_Inline"))
        )
        self.add_trait(
            has_defined_footprint_pinmap(
                {
                    1: self.IFs.E,
                    2: self.IFs.B,
                    3: self.IFs.C,
                }
            )
        )
        # self.add_trait(has_defined_kicad_ref("Q"))
        self.add_trait(has_defined_type_description("Q"))
        return

    def _setup_interfaces(self):
        self.IFs.add_all(times(0, Electrical))
        self.IFs.E = Electrical()
        self.IFs.B = Electrical()
        self.IFs.C = Electrical()

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        return self

    def __init__(self):
        super().__init__()

        self._setup_interfaces()
        self._setup_traits()


class _2N3906(Component):
    """
    Generated by symbol_converter
    filepath: ./Transistor_BJT.kicad_sym
    hash: 5a6074b533a5e64bf5672a15f73eb456875e8407
    source:
        (   'symbol',
            '2N3906',
            ('pin_names', ('offset', 0), 'hide'),
            ('in_bom', 'yes'),
            ('on_board', 'yes'),
            (   'property',
                'Reference',
                'Q',
                ('id', 0),
                ('at', 5.08, 1.905, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), ('justify', 'left'))),
            (   'property',
                'Value',
                '2N3906',
                ('id', 1),
                ('at', 5.08, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), ('justify', 'left'))),
            (   'property',
                'Footprint',
                'Package_TO_SOT_THT:TO-92_Inline',
                ('id', 2),
                ('at', 5.08, -1.905, 0),
                (   'effects',
                    ('font', ('size', 1.27, 1.27), 'italic'),
                    ('justify', 'left'),
                    'hide')),
            (   'property',
                'Datasheet',
                'https://www.onsemi.com/pub/Collateral/2N3906-D.PDF',
                ('id', 3),
                ('at', 0, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), ('justify', 'left'), 'hide')),
            (   'property',
                'ki_keywords',
                'PNP Transistor',
                ('id', 4),
                ('at', 0, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), 'hide')),
            (   'property',
                'ki_description',
                '-0.2A Ic, -40V Vce, Small Signal PNP Transistor, TO-92',
                ('id', 5),
                ('at', 0, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), 'hide')),
            (   'property',
                'ki_fp_filters',
                'TO?92*',
                ('id', 6),
                ('at', 0, 0, 0),
                ('effects', ('font', ('size', 1.27, 1.27)), 'hide')),
            (   'symbol',
                '2N3906_0_1',
                (   'polyline',
                    ('pts', ('xy', 0.635, 0.635), ('xy', 2.54, 2.54)),
                    ('stroke', ('width', 0), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'none'))),
                (   'polyline',
                    ('pts', ('xy', 0.635, -0.635), ('xy', 2.54, -2.54), ('xy', 2.54, -2.54)),
                    ('stroke', ('width', 0), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'none'))),
                (   'polyline',
                    ('pts', ('xy', 0.635, 1.905), ('xy', 0.635, -1.905), ('xy', 0.635, -1.905)),
                    ('stroke', ('width', 0.508), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'none'))),
                (   'polyline',
                    (   'pts',
                        ('xy', 2.286, -1.778),
                        ('xy', 1.778, -2.286),
                        ('xy', 1.27, -1.27),
                        ('xy', 2.286, -1.778),
                        ('xy', 2.286, -1.778)),
                    ('stroke', ('width', 0), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'outline'))),
                (   'circle',
                    ('center', 1.27, 0),
                    ('radius', 2.8194),
                    ('stroke', ('width', 0.254), ('type', 'default'), ('color', 0, 0, 0, 0)),
                    ('fill', ('type', 'none')))),
            (   'symbol',
                '2N3906_1_1',
                (   'pin',
                    'passive',
                    'line',
                    ('at', 2.54, -5.08, 90),
                    ('length', 2.54),
                    ('name', 'E', ('effects', ('font', ('size', 1.27, 1.27)))),
                    ('number', '1', ('effects', ('font', ('size', 1.27, 1.27))))),
                (   'pin',
                    'input',
                    'line',
                    ('at', -5.08, 0, 0),
                    ('length', 5.715),
                    ('name', 'B', ('effects', ('font', ('size', 1.27, 1.27)))),
                    ('number', '2', ('effects', ('font', ('size', 1.27, 1.27))))),
                (   'pin',
                    'passive',
                    'line',
                    ('at', 2.54, 5.08, 270),
                    ('length', 2.54),
                    ('name', 'C', ('effects', ('font', ('size', 1.27, 1.27)))),
                    ('number', '3', ('effects', ('font', ('size', 1.27, 1.27)))))))
    """

    def _setup_traits(self):
        self.add_trait(
            has_defined_footprint(KicadFootprint("Package_TO_SOT_THT:TO-92_Inline"))
        )
        self.add_trait(
            has_defined_footprint_pinmap({1: self.IFs.E, 2: self.IFs.B, 3: self.IFs.C})
        )
        # self.add_trait(has_defined_kicad_ref("Q"))
        self.add_trait(has_defined_type_description("Q"))
        return

    def _setup_interfaces(self):
        self.IFs.add_all(times(0, Electrical))
        self.IFs.E = Electrical()
        self.IFs.B = Electrical()
        self.IFs.C = Electrical()

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        return self

    def __init__(self):
        super().__init__()

        self._setup_interfaces()
        self._setup_traits()