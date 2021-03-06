import bpy

def get_new_id_xodr(context):
    '''
        Generate and return new ID for OpenDRIVE objects using a dummy object
        for storage.
    '''
    dummy_obj = context.scene.objects.get('id_next')
    if dummy_obj is None:
        dummy_obj = bpy.data.objects.new('id_next',None)
        # Do not render
        dummy_obj.hide_viewport = True
        dummy_obj.hide_render = True
        dummy_obj['id_next'] = 0
        if not 'OpenDRIVE' in bpy.data.collections:
            collection = bpy.data.collections.new('OpenDRIVE')
            context.scene.collection.children.link(collection)
        collection = bpy.data.collections.get('OpenDRIVE')
        collection.objects.link(dummy_obj)
    id_next = dummy_obj['id_next']
    dummy_obj['id_next'] += 1
    return id_next