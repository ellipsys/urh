import copy
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom
from collections import defaultdict

import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal, Qt

from urh import constants
from urh.awre.FormatFinder import FormatFinder
from urh.cythonext import signalFunctions
from urh.cythonext.signalFunctions import Symbol

from urh.signalprocessing.MessageType import MessageType
from urh.signalprocessing.Modulator import Modulator
from urh.signalprocessing.Participant import Participant
from urh.signalprocessing.Message import Message
from urh.signalprocessing.Signal import Signal
from urh.signalprocessing.encoder import Encoder
from urh.cythonext import util
from urh.util.Logger import logger


class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class ProtocolAnalyzerSignals(QObject):
    protocol_updated = pyqtSignal()
    show_state_changed = pyqtSignal()
    data_sniffed = pyqtSignal(int)
    sniff_device_errors_changed = pyqtSignal(str)
    line_duplicated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)


class ProtocolAnalyzer(object):
    """
    The ProtocolAnalyzer is what you would refer to as "protocol".
    The data is stored in the messages variable.
    This class offers several methods for protocol analysis.
    """

    def __init__(self, signal: Signal):
        self.messages = []
        """:type: list of Message """

        self.used_symbols = set()
        """:type: set of Symbol """

        self.signal = signal
        self.filename = self.signal.filename if self.signal is not None else ""

        self.__name = "Blank"  # Fallback if Signal has no Name

        self.show = Qt.Checked  # Show in Compare Frame?
        self.qt_signals = ProtocolAnalyzerSignals()

        self.decoder = Encoder(["Non Return To Zero (NRZ)"]) # For Default Encoding of Protocol

        self.message_types = [MessageType("default")]

    @property
    def default_message_type(self) -> MessageType:
        if len(self.message_types) == 0:
            self.message_types.append(MessageType("default"))

        return self.message_types[0]

    @default_message_type.setter
    def default_message_type(self, val: MessageType):
        if len(self.message_types) > 0:
            self.message_types[0] = val
        else:
            self.message_types.append(val)

    @property
    def protocol_labels(self):
        return [lbl for message_type in self.message_types for lbl in message_type]

    def __deepcopy__(self, memo):
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k != "qt_signals" and k != "signal":
                setattr(result, k, copy.deepcopy(v, memo))
        result.signal = self.signal
        result.qt_signals = ProtocolAnalyzerSignals()
        return result

    @property
    def name(self):
        name = self.signal.name if self.signal is not None else self.__name
        return name

    @name.setter
    def name(self, val: str):
        if self.signal is None:
            self.__name = val
        else:
            self.signal.name = val

    @property
    def pauses(self):
        return [msg.pause for msg in self.messages]

    @property
    def plain_bits_str(self):
        return [str(msg) for msg in self.messages]

    @property
    def plain_hex_str(self):
        return [msg.plain_hex_str for msg in self.messages]

    @property
    def plain_ascii_str(self):
        return [msg.plain_ascii_str for msg in self.messages]

    @property
    def decoded_proto_bits_str(self):
        """

        :rtype: list of str
        """
        return [msg.decoded_bits_str for msg in self.messages]

    @property
    def decoded_hex_str(self):
        """

        :rtype: list of str
        """
        return [msg.decoded_hex_str for msg in self.messages]

    @property
    def decoded_ascii_str(self):
        """

        :rtype: list of str
        """
        return [msg.decoded_ascii_str for msg in self.messages]

    @property
    def num_messages(self):
        return len([msg for msg in self.messages if msg])

    def clear_decoded_bits(self):
        [msg.clear_decoded_bits() for msg in self.messages]

    def decoded_to_str_list(self, view_type):
        if view_type == 0:
            return self.decoded_proto_bits_str
        elif view_type == 1:
            return self.decoded_hex_str
        elif view_type == 2:
            return self.decoded_ascii_str

    def plain_to_string(self, view: int, show_pauses=True) -> str:
        """

        :param view: 0 - Bits ## 1 - Hex ## 2 - ASCII
        """
        time = constants.SETTINGS.value('show_pause_as_time', type=bool)
        if show_pauses and time and self.signal:
            srate = self.signal.sample_rate
        else:
            srate = None

        return '\n'.join(msg.view_to_string(view, False, show_pauses,
                                              sample_rate=srate
                                              ) for msg in self.messages)


    def plain_to_html(self, view, show_pauses=True) -> str:
        time = constants.SETTINGS.value('show_pause_as_time', type=bool)
        if show_pauses and time and self.signal:
            srate = self.signal.sample_rate
        else:
            srate = None

        result = []
        for message in self.messages:
            cur_str = ""
            if message.participant:
                color = constants.PARTICIPANT_COLORS[message.participant.color_index]
                red, green, blue  = color.red(), color.green(), color.blue()
                fgcolor = "#000000" if (red * 0.299 + green * 0.587 + blue * 0.114) > 186 else "#ffffff"
                cur_str += '<span style="background-color: rgb({0},{1},{2}); color: {3}">'.format(red, green, blue, fgcolor)

                #cur_str += '<span style="color: rgb({0},{1},{2})">'.format(red, green, blue)

            cur_str += message.view_to_string(view=view, decoded=False, show_pauses=False, sample_rate=srate)

            if message.participant:
                cur_str += '</span>'

            cur_str += message.get_pause_str(sample_rate=srate)
            result.append(cur_str)

        return "<br>".join(result)

    def set_decoder_for_messages(self, decoder: Encoder, messages=None):
        messages = messages if messages is not None else self.messages
        self.decoder = decoder
        for message in messages:
            message.decoder = decoder

    def get_protocol_from_signal(self):
        signal = self.signal
        if signal is None:
            self.messages = None
            return

        if self.messages is not None:
            self.messages[:] = []
        else:
            self.messages = []

        bit_len = signal.bit_len

        rel_symbol_len = self._read_symbol_len()
        self.used_symbols.clear()

        ppseq = signalFunctions.grab_pulse_lens(signal.qad,
                                                signal.qad_center,
                                                signal.tolerance,
                                                signal.modulation_type)

        bit_data, pauses, bit_sample_pos = self._ppseq_to_bits(ppseq, bit_len, rel_symbol_len)


        i = 0
        for bits, pause in zip(bit_data, pauses):
            middle_bit_pos = bit_sample_pos[i][int(len(bits) / 2)]
            start, end = middle_bit_pos, middle_bit_pos + bit_len
            rssi = np.mean(np.abs(signal._fulldata[start:end]))
            message = Message(bits, pause, message_type=self.default_message_type,
                              bit_len=bit_len, rssi=rssi, decoder=self.decoder, bit_sample_pos=bit_sample_pos[i])
            self.messages.append(message)
            i += 1

        self.qt_signals.protocol_updated.emit()

    def _read_symbol_len(self):
        settings = constants.SETTINGS
        if 'rel_symbol_length' in settings.allKeys():
            rel_symbol_len = settings.value('rel_symbol_length', type=int) / 200
        else:
            rel_symbol_len = 0.1
        return rel_symbol_len

    def _ppseq_to_bits(self, ppseq, bit_len: int, rel_symbol_len: float, write_bit_sample_pos=True):
        self.used_symbols.clear()
        bit_sampl_pos = []
        bit_sample_positions = []

        data_bits = []
        resulting_data_bits = []
        pauses = []
        start = 0
        total_samples = 0

        pause_type = 42
        zero_pulse_type = 0
        one_pulse_type = 1

        there_was_data = False
        lower_bit_bound = 0.5 - rel_symbol_len
        upper_bit_bound = 0.5 + rel_symbol_len
        avail_symbol_names = constants.SYMBOL_NAMES

        if len(ppseq) > 0 and ppseq[0, 0] == pause_type:
            start = 1  # Starts with Pause
            total_samples = ppseq[0, 1]

        for i in range(start, len(ppseq)):
            cur_pulse_type = ppseq[i, 0]
            num_samples = ppseq[i, 1]
            num_bits_floated = num_samples / bit_len
            num_bits = int(num_bits_floated)
            decimal_place = num_bits_floated - num_bits

            if decimal_place > upper_bit_bound:
                num_bits += 1
            elif lower_bit_bound < decimal_place < upper_bit_bound and \
                    (not cur_pulse_type == pause_type or num_bits < 9):
                ptype = 1 if cur_pulse_type == one_pulse_type else 0
                if not there_was_data:
                    there_was_data = bool(ptype)

                symbol = self.__find_matching_symbol(num_bits, ptype)
                if symbol is None:
                    symbol = self.__create_symbol(num_bits, ptype,
                                                  num_samples,
                                                  avail_symbol_names)

                data_bits.append(symbol)
                if write_bit_sample_pos:
                    bit_sampl_pos.append(total_samples)

                total_samples += num_samples
                continue

            if cur_pulse_type == pause_type:
                # OOK abdecken
                if num_bits < 9:
                    data_bits.extend([False] * num_bits)
                    if write_bit_sample_pos:
                        bit_sampl_pos.extend([total_samples + k * bit_len for k in range(num_bits)])

                elif not there_was_data:
                    # Ignore this pause, if there were no informations
                    # transmittted previously
                    data_bits[:] = []
                    bit_sampl_pos[:] = []

                else:
                    if write_bit_sample_pos:
                        bit_sampl_pos.append(total_samples)
                        bit_sampl_pos.append(total_samples + num_samples)
                        bit_sample_positions.append(bit_sampl_pos[:])
                        bit_sampl_pos[:] = []

                    resulting_data_bits.append(data_bits[:])
                    data_bits[:] = []
                    pauses.append(num_samples)
                    there_was_data = False

            elif cur_pulse_type == zero_pulse_type:
                data_bits.extend([False] * num_bits)
                if write_bit_sample_pos:
                    bit_sampl_pos.extend([total_samples + k * bit_len for k in range(num_bits)])

            elif cur_pulse_type == one_pulse_type:
                if not there_was_data:
                    there_was_data = num_bits > 0
                data_bits.extend([True] * num_bits)
                if write_bit_sample_pos:
                    bit_sampl_pos.extend([total_samples + k * bit_len for k in range(num_bits)])

            total_samples += num_samples

        if there_was_data:
            resulting_data_bits.append(data_bits[:])
            if write_bit_sample_pos:
                bit_sample_positions.append(bit_sampl_pos[:] + [total_samples])
            pause = ppseq[-1, 1] if ppseq[-1, 0] == pause_type else 0
            pauses.append(pause)

        return resulting_data_bits, pauses, bit_sample_positions

    def __find_matching_symbol(self, num_bits: int, pulsetype: int):
        for s in self.used_symbols:
            if s.nbits == num_bits and s.pulsetype == pulsetype:
                return s
        return None

    def __create_symbol(self, num_bits, ptype, num_samples, avail_symbol_names):
        name_index = len(self.used_symbols)
        if name_index > len(avail_symbol_names) - 1:
            name_index = len(avail_symbol_names) - 1
            print(
                "WARNING:"
                "Needed more symbols than names were available."
                "Symbols may be wrong labeled,"
                "consider extending the symbol alphabet.")

        symbol = Symbol(avail_symbol_names[name_index],
                        num_bits, ptype, num_samples)

        self.used_symbols.add(symbol)
        return symbol

    def get_samplepos_of_bitseq(self, startmessage: int, startindex: int,
                                endmessage: int, endindex: int,
                                include_pause: bool):
        """
        Determine on which place (regarding samples) a bit sequence is
        :rtype: tuple[int,int]
        """
        lookup = {i: message.bit_sample_pos for i, message in enumerate(self.messages)}
        try:
            if startmessage > endmessage:
                startmessage, endmessage = endmessage, startmessage

            if startindex >= len(lookup[startmessage]) - 1:
                startindex = len(lookup[startmessage]) - 1
                if not include_pause:
                    startindex -= 1

            if endindex >= len(lookup[endmessage]) - 1:
                endindex = len(lookup[endmessage]) - 1
                if not include_pause:
                    endindex -= 1

            start = lookup[startmessage][startindex]
            end = lookup[endmessage][endindex] - start

            return start, end
        except KeyError:
            return  -1, -1

    def get_bitseq_from_selection(self, selection_start: int, selection_width: int, bitlen: int):
        """
        Holt Start und Endindex der Bitsequenz von der Selektion der Samples

        :param selection_start: Selektionsstart in Samples
        :param selection_width: Selektionsende in Samples
        :rtype: tuple[int,int,int,int]
        :return: Startmessage, Startindex, Endmessage, Endindex
        """
        start_message = -1
        start_index = -1
        end_message = -1
        end_index = -1
        lookup =  [msg.bit_sample_pos for msg in self.messages]
        if not lookup:
            return -1, -1, -1, -1

        if selection_start + selection_width < lookup[0][0] or selection_width < bitlen:
            return start_message, start_index, end_message, end_index

        for j, msg_sample_pos in enumerate(lookup):
            if msg_sample_pos[-2] < selection_start:
                continue
            elif start_message == -1:
                start_message = j
                for i, sample_pos in enumerate(msg_sample_pos):
                    if sample_pos < selection_start:
                        continue
                    elif start_index == -1:
                        start_index = i
                        if msg_sample_pos[-1] - selection_start < selection_width:
                            break
                    elif sample_pos - selection_start > selection_width:
                        end_message = j
                        end_index = i
                        return start_message, start_index, end_message, end_index
            elif msg_sample_pos[-1] - selection_start < selection_width:
                continue
            else:
                end_message = j
                for i, sample_pos in enumerate(msg_sample_pos):
                    if sample_pos - selection_start > selection_width:
                        end_index = i
                        return start_message, start_index, end_message, end_index

        last_message = len(lookup) - 1
        last_index = len(lookup[last_message]) - 1
        return start_message, start_index, last_message, last_index

    def delete_messages(self, msg_start: int, msg_end: int, start: int, end: int, view: int, decoded: bool):
        removable_msg_indices = []

        for i in range(msg_start, msg_end + 1):
            try:
                self.messages[i].clear_decoded_bits()
                bs, be = self.convert_range(start, end, view, 0, decoded, message_indx=i)
                del self.messages[i][bs:be + 1]
                if len(self.messages[i]) == 0:
                    removable_msg_indices.append(i)
            except IndexError:
                continue

        # Remove empty messages and Pause after empty message
        for i in reversed(removable_msg_indices):
            del self.messages[i]

    def convert_index(self, index: int, from_view: int, to_view: int, decoded: bool, message_indx=-1) -> tuple:
        """
        Konvertiert einen Index aus der einen Sicht (z.B. Bit) in eine andere (z.B. Hex)

        :param message_indx: if -1, the message with max length is chosen
        :return:
        """
        if len(self.messages) == 0:
            return 0, 0

        if message_indx == -1:
            message_indx = self.messages.index(max(self.messages, key=len)) # Longest message

        if message_indx >= len(self.messages):
            message_indx = len(self.messages) - 1

        return self.messages[message_indx].convert_index(index, from_view, to_view, decoded)

    def convert_range(self, index1: int, index2: int, from_view: int,
                      to_view: int, decoded: bool, message_indx=-1):
        if len(self.messages) == 0:
            return 0, 0

        if message_indx == -1:
            message_indx = self.messages.index(max(self.messages, key=len)) # Longest message

        if message_indx >= len(self.messages):
            message_indx = len(self.messages) - 1

        return self.messages[message_indx].convert_range(index1, index2, from_view, to_view, decoded)

    def find_differences(self, refindex: int, view: int):
        """
        Search all differences between protocol messages regarding a reference message

        :param refindex: index of reference message
        :rtype: dict[int, set[int]]
        """
        differences = defaultdict(set)

        if refindex >= len(self.messages):
            return differences

        if view == 0:
            proto = self.decoded_proto_bits_str
        elif view == 1:
            proto = self.decoded_hex_str
        elif view == 2:
            proto = self.decoded_ascii_str
        else:
            return differences

        refmessage = proto[refindex]
        len_refmessage = len(refmessage)


        for i, message in enumerate(proto):
            if i == refindex:
                continue

            diff_cols = set()

            for j, value in enumerate(message):
                if j >= len_refmessage:
                    break

                if value != refmessage[j]:
                    diff_cols.add(j)

            len_message = len(message)
            if len_message != len_refmessage:
                len_diff = abs(len_refmessage - len_message)
                start = len_refmessage
                if len_refmessage > len_message:
                    start = len_message
                end = start + len_diff
                for k in range(start, end):
                    diff_cols.add(k)

            differences[i] = diff_cols

        return differences

    def estimate_frequency_for_one(self, sample_rate: float, nbits=42) -> float:
        """
        Calculates the frequency of at most nbits logical ones and returns the mean of these frequencies

        :param nbits:
        :return:
        """
        return self.__estimate_frequency_for_bit(True, sample_rate, nbits)

    def estimate_frequency_for_zero(self, sample_rate: float, nbits=42) -> float:
        """
        Calculates the frequency of at most nbits logical zeros and returns the mean of these frequencies

        :param nbits:
        :return:
        """
        return self.__estimate_frequency_for_bit(False, sample_rate, nbits)

    def __estimate_frequency_for_bit(self, bit: bool, sample_rate: float, nbits: int) -> float:
        if nbits == 0:
            return 0

        assert self.signal is not None
        freqs = []
        for i, message in enumerate(self.messages):
            for j, msg_bit in enumerate(message.plain_bits):
                if msg_bit == bit:
                    start, nsamples = self.get_samplepos_of_bitseq(i, j, i, j + 1, False)
                    freq = self.signal.estimate_frequency(start, start + nsamples, sample_rate)
                    freqs.append(freq)
                    if len(freqs) == nbits:
                        return np.mean(freqs)
        if freqs:
            return np.mean(freqs)
        else:
            return 0


    def __str__(self):
        return "ProtoAnalyzer " + self.name

    def set_labels(self, val):
        self._protocol_labels = val

    def add_new_message_type(self, labels):
        names = set(message_type.name for message_type in self.message_types)
        name = "Message type #"
        i = 0
        while True:
            i += 1
            if name + str(i) not in names:
                self.message_types.append(MessageType(name=name + str(i), iterable=[copy.deepcopy(lbl) for lbl in labels]))
                break

    def to_xml_tag(self, decodings, participants, tag_name="protocol", include_message_type=False, write_bits=False) -> ET.Element:
        root = ET.Element(tag_name)

        # Save modulators
        if hasattr(self, "modulators"): # For protocol analyzer container
            modulators_tag = ET.SubElement(root, "modulators")
            for i, modulator in enumerate(self.modulators):
                modulators_tag.append(modulator.to_xml(i))

        # Save symbols
        if len(self.used_symbols) > 0:
            symbols_tag = ET.SubElement(root, "symbols")
            for symbol in self.used_symbols:
                ET.SubElement(symbols_tag, "symbol",
                              attrib={"name": symbol.name, "pulsetype": str(symbol.pulsetype),
                                      "nbits": str(symbol.nbits), "nsamples": str(symbol.nsamples)})

        # Save decodings
        if not decodings:
            decodings = []
            for message in self.messages:
                if message.decoder not in decodings:
                    decodings.append(message.decoder)

        decodings_tag = ET.SubElement(root, "decodings")
        for decoding in decodings:
            dec_str = ""
            for chn in decoding.get_chain():
                dec_str += repr(chn) + ", "
            dec_tag = ET.SubElement(decodings_tag, "decoding")
            dec_tag.text = dec_str

        # Save participants
        if not participants:
            participants = []
            for message in self.messages:
                if message.participant and message.participant not in participants:
                    participants.append(message.participant)

        participants_tag = ET.SubElement(root, "participants")
        for participant in participants:
            participants_tag.append(participant.to_xml())

        # Save data
        data_tag = ET.SubElement(root, "messages")
        for i, message in enumerate(self.messages):
            message_tag = message.to_xml(decoders=decodings, include_message_type=include_message_type)
            if write_bits:
                message_tag.set("bits", message.plain_bits_str)
            data_tag.append(message_tag)

        # Save message types separatively as not saved in messages already
        if not include_message_type:
            message_types_tag = ET.SubElement(root, "message_types")
            for message_type in self.message_types:
                message_types_tag.append(message_type.to_xml())

        return root

    def to_xml_file(self, filename: str, decoders, participants, tag_name="protocol", include_message_types=False, write_bits=False):
        tag = self.to_xml_tag(decodings=decoders, participants=participants, tag_name=tag_name, include_message_type=include_message_types, write_bits=write_bits)

        xmlstr = minidom.parseString(ET.tostring(tag)).toprettyxml(indent="   ")
        with open(filename, "w") as f:
            for line in xmlstr.split("\n"):
                if line.strip():
                    f.write(line+"\n")


    def from_xml_tag(self, root: ET.Element, read_bits=False, participants=None, decodings=None):
        if not root:
            return None

        if root.find("modulators") and hasattr(self, "modulators"):
            self.modulators[:] = []
            for mod_tag in root.find("modulators").findall("modulator"):
                self.modulators.append(Modulator.from_xml(mod_tag))

        decoders = self.read_decoders_from_xml_tag(root) if decodings is None else decodings

        self.used_symbols.clear()
        try:
            for symbol_tag in root.find("symbols").findall("symbol"):
                s = Symbol(symbol_tag.get("name"), int(symbol_tag.get("nbits")),
                           int(symbol_tag.get("pulsetype")), int(symbol_tag.get("nsamples")))
                self.used_symbols.add(s)
        except AttributeError:
            pass

        if participants is None:
            participants = self.read_participants_from_xml_tag(root)


        if read_bits:
            self.messages[:] = []

        try:
            message_types = []
            for message_type_tag in root.find("message_types").findall("message_type"):
                message_types.append(MessageType.from_xml(message_type_tag))
        except AttributeError:
            message_types = []


        for message_type in message_types:
            if message_type not in self.message_types:
                self.message_types.append(message_type)

        try:
            message_tags = root.find("messages").findall("message")
            for i, message_tag in enumerate(message_tags):
                if read_bits:
                    message = Message.from_plain_bits_str(bits=message_tag.get("bits"),
                                                        symbols={s.name: s for s in self.used_symbols})
                    message.from_xml(tag=message_tag, participants=participants, decoders=decoders, message_types=self.message_types)
                    self.messages.append(message)
                else:
                    self.messages[i].from_xml(tag=message_tag, participants=participants, decoders=decoders, message_types=self.message_types)

        except AttributeError:
            pass

    def read_participants_from_xml_tag(self, root: ET.Element):
        try:
            participants = []
            for parti_tag in root.find("participants").findall("participant"):
                participants.append(Participant.from_xml(parti_tag))
            return participants
        except AttributeError:
            logger.warning("no participants found in xml")
            return []

    def read_decoders_from_xml_tag(self, root: ET.Element):
        try:
            decoders = []
            for decoding_tag in root.find("decodings").findall("decoding"):
                conf = [d.strip().replace("'", "") for d in decoding_tag.text.split(",") if d.strip().replace("'", "")]
                decoders.append(Encoder(conf))
            return decoders
        except AttributeError:
            logger.error("no decodings found in xml")
            return []


    def from_xml_file(self, filename: str, read_bits=False):
        try:
            tree = ET.parse(filename)
        except FileNotFoundError:
            logger.error("Could not find file "+filename)
            return
        except ET.ParseError:
            logger.error("Could not parse file " + filename)
            return

        root = tree.getroot()
        self.from_xml_tag(root, read_bits=read_bits)


    def destroy(self):
        try:
            for message_type in self.message_types:
                message_type.clear()
        except TypeError:
            pass  # No message types defined
        self.message_types = []
        self.messages = None

    def update_auto_message_types(self):
        for message in self.messages:
            for message_type in (msg_type for msg_type in self.message_types if msg_type.assigned_by_ruleset):
                if message_type.ruleset.applies_for_message(message):
                    message.message_type = message_type
                    break

    def auto_assign_participants(self, participants):
        """

        :type participants: list of Participant
        :return:
        """
        if len(participants) == 0:
            return

        if len(participants) == 1:
            for message in self.messages:
                message.participant = participants[0]
            return

        rssis = np.array([msg.rssi for msg in self.messages], dtype=np.float32)
        min_rssi, max_rssi = util.minmax(rssis)
        center_spacing = (max_rssi - min_rssi) / (len(participants) - 1)
        centers = [min_rssi + i*center_spacing for i in range(0, len(participants))]
        rssi_assigned_centers = []

        for rssi in rssis:
            center_index = 0
            diff = 999
            for i, center in enumerate(centers):
                if abs(center-rssi) < diff:
                    center_index = i
                    diff = abs(center-rssi)
            rssi_assigned_centers.append(center_index)

        participants.sort(key=lambda participant: participant.relative_rssi)
        for message, center_index in zip(self.messages, rssi_assigned_centers):
            if message.participant is None:
                message.participant = participants[center_index]

    def auto_assign_decodings(self, decodings):
        """
        :type decodings: list of Encoder
        """
        nrz_decodings = [decoding for decoding in decodings if decoding.is_nrz or decoding.is_nrzi]
        fallback = nrz_decodings[0] if nrz_decodings else None
        candidate_decodings = [decoding for decoding in decodings
                               if decoding not in nrz_decodings and not decoding.contains_cut]

        for message in self.messages:
            decoder_found = False

            for decoder in candidate_decodings:
                if decoder.applies_for_message(message.plain_bits):
                    message.decoder = decoder
                    decoder_found = True
                    break

            if not decoder_found and fallback:
                message.decoder = fallback

    def auto_assign_labels(self):
        format_finder = FormatFinder(self)

        # TODO Perform multiple iterations with varying priorities
        format_finder.perform_iteration()