# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy

import ctypes
import ctypes.util
import json
import pathlib
import shutil
import tempfile
from dataclasses import dataclass
from math import atan2, cos, sin
from mathutils import Euler, Vector


_EXPORT_BASENAME = 'bdsc_export'
_STATUS_INACTIVE = 'Inactive'
_STATUS_RUNNING = 'Running'
_STATUS_PAUSED = 'Paused'
_STATUS_ERROR = 'Error'
_CONFIG_DIR_NAME = 'driving_scenario_creator'
_CONFIG_FILE_NAME = 'config.json'

_status = _STATUS_INACTIVE
_last_message = ''
_session = None


def _log(message):
    print('[BDSC esmini preview] {}'.format(message))


def _set_status(status, message=''):
    global _status
    global _last_message
    _status = status
    _last_message = message


def get_preview_status_text():
    if _last_message:
        return '{} ({})'.format(_status, _last_message)
    return _status


def is_preview_active():
    return _session is not None and _session.active


def is_preview_running():
    return is_preview_active() and _session.timer_registered


def _get_esmini_library_path(user_path=''):
    candidates = []
    if user_path:
        candidates.append(pathlib.Path(user_path).expanduser())

    for name in ('esminiLib', 'esminiLib64', 'libesminiLib'):
        discovered = ctypes.util.find_library(name)
        if discovered:
            candidates.append(pathlib.Path(discovered))

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return ''


def _get_user_configured_library_path(context):
    if context is None or context.preferences is None:
        return _get_library_path_from_config_file()

    addons = context.preferences.addons

    module_candidates = []
    for candidate in (__package__, __name__.split('.')[0], 'addon'):
        if candidate and candidate not in module_candidates:
            module_candidates.append(candidate)

    for module_name in module_candidates:
        addon_cfg = addons.get(module_name)
        if addon_cfg is None or addon_cfg.preferences is None:
            continue
        value = getattr(addon_cfg.preferences, 'esmini_library_path', '')
        if value:
            return value

    for addon_cfg in addons.values():
        prefs = getattr(addon_cfg, 'preferences', None)
        if prefs is None:
            continue
        value = getattr(prefs, 'esmini_library_path', '')
        if value:
            return value

    return _get_library_path_from_config_file()


def _get_library_path_from_config_file():
    config_root = bpy.utils.user_resource('CONFIG', path=_CONFIG_DIR_NAME, create=False)
    if not config_root:
        return ''

    config_file = pathlib.Path(config_root) / _CONFIG_FILE_NAME
    if not config_file.exists():
        return ''

    try:
        with config_file.open('r', encoding='utf-8') as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return ''

    value = data.get('esmini_library_path', '') if isinstance(data, dict) else ''
    return value if isinstance(value, str) else ''


class _SEScenarioObjectState(ctypes.Structure):
    # Match esminiLib SE_ScenarioObjectState layout (v3.x).
    _fields_ = [
        ('id', ctypes.c_int),
        ('model_id', ctypes.c_int),
        ('control', ctypes.c_int),
        ('timestamp', ctypes.c_double),
        ('x', ctypes.c_double),
        ('y', ctypes.c_double),
        ('z', ctypes.c_double),
        ('h', ctypes.c_double),
        ('p', ctypes.c_double),
        ('r', ctypes.c_double),
        ('roadId', ctypes.c_int),
        ('junctionId', ctypes.c_int),
        ('t', ctypes.c_double),
        ('laneId', ctypes.c_int),
        ('laneOffset', ctypes.c_double),
        ('s', ctypes.c_double),
        ('speed', ctypes.c_double),
        ('centerOffsetX', ctypes.c_double),
        ('centerOffsetY', ctypes.c_double),
        ('centerOffsetZ', ctypes.c_double),
        ('width', ctypes.c_double),
        ('length', ctypes.c_double),
        ('height', ctypes.c_double),
        ('objectType', ctypes.c_int),
        ('objectCategory', ctypes.c_int),
        ('wheelAngle', ctypes.c_double),
        ('wheelRot', ctypes.c_double),
        ('visibilityMask', ctypes.c_int),
    ]


