from __future__ import division, unicode_literals, print_function, absolute_import
#from labscript_utils import PY2
#if PY2:
#    str = unicode

from labscript_devices import runviewer_parser, BLACS_tab
from labscript_devices import DDSAD9954
from labscript_devices.RepumpDDS import  RepumpDDS
from labscript import IntermediateDevice, Device, config, LabscriptError, set_passed_properties
from labscript_utils.unitconversions import NovaTechDDS9mFreqConversion, NovaTechDDS9mAmpConversion

import numpy as np
import labscript_utils.h5_lock, h5py
import labscript_utils.properties

bauds = {9600: b'Kb 78',
         19200: b'Kb 3c',
         38400: b'Kb 1e',
         57600: b'Kb 14',
         115200: b'Kb 0a'}

class Arduino_Repump_DDS(IntermediateDevice):
    description = 'Arduino_Repump_DDS'
    allowed_children = [RepumpDDS]
    clock_limit = 9990#I need to find out what this would be for the Arduino

    @set_passed_properties(
        property_names = {'connection_table_properties': ['com_port', 'baud_rate', 'default_baud_rate', 'update_mode',
        'synchronous_first_line_repeat']}#I'm not sure which of these I'll keep
        )
    def __init__(self, name, parent_device,
                 com_port = '', baud_rate=9600, default_baud_rate = None, update_mode='synchronous',
                 synchronous_first_line_repeat = False, **kwargs):

        IntermediateDevice.__init__(self, name, parent_device, **kwargs)
        self.BLACS_connection = '%s,%s'%(com_port, str(baud_rate))

        if not update_mode in ['synchronous', 'asyncronous']:
            raise LabscriptError('update_mode must be \'synchronous\' or \'asynchronous\'')

        if not baud_rate in bauds:
            raise LabscriptError('baud_rate must be one of {0}'.format(list(bauds)))

        if not default_baud_rate in bauds and default_baud_rate is not None:
            raise LabscriptError('default_baud_rate must be one of {0} or None (to indicate no default)'.format(list(bauds)))

        self.update_mode = update_mode
        self.synchronous_first_line_repeat = synchronous_first_line_repeat

    def add_device(self, device):
        Device.add_device(self, device)
        # The Novatech doesn't support 0Hz output; set the default frequency of the DDS to 0.1 Hz:
        device.frequency0.default_value = 1
        device.amplitude0.default_value = 10
        device.frequency1.default_value = 1
        device.amplitude1.default_value = 10
        device.frequency2.default_value = 1
        device.amplitude2.default_value = 10
        device.frequency3.default_value = 1
        device.amplitude3.default_value = 10
        device.frequency4.default_value = 1
        device.amplitude4.default_value = 10
        device.frequency5.default_value = 1
        device.amplitude5.default_value = 10
        device.frequency6.default_value = 1
        device.amplitude6.default_value = 10
        device.frequency7.default_value = 1
        device.amplitude7.default_value = 10
        device.usedfreqs.default_value = 0
        device.delaytime.default_value = 20

    def get_default_unit_conversion_classes(self, device):
        return NovaTechDDS9mFreqConversion #Check up on this and make these files?

    def quantise_freq(self, data, device):
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        if np.any(data > 160e6) or np.any(data < 0.1):
            raise LabscriptError('%s %s'%(device.description, device.name) + 'can only have frequencies between 0.1Hz and 160MHz')
        data = np.array(data,dtype=np.uint32)
        return data

    def quantise_usedfreqs(self, data, device):
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        if np.any(data > 8) or np.any(data < 0):
            raise LabscriptError('%s %s'%(device.description, device.name) + 'must use between 0 and 8 frequencies')
        data = np.array(data,dtype=np.uint32)
        return data

    def quantise_delaytime(self, data, device):
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        if np.any(data < 1):
            raise LabscriptError('%s %s'%(device.description, device.name) + 'I decided that the duration must be at least 1')
        data = np.array(data,dtype=np.uint32)
        return data

    def quantise_amp(self, data, device):
        if not isinstance(data, np.ndarray):
            data = np.array(data)
        if np.any(data > 100) or np.any(data < 0):
            raise LabscriptError('%s %s'%(device.description, device.name) + 'not a valid amplitude')
        data = np.array(data,dtype=np.uint8)
        return data

    def generate_code(self, hdf5_file):
        DDSs = {}
        for output in self.child_devices:
            # Check that the instructions will fit into RAM:
            # if isinstance(output, DDSAD9954) and len(output.frequency.raw_output) > 16384 - 2: # -2 to include space for dummy instructions, not sure if this holds for arduinos
            #     raise LabscriptError('%s can only support 16383 instructions. '%self.name +
            #                          'Please decrease the sample rates of devices on the same clock, ' +
            #                          'or connect %s to a different pseudoclock.'%self.name)
            try:
                prefix, channel = output.connection.split()
                channel = int(channel)
            except:
                raise LabscriptError('%s %s has invalid connection string: \'%s\'. '%(output.description,output.name,str(output.connection)) +
                                     'Format must be \'channel n\' with n from 0 to 2.')
            DDSs[channel] = output
        for connection in DDSs:
            if connection in range(len(self.child_devices)):
                # Dynamic DDS
                dds = DDSs[connection]
                dds.frequency0.raw_output = self.quantise_freq(dds.frequency0.raw_output, dds)
                dds.frequency1.raw_output = self.quantise_freq(dds.frequency1.raw_output, dds)
                dds.frequency2.raw_output = self.quantise_freq(dds.frequency2.raw_output, dds)
                dds.frequency3.raw_output = self.quantise_freq(dds.frequency3.raw_output, dds)
                dds.frequency4.raw_output = self.quantise_freq(dds.frequency4.raw_output, dds)
                dds.frequency5.raw_output = self.quantise_freq(dds.frequency5.raw_output, dds)
                dds.frequency6.raw_output = self.quantise_freq(dds.frequency6.raw_output, dds)
                dds.frequency7.raw_output = self.quantise_freq(dds.frequency7.raw_output, dds)
                dds.amplitude0.raw_output = self.quantise_amp(dds.amplitude0.raw_output, dds)
                dds.amplitude1.raw_output = self.quantise_amp(dds.amplitude1.raw_output, dds)
                dds.amplitude2.raw_output = self.quantise_amp(dds.amplitude2.raw_output, dds)
                dds.amplitude3.raw_output = self.quantise_amp(dds.amplitude3.raw_output, dds)
                dds.amplitude4.raw_output = self.quantise_amp(dds.amplitude4.raw_output, dds)
                dds.amplitude5.raw_output = self.quantise_amp(dds.amplitude5.raw_output, dds)
                dds.amplitude6.raw_output = self.quantise_amp(dds.amplitude6.raw_output, dds)
                dds.amplitude7.raw_output = self.quantise_amp(dds.amplitude7.raw_output, dds)
                dds.usedfreqs.raw_output = self.quantise_usedfreqs(dds.usedfreqs.raw_output, dds)
                dds.delaytime.raw_output = self.quantise_delaytime(dds.delaytime.raw_output, dds)


            # elif connection in range(2,4):
                # # StaticDDS:
                # dds = DDSs[connection]
                # dds.frequency.raw_output, dds.frequency.scale_factor = self.quantise_freq(dds.frequency.static_value, dds)
                # dds.phase.raw_output, dds.phase.scale_factor = self.quantise_phase(dds.phase.static_value, dds)
                # dds.amplitude.raw_output, dds.amplitude.scale_factor = self.quantise_amp(dds.amplitude.static_value, dds)
            else:
                raise LabscriptError('%s %s has invalid connection string: \'%s\'. '%(dds.description,dds.name,str(dds.connection)) +
                                     'Format must be \'channel n\' with n from 0 to 2.')

        dtypes = [('freq',np.uint32)] + \
                 [('frequency%d'%i,np.uint32) for i in range(1,8)] + \
                 [('amplitude%d'%i,np.uint32) for i in range(8)] + \
                 [('usedfreqs',np.uint32)] + \
                 [('delaytime',np.uint32)]

        clockline = self.parent_clock_line
        pseudoclock = clockline.parent_device
        times = pseudoclock.times[clockline]

        out_table = np.zeros(len(times),dtype=dtypes)

        for connection in range(len(self.child_devices)):
            if not connection in DDSs:
                continue
            dds = DDSs[connection]
            # The last two instructions are left blank, for BLACS
            # to fill in at program time.
            out_table['freq'][:] = dds.frequency0.raw_output
            out_table['frequency1'][:] = dds.frequency1.raw_output
            out_table['frequency2'][:] = dds.frequency2.raw_output
            out_table['frequency3'][:] = dds.frequency3.raw_output
            out_table['frequency4'][:] = dds.frequency4.raw_output
            out_table['frequency5'][:] = dds.frequency5.raw_output
            out_table['frequency6'][:] = dds.frequency6.raw_output
            out_table['frequency7'][:] = dds.frequency7.raw_output
            out_table['amplitude0'][:] = dds.amplitude0.raw_output
            out_table['amplitude1'][:] = dds.amplitude1.raw_output
            out_table['amplitude2'][:] = dds.amplitude2.raw_output
            out_table['amplitude3'][:] = dds.amplitude3.raw_output
            out_table['amplitude4'][:] = dds.amplitude4.raw_output
            out_table['amplitude5'][:] = dds.amplitude5.raw_output
            out_table['amplitude6'][:] = dds.amplitude6.raw_output
            out_table['amplitude7'][:] = dds.amplitude7.raw_output
            out_table['usedfreqs'][:] = dds.usedfreqs.raw_output
            out_table['delaytime'][:] = dds.delaytime.raw_output


        if self.update_mode == 'asynchronous' or self.synchronous_first_line_repeat:
            # Duplicate the first line of the table. Otherwise, we are one step
            # ahead in the table from the start of a run. In asynchronous
            # updating mode, this is necessary since the first line of the
            # table is already being output before the first trigger from
            # the master clock. When using a simple delay line for synchronous
            # output, this also seems to be required, in which case
            # synchronous_first_line_repeat should be set to True.
            # However, when a tristate driver is used as described at
            # http://labscriptsuite.org/blog/implementation-of-the-novatech-dds9m/
            # then is is not neccesary to duplicate the first line. Use of a
            # tristate driver in this way is the correct way to use
            # the novatech DDS, as per its instruction manual, and so is likely
            # to be the most reliable. However, through trial and error we've
            # determined that duplicating the first line like this gives correct
            # output in asynchronous mode and in synchronous mode when using a
            # simple delay line, at least for the specific device we tested.
            # Your milage may vary.
            out_table = np.concatenate([out_table[0:1], out_table])

        grp = self.init_device_group(hdf5_file)
        grp.create_dataset('TABLE_DATA',compression=config.compression,data=out_table)
        self.set_property('frequency_scale_factor', 1, location='device_properties')



