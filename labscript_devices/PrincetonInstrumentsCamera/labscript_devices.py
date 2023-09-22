import sys
from labscript_utils import dedent
from labscript import TriggerableDevice, set_passed_properties
import numpy as np
import labscript_utils.h5_lock
import h5py

class PrincetonInstrumentsCamera(TriggerableDevice):
    description = 'PrincetonInstrumentsCamera'


    @set_passed_properties(
        property_names={
            "connection_table_properties": [
            "camera_ID",
            "orientation",
            "manual_mode_camera_attributes",
            ],
            "device_properties": [
            "camera_attributes",
            "stop_acquisition_timeout",
            "exception_on_failed_shot",
            ],
        }
    )

    def __init__(
        self,
        name,
        parent_device,
        connection,
        camera_ID,
        orientation=None,
        trigger_edge_type='rising',
        trigger_duration=None,
        minimum_recovery_time=0.0,
        camera_attributes=None,
        manual_mode_camera_attributes=None,
        stop_acquisition_timeout=5.0,
        exception_on_failed_shot=True,
        **kwargs
    ):
        """A Princeton Instruments PIXIS camera controlled with PICAM.

        Args:
            name (str)
                device name

            parent_device (IntermediateDevice)
                Device with digital outputs to be used to trigger acquisition

            connection (str)
                Name of digital output port on parent device.

            camera_ID (int)
                integer of the camera_ID as given by PICAM, if this is None, the first
                camera in the list will be connected.

            orientation (str, optional), default: `<name>`
                Description of the camera's location or orientation. This will be used
                to determine the location in the shot file where the images will be
                saved. If not given, the device name will be used instead.

            trigger_edge_type (str), default: `'rising'`
                The direction of the desired edges to be generated on the parent
                devices's digital output used for triggering. Must be 'rising' or
                'falling'. Note that this only determines the edges created on the
                parent device, it does not program the camera to expect this type of
                edge. If required, one must configure the camera separately via
                `camera_attributes` to ensure it expects the type of edge being
                generated. Default: `'rising'`

            trigger_duration (float or None), default: `None`
                Duration of digital pulses to be generated by the parent device. This
                can also be specified as an argument to `expose()` - the value given
                here will be used only if nothing is passed to `expose()`.

            minimum_recovery_time (float), default: `0`
                Minimum time between frames. This will be used for error checking during
                compilation.

            camera_attributes (dict, optional):
                Dictionary of camera attribute names and values to be programmed into
                the camera. The meaning of these attributes is model-specific.
                Attributes will be programmed in the order they appear in this
                dictionary. This can be important as some attributes may not be settable
                unless another attrbiute has been set first. After adding this device to
                your connection table, a dictionary of the camera's default attributes
                can be obtained from the BLACS tab, appropriate for copying and pasting
                into your connection table to customise the ones you are interested in.

            manual_mode_camera_attributes (dict, optional):
                Dictionary of attributes that will be programmed into the camera during
                manual mode, that differ from their values in `camera_attributes`. This
                can be useful for example, to have software triggering during manual
                mode (allowing the acquisition of frames from the BLACS manual mode
                interface) but hardware triggering during buffered runs. Any attributes
                in this dictionary must also be present in `camera_attributes`.

            stop_acquisition_timeout (float), default: `5.0`
                How long, in seconds, to wait during `transition_to_buffered` for the
                acquisition of images to complete before giving up. Whilst all triggers
                should have been received, this can be used to allow for slow image
                download time.

            exception_on_failed_shot (bool), default: `True`.
                If acquisition does not complete within the given timeout after the end
                of a shot, whether to raise an exception. If False, instead prints a
                warning to stderr (visible in the terminal output pane in the BLACS
                tab), saves the images acquired so far, and continues. In the case of
                such a 'failed shot', the HDF5 attribute
                f['images'][orientation/name].attrs['failed_shot'] will be set to `True`
                (otherwise it is set to `False`). This attribute is acessible in the
                lyse dataframe as `df[orientation/name, 'failed_shot']`.

            mock (bool, optional), default: False
                For testing purpses, simulate a camera with fake data instead of
                communicating with actual hardware.

            **kwargs: Further keyword arguments to be passed to the `__init__` method of
                the parent class (TriggerableDevice).
        """

        self.trigger_edge_type = trigger_edge_type
        self.minimum_recovery_time = minimum_recovery_time
        self.trigger_duration = trigger_duration
        self.orientation = orientation
        self.camera_ID = camera_ID
        self.BLACS_connection = camera_ID#Come back to this
        if camera_attributes is None:
            camera_attributes = {}
        if manual_mode_camera_attributes is None:
            manual_mode_camera_attributes = {}
        # for attr_name in manual_mode_camera_attributes:
        #     if attr_name not in camera_attributes:
        #         msg = f"""attribute '{attr_name}' is present in
        #             manual_mode_camera_attributes but not in camera_attributes.
        #             Attributes that are to differ between manual mode and buffered
        #             mode must be present in both dictionaries."""
        #         raise ValueError(dedent(msg))
        valid_attr_levels = ('simple', 'intermediate', 'advanced', None)
        self.camera_attributes = camera_attributes
        self.manual_mode_camera_attributes = manual_mode_camera_attributes
        self.exposures = []
        TriggerableDevice.__init__(self, name, parent_device, connection, **kwargs)

    def expose(self, t, name, frametype='frame', trigger_duration=None):
        """Request an exposure at the given time. A trigger will be produced by the
        parent trigger object, with duration trigger_duration, or if not specified, of
        self.trigger_duration. The frame should have a `name, and optionally a
        `frametype`, both strings. These determine where the image will be stored in the
        hdf5 file. `name` should be a description of the image being taken, such as
        "insitu_absorption" or "fluorescence" or similar. `frametype` is optional and is
        the type of frame being acquired, for imaging methods that involve multiple
        frames. For example an absorption image of atoms might have three frames:
        'probe', 'atoms' and 'background'. For this one might call expose three times
        with the same name, but three different frametypes.
        """
        # Backward compatibility with code that calls expose with name as the first
        # argument and t as the second argument:
        if isinstance(t, str) and isinstance(name, (int, float)):
            msg = """expose() takes `t` as the first argument and `name` as the second
                argument, but was called with a string as the first argument and a
                number as the second. Swapping arguments for compatibility, but you are
                advised to modify your code to the correct argument order."""
            print(dedent(msg), file=sys.stderr)
            t, name = name, t
        if trigger_duration is None:
            trigger_duration = self.trigger_duration
        if trigger_duration is None:
            msg = """%s %s has not had an trigger_duration set as an instantiation
                argument, and none was specified for this exposure"""
            raise ValueError(dedent(msg) % (self.description, self.name))
        if not trigger_duration > 0:
            msg = "trigger_duration must be > 0, not %s" % str(trigger_duration)
            raise ValueError(msg)
        self.trigger(t, trigger_duration)
        self.exposures.append((t, name, frametype, trigger_duration))
        return trigger_duration

    def generate_code(self, hdf5_file):
        self.do_checks()
        vlenstr = h5py.special_dtype(vlen=str)
        table_dtypes = [
            ('t', float),
            ('name', vlenstr),
            ('frametype', vlenstr),
            ('trigger_duration', float),
        ]
        data = np.array(self.exposures, dtype=table_dtypes)
        group = self.init_device_group(hdf5_file)
        if self.exposures:
            group.create_dataset('EXPOSURES', data=data)
