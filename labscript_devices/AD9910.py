from __future__ import division, unicode_literals, print_function, absolute_import
#from labscript_utils import PY2
#if PY2:
#    str = unicode

from labscript_devices import runviewer_parser, BLACS_tab

from labscript import Device, config, LabscriptError, set_passed_properties, AnalogQuantity, DigitalOut, DigitalQuantity

import numpy as np
import labscript_utils.h5_lock, h5py
import labscript_utils.properties

class AD9910(Device):
    description = 'DDS'
    allowed_children = [AnalogQuantity,DigitalOut,DigitalQuantity] # Adds its own children when initialised

    @set_passed_properties(property_names = {})
    def __init__(self, name, parent_device, connection, freq_limits=None, freq_conv_class=None, freq_conv_params={},
                 **kwargs):
        #self.clock_type = parent_device.clock_type # Don't see that this is needed anymore

        # Here we set call_parents_add_device=False so that we
        # can do additional initialisation before manually calling
        # self.parent_device.add_device(self). This allows the parent's
        # add_device method to perform checks based on the code below,
        # whilst still providing us with the checks and attributes that
        # Device.__init__ gives us in the meantime.
        Device.__init__(self, name, parent_device, connection, call_parents_add_device=False, **kwargs)

        # Ask the parent device if it has default unit conversion classes it would like us to use:
        if hasattr(parent_device, 'get_default_unit_conversion_classes'):
            classes = self.parent_device.get_default_unit_conversion_classes(self)
            default_freq_conv = classes
            # If the user has not overridden, use these defaults. If
            # the parent does not have a default for one or more of amp,
            # freq or phase, it should return None for them.
            if freq_conv_class is None:
                freq_conv_class = default_freq_conv

        self.frequency = AnalogQuantity(self.name + '_freq', self, 'freq', freq_limits, freq_conv_class, freq_conv_params)
        self.ramplow = AnalogQuantity(self.name + '_ramplow', self, 'ramplow', freq_limits, freq_conv_class, freq_conv_params)
        self.ramphigh = AnalogQuantity(self.name + '_ramphigh', self, 'ramphigh', freq_limits, freq_conv_class, freq_conv_params)
        self.rampdur = AnalogQuantity(self.name + '_rampdur', self, 'rampdur')
        self.rampon = DigitalQuantity(self.name + '_rampon', self, 'rampon')

        # If the user has not specified a gate, and the parent device
        # supports gating of DDS output, it should add a gate to this
        # instance in its add_device method, which is called below. If
        # they *have* specified a gate device, but the parent device
        # has its own gating (such as the PulseBlaster), it should
        # check this and throw an error in its add_device method. See
        # labscript_devices.PulseBlaster.PulseBlaster.add_device for an
        # example of this.
        self.parent_device.add_device(self)

    def setfreq(self, t, value, units=None):
        self.frequency.constant(t, value, units)

    def setrampon(self, t, freq0, freq1, tau, units=None):
        self.ramplow.constant(t, freq0, units)
        self.ramphigh.constant(t, freq1, units)
        self.rampdur.constant(t, tau)
        self.rampon.go_high(t)

    def setrampoff(self, t):
        self.rampon.go_low(t)