import time

from blacs.tab_base_classes import Worker, define_state
from blacs.tab_base_classes import MODE_MANUAL, MODE_TRANSITION_TO_BUFFERED, MODE_TRANSITION_TO_MANUAL, MODE_BUFFERED

from blacs.device_base_class import DeviceTab

@BLACS_tab
class Arduino__Repump_DDSTab(DeviceTab):
    def initialise_GUI(self):
        # Capabilities
        self.base_units =    {'freq':'Hz', 'frequency1':'Hz', 'frequency2':'Hz', 'frequency3':'Hz', 'frequency4':'Hz', 'frequency5':'Hz', 'frequency6':'Hz', 'frequency7':'Hz',
                              'amplitude0':'', 'amplitude1':'', 'amplitude2':'', 'amplitude3':'', 'amplitude4':'', 'amplitude5':'', 'amplitude6':'', 'amplitude7':'', 'usedfreqs':'', 'delaytime':''}
        self.base_min =      {'freq':0, 'frequency1':0, 'frequency2':0, 'frequency3':0, 'frequency4':0, 'frequency5':0, 'frequency6':0, 'frequency7':0,
                              'amplitude0':0, 'amplitude1':0, 'amplitude2':0, 'amplitude3':0, 'amplitude4':0, 'amplitude5':0, 'amplitude6':0, 'amplitude7':0, 'usedfreqs':1, 'delaytime':0}
        self.base_max =      {'freq':160.0*10.0**6, 'frequency1':160.0*10.0**6, 'frequency2':160.0*10.0**6, 'frequency3':160.0*10.0**6, 'frequency4':160.0*10.0**6, 'frequency5':160.0*10.0**6, 'frequency6':160.0*10.0**6, 'frequency7':160.0*10.0**6,
                              'amplitude0':100, 'amplitude1':100, 'amplitude2':100, 'amplitude3':100, 'amplitude4':100, 'amplitude5':100, 'amplitude6':100, 'amplitude7':100, 'usedfreqs':8, 'delaytime':1000}
        self.base_step =      {'freq':1, 'frequency1':100, 'frequency2':100, 'frequency3':100, 'frequency4':100, 'frequency5':100, 'frequency6':100, 'frequency7':100,
                              'amplitude0':1, 'amplitude1':1, 'amplitude2':1, 'amplitude3':1, 'amplitude4':1, 'amplitude5':1, 'amplitude6':1, 'amplitude7':1, 'usedfreqs':1, 'delaytime':1}
        self.base_decimals = {'freq':1, 'frequency1':1, 'frequency2':1, 'frequency3':1, 'frequency4':1, 'frequency5':1, 'frequency6':1, 'frequency7':1,
                              'amplitude0':1, 'amplitude1':1, 'amplitude2':1, 'amplitude3':1, 'amplitude4':1, 'amplitude5':1, 'amplitude6':1, 'amplitude7':1, 'usedfreqs':1, 'delaytime':1}
        self.num_DDS = 1

        # Create DDS Output objects
        dds_prop = {}
        for i in range(8):
            dds_prop['freq%d' % i] = {}
            dds_prop['freq%d' % i]['freq'] = {'base_unit': 'MHz',
                                      'min': 20,
                                      'max': 2000,
                                      'step': 1,
                                      'decimals': 0}
            dds_prop['freq%d' % i]['amp'] = {'base_unit': 'arb',
                              'min': 8,
                              'max': 15,
                              'step': 0.1,
                              'decimals': 1}
        # dds_prop['frequency'] = {}
        # for subchnl in ['freq', 'frequency1', 'frequency2', 'frequency3', 'frequency4', 'frequency5', 'frequency6', 'frequency7',
        #                 'amplitude0', 'amplitude1', 'amplitude2', 'amplitude3', 'amplitude4', 'amplitude5', 'amplitude6', 'amplitude7', 'usedfreqs', 'delaytime']:
        #     dds_prop['channel 0'][subchnl] = {'base_unit':self.base_units[subchnl],
        #                                              'min':self.base_min[subchnl],
        #                                              'max':self.base_max[subchnl],
        #                                              'step':self.base_step[subchnl],
        #                                              'decimals':self.base_decimals[subchnl]
        #                                             }
        ao_prop = {}
        ao_prop['numFreq'] = {'base_unit': 'arb',
                          'min': 1,
                          'max': 8,
                          'step': 1,
                          'decimals': 0}
        ao_prop['delayTime'] = {'base_unit': 'ms',
                            'min': 20,
                            'max': 100,
                            'step': 1,
                            'decimals': 0}
        # Create the output objects
        self.create_dds_outputs(dds_prop)
        self.create_analog_outputs(ao_prop)
        #self.create_digital_outputs(do_prop)
        # Create widgets for output objects
        dds_widgets,ao_widgets,do_widgets = self.auto_create_widgets()
        #ao_widgets = self.auto_create_widgets()
        # and auto place the widgets in the UI
        self.auto_place_widgets(("DDS Outputs",dds_widgets))
        self.auto_place_widgets(("Analog Outs",ao_widgets))
        #self.auto_place_widgets(("Digital Outs",do_widgets))

        connection_object = self.settings['connection_table'].find_by_name(self.device_name)
        connection_table_properties = connection_object.properties

        self.com_port = connection_table_properties.get('com_port', None)
        self.baud_rate = connection_table_properties.get('baud_rate', None)
        self.default_baud_rate = connection_table_properties.get('default_baud_rate', None)
        self.update_mode = connection_table_properties.get('update_mode', 'synchronous')

        # Backward compat:
        blacs_connection =  str(connection_object.BLACS_connection)
        if ',' in blacs_connection:
            com_port, baud_rate = blacs_connection.split(',')
            if self.com_port is None:
                self.com_port = com_port
            if self.baud_rate is None:
                self.baud_rate = int(baud_rate)
        else:
            self.com_port = blacs_connection
            self.baud_rate = 115200



        # Create and set the primary worker
        self.create_worker("main_worker",Arduino_Repump_DDSWorker,{'com_port':self.com_port,
                                                              'baud_rate': self.baud_rate,
                                                              'default_baud_rate': self.default_baud_rate,
                                                              'update_mode': self.update_mode})
        self.primary_worker = "main_worker"

        # Set the capabilities of this device
        self.supports_remote_value_check(False)
        self.supports_smart_programming(False)