class EsminiLibraryError(RuntimeError):
    pass


class EsminiBindings:

    def __init__(self, library_path):
        try:
            self.lib = ctypes.CDLL(library_path)
        except OSError as exc:
            raise EsminiLibraryError('Failed to load esmini library: {}'.format(exc)) from exc

        self._bind_symbol('SE_Close', restype=ctypes.c_int)
        self._bind_symbol('SE_StepDT', argtypes=[ctypes.c_double], restype=ctypes.c_int)
        self._bind_symbol('SE_GetNumberOfObjects', restype=ctypes.c_int)
        self._bind_symbol('SE_GetId', argtypes=[ctypes.c_int], restype=ctypes.c_int)

        self.fn_get_object_state = self._bind_symbol('SE_GetObjectState',
                                                     argtypes=[ctypes.c_int, ctypes.POINTER(_SEScenarioObjectState)],
                                                     restype=ctypes.c_int,
                                                     required=False)
        self.fn_get_object_name = self._bind_symbol('SE_GetObjectName',
                                                    argtypes=[ctypes.c_int],
                                                    restype=ctypes.c_char_p,
                                                    required=False)
        self.fn_init = self._bind_symbol('SE_Init',
                                         argtypes=[ctypes.c_char_p, ctypes.c_int, ctypes.c_int,
                                                   ctypes.c_int, ctypes.c_int],
                                         restype=ctypes.c_int,
                                         required=False)
        self.fn_init_with_args = self._bind_symbol('SE_InitWithArgs',
                                                   argtypes=[ctypes.c_int, ctypes.POINTER(ctypes.c_char_p)],
                                                   restype=ctypes.c_int,
                                                   required=False)

        if self.fn_init is None and self.fn_init_with_args is None:
            raise EsminiLibraryError('esmini library missing required init function (SE_Init/SE_InitWithArgs).')
        if self.fn_get_object_state is None:
            raise EsminiLibraryError('esmini library missing required state function (SE_GetObjectState).')

    def _bind_symbol(self, symbol, argtypes=None, restype=ctypes.c_int, required=True):
        fn = getattr(self.lib, symbol, None)
        if fn is None:
            if required:
                raise EsminiLibraryError('esmini library missing symbol: {}'.format(symbol))
            return None
        if argtypes is not None:
            fn.argtypes = argtypes
        fn.restype = restype
        return fn

    def init(self, xosc_path):
        xosc_bytes = str(xosc_path).encode('utf-8')
        if self.fn_init is not None:
            rc = self.fn_init(xosc_bytes, 0, 0, 0, 0)
            if rc != 0:
                raise EsminiLibraryError('SE_Init returned {}'.format(rc))
            return

        args = [
            b'esmini',
            b'--osc',
            xosc_bytes,
            b'--headless',
        ]
        argc = len(args)
        argv = (ctypes.c_char_p * argc)(*args)
        rc = self.fn_init_with_args(argc, argv)
        if rc != 0:
            raise EsminiLibraryError('SE_InitWithArgs returned {}'.format(rc))

    def close(self):
        self.lib.SE_Close()

    def step_dt(self, dt):
        rc = self.lib.SE_StepDT(ctypes.c_double(dt))
        if rc != 0:
            raise EsminiLibraryError('SE_StepDT returned {}'.format(rc))

    def get_object_id(self, object_index):
        value = self.lib.SE_GetId(object_index)
        if value < 0:
            raise EsminiLibraryError('SE_GetId returned {} for index {}'.format(value, object_index))
        return value

    def get_number_of_objects(self):
        value = self.lib.SE_GetNumberOfObjects()
        if value < 0:
            raise EsminiLibraryError('SE_GetNumberOfObjects returned {}'.format(value))
        return value

    def get_object_state(self, object_index):
        state = _SEScenarioObjectState()
        rc = self.fn_get_object_state(object_index, ctypes.byref(state))
        if rc != 0:
            raise EsminiLibraryError('SE_GetObjectState returned {} for index {}'.format(rc, object_index))
        return state

    def get_object_name(self, object_index, fallback_name=''):
        if self.fn_get_object_name is not None:
            value = self.fn_get_object_name(object_index)
            if value:
                return value.decode('utf-8', errors='ignore')
        if fallback_name:
            return fallback_name
        return ''


