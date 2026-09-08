import bpy
from mathutils import Vector

from . import helpers
from . modal_road_object_base import DSC_OT_modal_road_object_base, load_geometry
from . road_object_parking_spots import road_object_parking_spots


class DSC_OT_road_object_parking_spots(DSC_OT_modal_road_object_base):
    bl_idname = 'dsc.road_object_parking_spots'
    bl_label = 'Parking spots'
    bl_description = 'Create rectangular parking spot road markings'
    bl_options = {'REGISTER', 'UNDO'}

    spot_length: bpy.props.FloatProperty(name='Spot length', default=5.0, min=1.0, max=20.0, unit='LENGTH')
    num_spots: bpy.props.IntProperty(name='Number of spots', default=1, min=1, max=100)
    start_modal: bpy.props.BoolProperty(options={'HIDDEN'})
    road_object_type = 'parking_spots'
    reference_object_mode = False
    snap_filter = 'surface'

    def create_object_model(self, context):
        self.road_object = road_object_parking_spots(context, self.road_object_type)

    def execute(self, context):
        self.state = 'INIT'
        self.anchor_point_s = None
        self.create_object_model(context)
        bpy.ops.object.select_all(action='DESELECT')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if self.start_modal:
            return self.execute(context)
        return context.window_manager.invoke_popup(self, width=280)

    def cancel(self, context):
        self.num_spots = 1
        spot_length = self.spot_length
        helpers.call_operator_deferred(
            lambda: bpy.ops.dsc.road_object_parking_spots(
                'INVOKE_DEFAULT', spot_length=spot_length, start_modal=True))

    def clean_up(self, context):
        self.num_spots = 1
        self.anchor_point_s = None
        super().clean_up(context)

    def draw(self, context):
        self.layout.prop(self, 'spot_length')

    def modal(self, context, event):
        if self.state == 'INIT':
            context.workspace.status_text_set(
                'LEFTMOUSE: place parking spots, SHIFT+WHEEL: change spot count, '
                'RIGHTMOUSE/ESCAPE: exit')
            bpy.context.window.cursor_modal_set('CROSSHAIR')
            self.reset_params_input()
            self.reset_params_snap()
            self.selected_road = None
            self.selected_geometry = None
            self.anchor_point_s = None
            self.selected_elevation = 0.0
            self.create_stencil(context)
            self.state = 'PLACE'

        if event.type in {'NONE', 'TIMER', 'TIMER_REPORT', 'EVT_TWEAK_L', 'WINDOW_DEACTIVATE'}:
            return {'PASS_THROUGH'}

        if event.shift and event.type in {'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            spot_count_delta = 1 if event.type == 'WHEELUPMOUSE' else -1
            new_num_spots = max(1, min(100, self.num_spots + spot_count_delta))
            if (self.selected_road is not None and self.anchor_point_s is not None
                    and new_num_spots != self.num_spots):
                self.params_input['point_s'] = (
                    self.anchor_point_s + (new_num_spots - 1) * self.spot_length / 2.0)
            self.num_spots = new_num_spots
            if self.selected_road is not None:
                self.update_stencil(context, update_start=False)
            return {'RUNNING_MODAL'}

        if event.type == 'MOUSEMOVE':
            params_snap = helpers.mouse_to_road_surface_params(context, event)
            if params_snap['hit_type'] == 'road_surface':
                road_obj = bpy.data.objects.get(params_snap['id_obj'])
                road_type = road_obj.get('dsc_type') if road_obj is not None else None
                road_types = {
                    'road_straight', 'road_arc', 'road_clothoid',
                    'road_clothoid_triple', 'road_parampoly3',
                }
                if (road_obj is not None and road_type in road_types
                        and road_obj.get('geometry') is not None
                        and road_obj.get('lane_offset_coefficients') is not None):
                    self.selected_road = road_obj
                    self.id_road = road_obj['id_odr']
                    self.selected_geometry = load_geometry(
                        road_obj['dsc_type'], road_obj['geometry'], road_obj['lane_offset_coefficients'])
                    point_ref_line_local, heading_ref_line, point_s, point_t = \
                        self.selected_geometry.get_closest_ref_line_x_y_heading_s_t(params_snap['point'])
                    self.anchor_point_s = point_s
                    self.params_input['point_s'] = (
                        self.anchor_point_s + (self.num_spots - 1) * self.spot_length / 2.0)
                    self.params_input['point_t'] = point_t
                    self.params_input['point_ref_line'] = \
                        self.selected_geometry.matrix_world @ point_ref_line_local.to_3d()
                    self.params_input['point'] = params_snap['point'].copy()
                    self.params_input['heading'] = \
                        self.selected_geometry.sections[0]['heading_start'] + heading_ref_line
                    self.params_snap = params_snap
                    self.params_input['point'] = self.selected_geometry.matrix_world @ \
                        Vector(self.selected_geometry.sample_cross_section(point_s, [point_t], False)[0][0])
                    context.scene.cursor.location = self.params_input['point']
                    self.update_stencil(context, update_start=False)
                    return {'RUNNING_MODAL'}

            self.selected_road = None
            self.selected_geometry = None
            self.params_input['parking_lane_valid'] = False
            return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.update_parking_lane_params()
            if self.params_input.get('parking_lane_valid', False):
                self.create_object_3d(context)
                self.num_spots = 1
                if self.anchor_point_s is not None:
                    self.params_input['point_s'] = self.anchor_point_s
                self.update_stencil(context, update_start=False)
            return {'RUNNING_MODAL'}

        if event.type in {'RIGHTMOUSE', 'ESC'} and event.value == 'RELEASE':
            self.clean_up(context)
            return {'FINISHED'}

        if event.type == 'WHEELUPMOUSE':
            bpy.ops.view3d.zoom(mx=0, my=0, delta=1, use_cursor_init=False)
        elif event.type == 'WHEELDOWNMOUSE':
            bpy.ops.view3d.zoom(mx=0, my=0, delta=-1, use_cursor_init=True)
        elif event.type == 'MIDDLEMOUSE' and event.alt and event.value == 'RELEASE':
            bpy.ops.view3d.view_center_cursor()

        return {'RUNNING_MODAL'}

    def update_params_get_mesh(self, context, wireframe=True):
        self.update_parking_lane_params()
        valid, mesh, matrix_world, materials = self.road_object.update_params_get_mesh(
            context, self.params_input, self.selected_road, self.selected_geometry, wireframe)
        return valid, mesh, matrix_world, materials

    def create_object_3d(self, context):
        self.update_parking_lane_params()
        return self.road_object.create_object_3d(
            context, self.params_input, self.id_road, self.selected_road, self.selected_geometry)

    def update_parking_lane_params(self):
        self.params_input['spot_length'] = self.spot_length
        self.params_input['num_spots'] = self.num_spots
        self.params_input['lane_inset'] = 0.10
        self.params_input['parking_lane_valid'] = False
        if self.selected_road is None or self.selected_geometry is None:
            return
        road = self.selected_road
        lane_offset = helpers.calculate_lane_offset(
            self.params_input['point_s'], road['lane_offset_coefficients'], road['geometry_total_length'])
        relative_t = self.params_input['point_t'] - lane_offset
        if relative_t >= 0.0:
            lane_side = 'left'
            widths = self._lane_widths('left')
            lane_types = road['lanes_left_types']
            lane_position = relative_t
        else:
            lane_side = 'right'
            widths = self._lane_widths('right')
            lane_types = road['lanes_right_types']
            lane_position = -relative_t
        accumulated = 0.0
        for lane_index, lane_width in enumerate(widths):
            if accumulated <= lane_position <= accumulated + lane_width:
                if lane_types[lane_index] == 'parking' and lane_width > 2.0 * self.params_input['lane_inset']:
                    self.params_input['lane_side'] = lane_side
                    self.params_input['lane_index'] = lane_index
                    self.params_input['lane_width'] = lane_width - 2.0 * self.params_input['lane_inset']
                    self.params_input['parking_lane_valid'] = True
                return
            accumulated += lane_width

    def _lane_widths(self, side):
        road = self.selected_road
        return helpers._interpolate_lane_widths(
            road['lanes_{}_widths_start'.format(side)], road['lanes_{}_widths_end'.format(side)],
            self.params_input['point_s'], road['geometry_total_length'])