class Arduino_Repump_DDSWorker(Worker):
    def init(self):
        global serial; import serial
        global socket; import socket
        global h5py; import labscript_utils.h5_lock, h5py
        self.smart_cache = {'STATIC_DATA': None, 'TABLE_DATA': ''}

        if self.default_baud_rate is not None:
            initial_baud_rate = self.default_baud_rate
        else:
            initial_baud_rate = self.baud_rate

        self.connection = serial.Serial(
            self.com_port, baudrate=initial_baud_rate, timeout=0.1
        )

    def program_manual(self,front_panel_values):
        # TODO: Optimise this so that only items that have changed are reprogrammed by storing the last programmed values
        # For each DDS channel,
        for i in range(1):
            # and for each subchnl in the DDS,
            self.connection.write(b'@ %d\r\n'%i)
            #if front_panel_values['channel %d'%i]['rampon'] == 1:
            #    ramplow = front_panel_values['channel %d'%i]['ramplow']
            #    ramphigh = front_panel_values['channel %d'%i]['ramphigh']
            #    rampdur = front_panel_values['channel %d'%i]['rampdur']
            #    self.connection.write(b'r %f %f %f\r\n'%(ramplow, ramphigh, rampdur))
            #else:
            self.program_static(i,front_panel_values)
        self.connection.write(b'$\r\n')

    def program_static(self,channel,front_panel_values):
        values = (#651,12.2,1242,13,1510,10,1720,8,800,10,1150,10,1300,10,10,0,4,20
                  front_panel_values['freq0']['freq'],
                  front_panel_values['freq0']['amp'],
                  front_panel_values['freq1']['freq'],
                  front_panel_values['freq1']['amp'],
                  front_panel_values['freq2']['freq'],
                  front_panel_values['freq2']['amp'],
                  front_panel_values['freq3']['freq'],
                  front_panel_values['freq3']['amp'],
                  front_panel_values['freq4']['freq'],
                  front_panel_values['freq4']['amp'],
                  front_panel_values['freq5']['freq'],
                  front_panel_values['freq5']['amp'],
                  front_panel_values['freq6']['freq'],
                  front_panel_values['freq6']['amp'],
                  front_panel_values['freq7']['freq'],
                  front_panel_values['freq7']['amp'],
                  front_panel_values['numFreq'],
                  front_panel_values['delayTime'],
        )
        command = b'MF2 %d %f %d %f %d %f %d %f %d %f %d %f %d %f %d %f %d %d\r\n'%values
        print(command)
        print(front_panel_values)
        self.connection.write(command)
        self.connection.write(b"$")
        print(self.connection.read(1000))

        # Now that a static update has been done, we'd better invalidate the saved STATIC_DATA:
        self.smart_cache['STATIC_DATA'] = None

    def transition_to_buffered(self,device_name,h5file,initial_values,fresh):

        # Pretty please reset your memory pointer to zero:

        # Store the initial values in case we have to abort and restore them:
        # Store the final values to for use during transition_to_static:
        self.final_values = {}
        table_data = None
        with h5py.File(h5file) as hdf5_file:
            group = hdf5_file['/devices/'+device_name]
            # Now program the buffered outputs:
            if 'TABLE_DATA' in group:
                table_data = group['TABLE_DATA'][:]


        # Now program the buffered outputs:

        if table_data is not None:
            data = table_data
            for ddsno in range(1):
                self.connection.write(b'@ %d\r\n'%ddsno)
                for i, line in enumerate(data):
                    oldtable = self.smart_cache['TABLE_DATA']
                    if fresh or i >= len(oldtable) or (line['freq'], line['amplitude0'], line['frequency1'], line['amplitude1'],
                                                       line['frequency2'], line['amplitude2'], line['frequency3'], line['amplitude3'],
                                                       line['frequency4'], line['amplitude4'], line['frequency5'], line['amplitude5'],
                                                       line['frequency6'], line['amplitude6'], line['frequency7'], line['amplitude7'],
                                                       line['usedfreqs'], line['delaytime']) != (oldtable[i]['freq'], oldtable[i]['amplitude0'], oldtable[i]['frequency1'], oldtable[i]['amplitude1'],
                                                                                          oldtable[i]['frequency2'], oldtable[i]['amplitude2'], oldtable[i]['frequency3'], oldtable[i]['amplitude3'],
                                                                                          oldtable[i]['frequency4'], oldtable[i]['amplitude4'], oldtable[i]['frequency5'], oldtable[i]['amplitude5'],
                                                                                          oldtable[i]['frequency6'], oldtable[i]['amplitude6'], oldtable[i]['frequency7'], oldtable[i]['amplitude7'],
                                                                                          oldtable[i]['usedfreqs'], oldtable[i]['delaytime']):
                        # if line['rampon%d'%ddsno] == 1:
                        #     self.connection.write(b'r %f %f %f\r\n'%(line['ramplow%d'%ddsno], line['ramphigh%d'%ddsno], line['rampdur%d'%ddsno]))
                        # else:
                        self.connection.write(b'MF2 %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f %f\r\n'%(line['freq'], line['amplitude0'], line['frequency1'], line['amplitude1'],
                                                           line['frequency2'], line['amplitude2'], line['frequency3'], line['amplitude3'],
                                                           line['frequency4'], line['amplitude4'], line['frequency5'], line['amplitude5'],
                                                           line['frequency6'], line['amplitude6'], line['frequency7'], line['amplitude7'],
                                                           line['usedfreqs'], line['delaytime']))

            # Store the table for future smart programming comparisons:
            try:
                self.smart_cache['TABLE_DATA'][:len(data)] = data
                self.logger.debug('Stored new table as subset of old table')
            except: # new table is longer than old table
                self.smart_cache['TABLE_DATA'] = data
                self.logger.debug('New table is longer than old table and has replaced it.')

            # Get the final values of table mode so that the GUI can
            # reflect them after the run:
            self.final_values = {}
            self.final_values['freq0'] = {}
            self.final_values['freq1'] = {}
            self.final_values['freq2'] = {}
            self.final_values['freq3'] = {}
            self.final_values['freq4'] = {}
            self.final_values['freq5'] = {}
            self.final_values['freq6'] = {}
            self.final_values['freq7'] = {}
            self.final_values['freq0']['freq'] = data[-1]['freq']
            self.final_values['freq0']['amp'] = data[-1]['amplitude0']
            self.final_values['freq1']['freq'] = data[-1]['frequency1']
            self.final_values['freq1']['amp'] = data[-1]['amplitude1']
            self.final_values['freq2']['freq'] = data[-1]['frequency2']
            self.final_values['freq2']['amp'] = data[-1]['amplitude2']
            self.final_values['freq3']['freq'] = data[-1]['frequency3']
            self.final_values['freq3']['amp'] = data[-1]['amplitude3']
            self.final_values['freq4']['freq'] = data[-1]['frequency4']
            self.final_values['freq4']['amp'] = data[-1]['amplitude4']
            self.final_values['freq5']['freq'] = data[-1]['frequency5']
            self.final_values['freq5']['amp'] = data[-1]['amplitude5']
            self.final_values['freq6']['freq'] = data[-1]['frequency6']
            self.final_values['freq6']['amp'] = data[-1]['amplitude6']
            self.final_values['freq7']['freq'] = data[-1]['frequency7']
            self.final_values['freq7']['amp'] = data[-1]['amplitude7']
            self.final_values['numFreq'] = data[-1]['usedfreqs']
            self.final_values['delayTime'] = data[-1]['delaytime']
            self.connection.readline()
            if self.update_mode == 'synchronous':
                # Transition to hardware synchronous updates:
                self.connection.write(b'$\r\n')
                self.connection.readline()
                # We are now waiting for a rising edge to trigger the output
                # of the second table pair (first of the experiment)
            elif self.update_mode == 'asynchronous':
                # Output will now be updated on falling edges.
                pass
            else:
                raise ValueError('invalid update mode %s'%str(self.update_mode))


        return self.final_values

    def abort_transition_to_buffered(self):
        return self.transition_to_manual(True)

    def abort_buffered(self):
        # TODO: untested
        return self.transition_to_manual(True)

    def transition_to_manual(self,abort = False):
        if abort:
            # If we're aborting the run, then we need to reset DDSs 2 and 3 to their initial values.
            # 0 and 1 will already be in their initial values. We also need to invalidate the smart
            # programming cache for them.
            #values = self.initial_values
            DDSs = []
            self.smart_cache['STATIC_DATA'] = None
        else:
            # If we're not aborting the run, then we need to set DDSs 0 and 1 to their final values.
            # 2 and 3 will already be in their final values.
            values = self.final_values
            DDSs = [0]

        # only program the channels that we need to
        for ddsnumber in DDSs:
            self.connection.write(b'@ %d\r\n'%ddsnumber)
            self.program_static(ddsnumber,values)
            self.connection.write(b'$\r\n')

        # return True to indicate we successfully transitioned back to manual mode
        return True

    def shutdown(self):

        # return to the default baud rate
        if self.default_baud_rate is not None:
            self.connection.write(b'%s\r\n' % bauds[self.default_baud_rate])
            time.sleep(0.1)
            self.connection.readlines()

        self.connection.close()