@dataclass
class PreviewObjectState:
    name: str
    object_ref: bpy.types.Object
    original_matrix: object


class PreviewSession:

    def __init__(self, esmini_path, export_dir, bindings, object_states):
        self.esmini_path = esmini_path
        self.export_dir = export_dir
        self.bindings = bindings
        self.object_states = object_states
        self.objects_by_name = {state.name: state.object_ref for state in object_states}
        self.ordered_names = [state.name for state in object_states]
        self.active = False
        self.timer_registered = False
        self.last_dt = 0.0
        self.last_object_count = 0
        self.last_matched_count = 0
        self.total_steps = 0
        self.elapsed_time = 0.0
        self.step_interval = 0.0
        self.auto_play_started = False
        self.manual_mode = False
        # 2D transform matrix from esmini XY -> Blender XY:
        # x' = a*x + b*y, y' = c*x + d*y
        self.xy_map = (1.0, 0.0, 0.0, 1.0)
        self.object_name_by_index = {}
        self.object_index_by_name = {}
        self.debug_print_each_step = False

    def register_handler(self):
        if not self.timer_registered:
            bpy.app.timers.register(_preview_timer_callback, first_interval=max(0.001, self.step_interval))
            self.timer_registered = True

    def unregister_handler(self):
        self.timer_registered = False

    def restore_objects(self):
        for state in self.object_states:
            if state.object_ref.name in bpy.data.objects:
                state.object_ref.matrix_world = state.original_matrix.copy()

    def close(self):
        try:
            self.bindings.close()
        except Exception:
            pass

        if self.export_dir and pathlib.Path(self.export_dir).exists():
            shutil.rmtree(self.export_dir, ignore_errors=True)


def _scene_step_interval(scene):
    fps_base = scene.render.fps_base if scene.render.fps_base > 0 else 1.0
    fps = scene.render.fps / fps_base
    if fps <= 0:
        return 1.0 / 24.0
    return 1.0 / float(fps)


def _collect_entities_for_preview():
    collection_root = bpy.data.collections.get('OpenSCENARIO')
    if collection_root is None:
        raise RuntimeError('OpenSCENARIO collection not found.')

    entities_collection = collection_root.children.get('entities')
    if entities_collection is None:
        raise RuntimeError('OpenSCENARIO/entities collection not found.')

    object_states = []
    for obj in entities_collection.objects:
        if 'dsc_type' in obj and obj['dsc_type'] == 'entity':
            object_states.append(
                PreviewObjectState(
                    name=obj.name,
                    object_ref=obj,
                    original_matrix=obj.matrix_world.copy(),
                )
            )

    if not object_states:
        raise RuntimeError('No OpenSCENARIO entities found for preview.')

    names = [state.name for state in object_states]
    if len(names) != len(set(names)):
        raise RuntimeError('Duplicate entity names detected. Ensure entity names are unique.')

    return object_states


def _export_preview_scenario(temp_dir):
    result = bpy.ops.dsc.export_driving_scenario('EXEC_DEFAULT', directory=temp_dir, mesh_file_type='glb')
    if 'FINISHED' not in result:
        raise RuntimeError('Preview export did not finish successfully.')

    xosc_path = pathlib.Path(temp_dir) / 'xosc' / (_EXPORT_BASENAME + '.xosc')
    if not xosc_path.exists():
        raise RuntimeError('Preview export did not produce {}'.format(xosc_path))

    return xosc_path


