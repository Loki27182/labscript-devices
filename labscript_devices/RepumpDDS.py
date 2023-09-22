from __future__ import division, unicode_literals, print_function, absolute_import
#from labscript_utils import PY2
#if PY2:
#    str = unicode

from labscript_devices import runviewer_parser, BLACS_tab

from labscript import Device, config, LabscriptError, set_passed_properties, AnalogQuantity, StaticDigitalOut, DigitalOut

import numpy as np
import labscript_utils.h5_lock, h5py
import labscript_utils.properties

class RepumpDDS(Device):
    description = 'RepumpDDS'
    allowed_children = [AnalogQuantity,DigitalOut,StaticDigitalOut]

    @set_passed_properties(property_names = {})
    def __init__(self,name,parent_device,connection,digital_gate = {},freq_limits = None,freq_conv_class = None,freq_conv_params = {},amp_limits=None,amp_conv_class = None,amp_conv_params = {},phase_limits=None,phase_conv_class = None,phase_conv_params = {},
                 **kwargs):
        #self.clock_type = parent_device.clock_type # Don't see that this is needed anymore

        # We tell Device.__init__ to not call
        # self.parent.add_device(self), we'll do that ourselves later
        # after further intitialisation, so that the parent can see the
        # freq/amp/phase objects and manipulate or check them from within
        # its add_device method.
        Device.__init__(self,name,parent_device,connection, call_parents_add_device=False, **kwargs)

        # Ask the parent device if it has default unit conversion classes it would like us to use:
        if hasattr(parent_device, 'get_default_unit_conversion_classes'):
            classes = self.parent_device.get_default_unit_conversion_classes(self)
            default_freq_conv = classes
            # If the user has not overridden, use these defaults. If
            # the parent does not have a default for one or more of amp,
            # freq or phase, it should return None for them.
            if freq_conv_class is None:
                freq_conv_class = default_freq_conv

        self.frequency0 = AnalogQuantity(self.name+'_freq',self,'freq',freq_limits,freq_conv_class,freq_conv_params)
        self.amplitude0 = AnalogQuantity(self.name+'_amplitude0',self,'amplitude0',amp_limits,amp_conv_class,amp_conv_params)
        self.frequency1 = AnalogQuantity(self.name+'_frequency1',self,'frequency1',freq_limits,freq_conv_class,freq_conv_params)
        self.amplitude1 = AnalogQuantity(self.name+'_amplitude1',self,'amplitude1',amp_limits,amp_conv_class,amp_conv_params)
        self.frequency2 = AnalogQuantity(self.name+'_frequency2',self,'frequency2',freq_limits,freq_conv_class,freq_conv_params)
        self.amplitude2 = AnalogQuantity(self.name+'_amplitude2',self,'amplitude2',amp_limits,amp_conv_class,amp_conv_params)
        self.frequency3 = AnalogQuantity(self.name+'_frequency3',self,'frequency3',freq_limits,freq_conv_class,freq_conv_params)
        self.amplitude3 = AnalogQuantity(self.name+'_amplitude3',self,'amplitude3',amp_limits,amp_conv_class,amp_conv_params)
        self.frequency4 = AnalogQuantity(self.name+'_frequency4',self,'frequency4',freq_limits,freq_conv_class,freq_conv_params)
        self.amplitude4 = AnalogQuantity(self.name+'_amplitude4',self,'amplitude4',amp_limits,amp_conv_class,amp_conv_params)
        self.frequency5 = AnalogQuantity(self.name+'_frequency5',self,'frequency5',freq_limits,freq_conv_class,freq_conv_params)
        self.amplitude5 = AnalogQuantity(self.name+'_amplitude5',self,'amplitude5',amp_limits,amp_conv_class,amp_conv_params)
        self.frequency6 = AnalogQuantity(self.name+'_frequency6',self,'frequency6',freq_limits,freq_conv_class,freq_conv_params)
        self.amplitude6 = AnalogQuantity(self.name+'_amplitude6',self,'amplitude6',amp_limits,amp_conv_class,amp_conv_params)
        self.frequency7 = AnalogQuantity(self.name+'_frequency7',self,'frequency7',freq_limits,freq_conv_class,freq_conv_params)
        self.amplitude7 = AnalogQuantity(self.name+'_amplitude7',self,'amplitude7',amp_limits,amp_conv_class,amp_conv_params)
        self.usedfreqs  = AnalogQuantity(self.name+'_usedfreqs',self,'usedfreqs')
        self.delaytime  = AnalogQuantity(self.name+'_delaytime',self,'delaytime')

        self.parent_device.add_device(self)

    def MultiFreq(self,t,values,usedfreqs,delaytime,units=None):
        self.frequency0.constant(t,values[0],units)
        self.amplitude0.constant(t,values[1])
        self.frequency1.constant(t,values[2],units)
        self.amplitude1.constant(t,values[3])
        self.frequency2.constant(t,values[4],units)
        self.amplitude2.constant(t,values[5])
        self.frequency3.constant(t,values[6],units)
        self.amplitude3.constant(t,values[7])
        self.frequency4.constant(t,values[8],units)
        self.amplitude4.constant(t,values[9])
        self.frequency5.constant(t,values[10],units)
        self.amplitude5.constant(t,values[11])
        self.frequency6.constant(t,values[12],units)
        self.amplitude6.constant(t,values[13])
        self.frequency7.constant(t,values[14],units)
        self.amplitude7.constant(t,values[15])
        self.usedfreqs.constant(t,usedfreqs)
        self.delaytime.constant(t,delaytime)

    def enable(self,t=None):
        if self.gate:
            self.gate.go_high(t)
        else:
            raise LabscriptError('DDS %s does not have a digital gate, so you cannot use the enable(t) method.'%(self.name))

    def disable(self,t=None):
        if self.gate:
            self.gate.go_low(t)
        else:
            raise LabscriptError('DDS %s does not have a digital gate, so you cannot use the disable(t) method.'%(self.name))
