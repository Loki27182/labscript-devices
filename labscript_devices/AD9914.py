from labscript_devices import BLACS_tab, runviewer_parser 
from labscript import Device, LabscriptError, set_passed_properties, StaticAnalogQuantity, StaticDigitalOut

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

class AD9914(Device):
    description = 'AD9914'
    allowed_children = [StaticAnalogQuantity,StaticDigitalOut]
    
    @set_passed_properties(
        property_names = {'connection_table_properties': ['com_port','baud_rate']}
        )
    def __init__(self, name, parent_device,
                 com_port = '', baud_rate=9600, default_baud_rate = None, update_mode='synchronous',
                 synchronous_first_line_repeat = True, **kwargs):

        Device.__init__(self, name, parent_device, **kwargs)
        self.BLACS_connection = '%s,%s'%(com_port, str(baud_rate))
        self.frequency = StaticAnalogQuantity(self.name+'_freq',self,'freq',(100000000,2000000000))
        self.frequency.default_value = 100000000
        self.gate = StaticDigitalOut(self.name+'_gate',self,'gate')

        if not update_mode in ['synchronous', 'asyncronous']:
            raise LabscriptError('update_mode must be \'synchronous\' or \'asynchronous\'')

        if not baud_rate in bauds:
            raise LabscriptError('baud_rate must be one of {0}'.format(list(bauds)))

        if not default_baud_rate in bauds and default_baud_rate is not None:
            raise LabscriptError('default_baud_rate must be one of {0} or None (to indicate no default)'.format(list(bauds)))

        self.update_mode = update_mode
        self.synchronous_first_line_repeat = synchronous_first_line_repeat

    def enable(self):       
        self.gate.go_high()
                            
    def disable(self):
        self.gate.go_low()  

    def set_freq(self,freq):
        self.frequency.constant(freq)

    def generate_code(self, hdf5_file):
        
        dtypes = [('freq',np.float64), ('gate',np.uint8)]

        out_table = np.zeros(1,dtype=dtypes)
        out_table['freq'] = self.frequency.static_value
        out_table['gate'] = self.gate.static_value

        grp = self.init_device_group(hdf5_file)
        grp.create_dataset('STATIC_DATA',compression=config.compression,data=out_table)
        self.set_property('frequency_scale_factor', 1, location='device_properties')

import time

from blacs.tab_base_classes import Worker, define_state
from blacs.tab_base_classes import MODE_MANUAL, MODE_TRANSITION_TO_BUFFERED, MODE_TRANSITION_TO_MANUAL, MODE_BUFFERED

from blacs.device_base_class import DeviceTab

@BLACS_tab
class AD9914Tab(DeviceTab):

    def initialise_GUI(self):
        dds_prop = {'channel 0': {'freq':{'base_unit':'Hz',
                                                     'min':100000000.0,
                                                     'max':2000000000.0,
                                                     'step':1000.0,
                                                     'decimals':1
                                                    },
                                                    'gate':0}}

        self.create_dds_outputs(dds_prop)
        dds_widgets,ao_widgets,do_widgets = self.auto_create_widgets()
        self.auto_place_widgets(("DDS Outputs",dds_widgets))

        connection_object = self.settings['connection_table'].find_by_name(self.device_name)
        connection_table_properties = connection_object.properties

        self.com_port = connection_table_properties.get('com_port', None)
        self.baud_rate = connection_table_properties.get('baud_rate', None)
        self.default_baud_rate = connection_table_properties.get('default_baud_rate', None)
        self.update_mode = connection_table_properties.get('update_mode', 'synchronous')


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


        self.create_worker("main_worker",AD9914Worker,{'com_port':self.com_port,
                                                              'baud_rate': self.baud_rate,
                                                              'default_baud_rate': self.default_baud_rate,
                                                              'update_mode': self.update_mode})
        self.primary_worker = "main_worker"

        self.supports_remote_value_check(False)
        self.supports_smart_programming(False)
    
class AD9914Worker(Worker):
    def init(self):
        global serial; import serial
        global socket; import socket
        global h5py; import labscript_utils.h5_lock, h5py
        import logging

        self.smart_cache = {'STATIC_DATA': None, 'TABLE_DATA': ''}
        self.logger = logging.getLogger('BLACS.%s.state_queue'%('AD9914'))
        
        if self.default_baud_rate is not None:
            initial_baud_rate = self.default_baud_rate
        else:
            initial_baud_rate = self.baud_rate

        print('Dummy serial setup...')

    def program_manual(self,front_panel_values):
        self.program_static(front_panel_values['channel 0'])

    def program_static(self,value):
        print('Dummy frequency set to {:1.0f}'.format(value['freq']))
        print('Dummy gate set to {:1.0f}'.format(value['gate']))
        self.smart_cache['STATIC_DATA'] = None

    def transition_to_buffered(self,device_name,h5file,initial_values,fresh):
        data = None
        with h5py.File(h5file,mode='r') as hdf5_file:
            group = hdf5_file['/devices/'+device_name]
            if 'STATIC_DATA' in group:
                data = group['STATIC_DATA'][0]

        final_values = {'channel 0': data}
        print('Transferring to buffered mode...')
        self.program_static(data)

        return final_values

    def abort_transition_to_buffered(self):
        return self.transition_to_manual(True)

    def abort_buffered(self):
        return self.transition_to_manual(True)

    def transition_to_manual(self,abort = False):
        return True

    def shutdown(self):
        pass

@runviewer_parser
class AD9914_Parser(object):
    pass