def _resolve_object_for_state(session, object_index):
    if object_index in session.object_name_by_index:
        state_name = session.object_name_by_index[object_index]
        return session.objects_by_name.get(state_name)

    fallback_name = session.ordered_names[object_index] if object_index < len(session.ordered_names) else ''
    state_name = session.bindings.get_object_name(object_index, fallback_name=fallback_name)

    # Fallback to index order if name lookup is unavailable or returns unknown values.
    if state_name not in session.objects_by_name and fallback_name in session.objects_by_name:
        state_name = fallback_name

    if state_name not in session.objects_by_name:
        return None
    return session.objects_by_name[state_name]


def _map_xy(session, x, y):
    a, b, c, d = session.xy_map
    return a * x + b * y, c * x + d * y


def _map_heading(session, heading):
    # Transform heading direction vector by the same 2D mapping used for position.
    hx = cos(heading)
    hy = sin(heading)
    hx_mapped, hy_mapped = _map_xy(session, hx, hy)
    return atan2(hy_mapped, hx_mapped)


def _candidate_xy_mappings():
    return [
        (1.0, 0.0, 0.0, 1.0),
        (1.0, 0.0, 0.0, -1.0),
        (-1.0, 0.0, 0.0, 1.0),
        (-1.0, 0.0, 0.0, -1.0),
        (0.0, 1.0, 1.0, 0.0),
        (0.0, 1.0, -1.0, 0.0),
        (0.0, -1.0, 1.0, 0.0),
        (0.0, -1.0, -1.0, 0.0),
    ]


def _collect_sim_states(session):
    object_count = session.bindings.get_number_of_objects()
    sim_states = []
    for object_index in range(object_count):
        object_id = session.bindings.get_object_id(object_index)
        sim_states.append((object_index, object_id, session.bindings.get_object_state(object_id)))
    return sim_states


def _calibrate_coordinate_mapping(session):
    sim_states = _collect_sim_states(session)
    if not sim_states:
        _log('Calibration skipped (no simulation states available at startup).')
        return

    best_map = (1.0, 0.0, 0.0, 1.0)
    best_error = float('inf')

    for candidate in _candidate_xy_mappings():
        a, b, c, d = candidate
        available_indices = [idx for idx, _, _ in sim_states]
        error = 0.0

        # Greedy nearest fit from authored Blender entity positions to sim states.
        for preview_state in session.object_states:
            if not available_indices:
                break

            obj_x = preview_state.object_ref.location.x
            obj_y = preview_state.object_ref.location.y
            best_local_idx = None
            best_local_error = float('inf')

            for sim_idx in available_indices:
                sim_state = sim_states[sim_idx][2]
                x_mapped = a * sim_state.x + b * sim_state.y
                y_mapped = c * sim_state.x + d * sim_state.y
                dx = obj_x - x_mapped
                dy = obj_y - y_mapped
                local_error = dx * dx + dy * dy
                if local_error < best_local_error:
                    best_local_error = local_error
                    best_local_idx = sim_idx

            if best_local_idx is not None:
                error += best_local_error
                available_indices.remove(best_local_idx)

        if error < best_error:
            best_error = error
            best_map = candidate

    session.xy_map = best_map
    _log('Coordinate mapping selected: {} (fit error {:.6f})'.format(session.xy_map, best_error))