@runviewer_parser
class RunviewerClass(object):
    def __init__(self, path, device):
        self.path = path
        self.name = device.name
        self.device = device

    def get_traces(self, add_trace, clock=None):
        if clock is None:
            # we're the master pseudoclock, software triggered. So we don't have to worry about trigger delays, etc
            raise Exception('No clock passed to %s. The NovaTechDDS9M must be clocked by another device.'%self.name)

        times, clock_value = clock[0], clock[1]

        clock_indices = np.where((clock_value[1:]-clock_value[:-1])==1)[0]+1
        # If initial clock value is 1, then this counts as a rising edge (clock should be 0 before experiment)
        # but this is not picked up by the above code. So we insert it!
        if clock_value[0] == 1:
            clock_indices = np.insert(clock_indices, 0, 0)
        clock_ticks = times[clock_indices]

        # get the data out of the H5 file
        data = {}
        with h5py.File(self.path, 'r') as hdf5_file:
            if 'TABLE_DATA' in hdf5_file['devices/%s' % self.name]:
                table_data = hdf5_file['devices/%s/TABLE_DATA' % self.name][:]
                connection_table_properties = labscript_utils.properties.get(hdf5_file, self.name, 'connection_table_properties')
                update_mode = getattr(connection_table_properties, 'update_mode', 'synchronous')
                synchronous_first_line_repeat = getattr(connection_table_properties, 'synchronous_first_line_repeat', False)
                if update_mode == 'asynchronous' or synchronous_first_line_repeat:
                    table_data = table_data[1:]
                for i in range(len(self.child_devices)):
                    for sub_chnl in [ 'freq', 'amplitude0', 'frequency1', 'amplitude1',
                                      'frequency2', 'amplitude2', 'frequency3', 'amplitude3',
                                      'frequency4', 'amplitude4', 'frequency5', 'amplitude5',
                                      'frequency6', 'amplitude6', 'frequency7', 'amplitude7',
                                      'usedfreqs', 'delaytime',]:
                        data['channel %d_%s'%(i,sub_chnl)] = table_data['%s%d'%(sub_chnl,i)][:]


        for channel, channel_data in data.items():
            data[channel] = (clock_ticks, channel_data)

        for channel_name, channel in self.device.child_list.items():
            for subchnl_name, subchnl in channel.child_list.items():
                connection = '%s_%s'%(channel.parent_port, subchnl.parent_port)
                if connection in data:
                    add_trace(subchnl.name, data[connection], self.name, connection)

        return {}