def _build_fixed_object_index_mapping(session):
    session.object_name_by_index = {}
    session.object_index_by_name = {}

    sim_states = _collect_sim_states(session)
    if not sim_states:
        _log('Object index mapping skipped (no simulation states available).')
        return

    available_indices = [idx for idx, _, _ in sim_states]

    # Prefer explicit name matches when available from esmini.
    for object_index, object_id, state in sim_states:
        sim_name = session.bindings.get_object_name(object_index, fallback_name='')
        if sim_name in session.objects_by_name and sim_name not in session.object_index_by_name:
            session.object_index_by_name[sim_name] = object_index
            session.object_name_by_index[object_index] = sim_name
            if object_index in available_indices:
                available_indices.remove(object_index)

    # Fill missing assignments by nearest mapped position.
    for preview_state in session.object_states:
        obj_name = preview_state.name
        if obj_name in session.object_index_by_name:
            continue
        if not available_indices:
            break

        obj_loc = preview_state.object_ref.location
        best_idx = None
        best_error = float('inf')
        for sim_idx in available_indices:
            sim_state = sim_states[sim_idx][2]
            x_mapped, y_mapped = _map_xy(session, sim_state.x, sim_state.y)
            dx = obj_loc.x - x_mapped
            dy = obj_loc.y - y_mapped
            dz = obj_loc.z - sim_state.z
            error = dx * dx + dy * dy + dz * dz
            if error < best_error:
                best_error = error
                best_idx = sim_idx

        if best_idx is not None:
            session.object_index_by_name[obj_name] = best_idx
            session.object_name_by_index[best_idx] = obj_name
            available_indices.remove(best_idx)

    if not session.object_name_by_index:
        _log('No fixed object index mappings established. Fallback matching will be used.')
        return

    _log('Fixed object mappings (Blender -> esmini index):')
    for obj_name, sim_idx in session.object_index_by_name.items():
        _log('  {} -> {}'.format(obj_name, sim_idx))


def _preview_progress_text(session):
    return 'step: {}, t: {:.3f}s'.format(session.total_steps, session.elapsed_time)


def _set_progress_status(session):
    status = _STATUS_RUNNING if session.timer_registered else _STATUS_PAUSED
    _set_status(status, _preview_progress_text(session))


def _apply_preview_step(scene):
    dt = _session.step_interval
    if dt <= 1e-8:
        return

    _session.bindings.step_dt(dt)
    _session.last_dt = dt
    _session.total_steps += 1
    _session.elapsed_time += dt

    object_count = _session.bindings.get_number_of_objects()
    _session.last_object_count = object_count
    matched_count = 0
    for object_index in range(object_count):
        object_id = _session.bindings.get_object_id(object_index)
        state = _session.bindings.get_object_state(object_id)
        obj = _resolve_object_for_state(_session, object_index)
        if obj is None:
            continue
        matched_count += 1

        x_mapped, y_mapped = _map_xy(_session, state.x, state.y)
        mapped_heading = _map_heading(_session, state.h)
        obj.location = Vector((x_mapped, y_mapped, state.z))
        obj.rotation_mode = 'XYZ'
        obj.rotation_euler = Euler((0.0, 0.0, mapped_heading), 'XYZ')

        if _session.manual_mode and _session.debug_print_each_step:
            _log(
                'step {} | sim_idx {} | obj {} | sim xyz=({:.3f},{:.3f},{:.3f}) h={:.3f} '
                '-> mapped xyz=({:.3f},{:.3f},{:.3f}) yaw={:.3f}'.format(
                    _session.total_steps,
                    object_index,
                    obj.name,
                    state.x,
                    state.y,
                    state.z,
                    state.h,
                    x_mapped,
                    y_mapped,
                    state.z,
                    mapped_heading,
                )
            )

    _session.last_matched_count = matched_count
    _set_progress_status(_session)


def _preview_timer_callback():
    if not is_preview_active():
        return None

    scene = bpy.context.scene
    if scene is None:
        return max(0.001, _session.step_interval)

    if not _session.active or not _session.timer_registered:
        return None

    try:
        _step_preview_once(scene)
    except Exception as exc:
        stop_preview_session(restore=True, reason='Preview stopped: {}'.format(exc))
        return None

    return max(0.001, _session.step_interval)


def _step_preview_once(scene):
    if not is_preview_active():
        raise RuntimeError('Preview is not running.')

    _apply_preview_step(scene)
    scene.frame_set(scene.frame_current + 1)


def _start_preview_session(context, manual_mode=False):
    global _session

    if is_preview_active():
        raise RuntimeError('Preview is already running.')

    user_path = _get_user_configured_library_path(context)
    library_path = _get_esmini_library_path(user_path)
    if not library_path:
        raise RuntimeError(
            'esmini library not found. Set library path in Add-on Preferences '
            '(Edit > Preferences > Add-ons > Driving Scenario Creator).'
        )

    object_states = _collect_entities_for_preview()
    temp_dir = tempfile.mkdtemp(prefix='bdsc_esmini_preview_')

    try:
        xosc_path = _export_preview_scenario(temp_dir)
        bindings = EsminiBindings(library_path)
        bindings.init(xosc_path)
        _session = PreviewSession(library_path, temp_dir, bindings, object_states)
        _session.active = True
        _session.manual_mode = manual_mode
        _session.debug_print_each_step = manual_mode
        _session.step_interval = _scene_step_interval(context.scene)
        _session.elapsed_time = 0.0
        _calibrate_coordinate_mapping(_session)
        _build_fixed_object_index_mapping(_session)

        if manual_mode:
            if context.screen is not None and context.screen.is_animation_playing:
                bpy.ops.screen.animation_play()
            _set_progress_status(_session)
        else:
            if context.screen is not None and not context.screen.is_animation_playing:
                bpy.ops.screen.animation_play()
                _session.auto_play_started = True
            _session.register_handler()
            _set_progress_status(_session)

        _log('Session started')
        _log('Library: {}'.format(library_path))
        _log('Scenario: {}'.format(xosc_path))
        _log('Mapped entities: {}'.format(', '.join(_session.ordered_names)))
        _log('Mode: {}'.format('manual step' if manual_mode else 'auto play'))
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def start_preview_session(context):
    _start_preview_session(context, manual_mode=False)


def pause_preview_session(context):
    del context
    if not is_preview_active():
        raise RuntimeError('Preview is not running.')
    if not _session.timer_registered:
        return

    _session.unregister_handler()
    screen = bpy.context.screen
    if screen is not None and screen.is_animation_playing:
        bpy.ops.screen.animation_play()
    _set_progress_status(_session)


def resume_preview_session(context):
    if not is_preview_active():
        raise RuntimeError('Preview is not running.')
    if _session.timer_registered:
        return

    _session.register_handler()
    screen = context.screen if context is not None else bpy.context.screen
    if screen is not None and not screen.is_animation_playing:
        bpy.ops.screen.animation_play()
        _session.auto_play_started = True
    _set_progress_status(_session)


def toggle_preview_play_pause(context):
    if not is_preview_active():
        start_preview_session(context)
        return 'started'
    if is_preview_running():
        pause_preview_session(context)
        return 'paused'
    resume_preview_session(context)
    return 'resumed'


def step_preview_session_once(context):
    if not is_preview_active():
        _start_preview_session(context, manual_mode=True)

    if _session.timer_registered:
        pause_preview_session(context)

    scene = context.scene if context is not None else bpy.context.scene
    if scene is None:
        raise RuntimeError('No active scene found.')

    _step_preview_once(scene)


def stop_preview_session(restore=True, reason=''):
    global _session

    if _session is None:
        if reason:
            _set_status(_STATUS_ERROR, reason)
        else:
            _set_status(_STATUS_INACTIVE, '')
        return

    session = _session
    _session = None

    try:
        session.unregister_handler()

        if session.auto_play_started and bpy.context.screen is not None and bpy.context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()

        if restore:
            session.restore_objects()
    finally:
        session.close()

    _log('Session stopped. steps={}, last_dt={:.4f}, sim_objects={}, updated={}'.format(
        session.total_steps, session.last_dt, session.last_object_count, session.last_matched_count))

    if reason:
        _set_status(_STATUS_ERROR, reason)
    else:
        _set_status(_STATUS_INACTIVE, '')


def ensure_preview_stopped_on_unregister():
    stop_preview_session(restore=True, reason='')
