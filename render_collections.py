import bpy
import os

bl_info = {
    "name": "Render Collections with Line Art",
    "author": "Your Name",
    "version": (2, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Tool Shelf > Render Collections",
    "description": "Renders selected collections with optional line art overlays.",
    "category": "Render",
}

class RENDER_OT_add_collections(bpy.types.Operator):
    """Add all collections to the render list"""
    bl_idname = "render.add_collections_to_list"
    bl_label = "Add All Collections to List"
    
    def execute(self, context):
        scene = context.scene
        scene.render_collections_list.clear()
        
        for collection in bpy.data.collections:
            if not collection.name.startswith("tech_") and not collection.name.startswith("c_") and collection.name != "lights_all":
                item = scene.render_collections_list.add()
                item.name = collection.name
                
        self.report({'INFO'}, f"Added {len(scene.render_collections_list)} collections to render list.")
        return {'FINISHED'}

class RENDER_OT_remove_collection(bpy.types.Operator):
    """Remove selected collection from the list"""
    bl_idname = "render.remove_collection_from_list"
    bl_label = "Remove Collection from List"
    
    def execute(self, context):
        scene = context.scene
        index = scene.render_collections_list_index
        
        if 0 <= index < len(scene.render_collections_list):
            scene.render_collections_list.remove(index)
            scene.render_collections_list_index = max(0, index - 1)
            self.report({'INFO'}, "Collection removed from the list.")
        else:
            self.report({'WARNING'}, "No valid collection selected.")
        
        return {'FINISHED'}

class RENDER_OT_collections_with_lineart(bpy.types.Operator):
    """Render selected collections with optional line art"""
    bl_idname = "render.render_collections_with_lineart"
    bl_label = "Render Collections"
    bl_options = {'REGISTER', 'UNDO'}
    
    output_path = "//renders/"
    render_lineart = False
    
    def execute(self, context):
        self.render_lineart = context.scene.render_collections_lineart
        
        # Convert to an absolute path
        output_path = bpy.path.abspath(context.scene.render_collections_output_path)
        
        # Ensure the directory exists
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        scene = context.scene
        view_layer = context.view_layer
        
        # Save original active states of collections
        original_states = {
            layer_collection: layer_collection.exclude
            for layer_collection in self.get_all_layer_collections(view_layer.layer_collection)
        }
        rendered_count = 0  # Counter for rendered collections
        
        # Get user-defined collections list
        collections_to_render = [item.name for item in scene.render_collections_list]
        total_collections = len(collections_to_render)
        
        # Progress bar setup
        progress = 0
        try:
            for collection_name in collections_to_render:
                progress += 1
                progress_message = f"Rendering {progress}/{total_collections}: {collection_name}"
                self.report({'INFO'}, progress_message)
                print(progress_message)
                bpy.context.window_manager.progress_update(progress / total_collections)
                
                # Deactivate all collections
                for layer_collection in view_layer.layer_collection.children:
                    layer_collection.exclude = True
                
                # Activate the target collection, lights_all, and its counterpart if it exists
                target_layer = self.get_layer_collection(view_layer.layer_collection, collection_name)
                lights_layer = self.get_layer_collection(view_layer.layer_collection, "lights_all")
                counterpart_layer = self.get_layer_collection(view_layer.layer_collection, f"c_{collection_name}")
                
                if target_layer:
                    target_layer.exclude = False
                    if lights_layer:
                        lights_layer.exclude = False
                    if counterpart_layer:
                        counterpart_layer.exclude = False
                    
                    # Get the active camera name (without the first part before "_")
                    active_camera = bpy.context.scene.camera
                    if active_camera:
                        camera_name = active_camera.name.split("_", 1)[-1]
                    else:
                        camera_name = "NoCamera"
                    
                    # Set the render filepath and render the collection
                    output_file = os.path.join(output_path, f"{collection_name}_{camera_name}.png")
                    scene.render.filepath = output_file  # Update the render file path
                    bpy.ops.render.render(write_still=True)  # Render the collection
                    rendered_count += 1
                    
                    # Render line art if enabled
                    if self.render_lineart:
                        self.render_line_art(view_layer, collection_name, output_path, camera_name)
                else:
                    self.report({'WARNING'}, f"Collection '{collection_name}' not found in the view layer.")
        
        finally:
            # Restore original active states of all collections
            for layer_collection, original_exclude in original_states.items():
                layer_collection.exclude = original_exclude

            # Finalize progress bar
            bpy.context.window_manager.progress_end()
            self.report({'INFO'}, f"Rendered {rendered_count} collections. Saved to: {output_path}")
            print(f"Rendered {rendered_count} collections. Images saved to: {output_path}")
        
        return {'FINISHED'}
    
    def render_line_art(self, view_layer, collection_name, output_path, camera_name):
        """Render the line art for a specific collection"""
        tech_ink_layer = self.get_layer_collection(view_layer.layer_collection, "tech_ink")
        target_layer = self.get_layer_collection(view_layer.layer_collection, collection_name)
        
        if not tech_ink_layer:
            self.report({'ERROR'}, "Line art collection 'tech_ink' not found!")
            return
        
        # Set target collection as holdout and activate tech_ink
        target_layer.holdout = True
        tech_ink_layer.exclude = False
        
        # Update the Line Art modifier
        line_art_object = bpy.data.objects.get("LineArt")
        if line_art_object and line_art_object.type == 'GPENCIL':
            line_art_modifier = line_art_object.grease_pencil_modifiers.get("Line Art")
            if line_art_modifier:
                line_art_modifier.source_collection = bpy.data.collections.get(collection_name)
        
        # Set the render filepath and render the line art
        output_file = os.path.join(output_path, f"{collection_name}_{camera_name}_lineart.png")
        bpy.context.scene.render.filepath = output_file  # Update the render file path
        bpy.ops.render.render(write_still=True)  # Render the line art
        
        # Restore settings
        target_layer.holdout = False
        tech_ink_layer.exclude = True

    def get_layer_collection(self, parent_layer_collection, collection_name):
        """Recursively search for the layer collection corresponding to a given collection name"""
        for layer_collection in parent_layer_collection.children:
            if layer_collection.collection.name == collection_name:
                return layer_collection
        return None

    def get_all_layer_collections(self, parent_layer_collection):
        """Recursively get all layer collections in the hierarchy"""
        all_layer_collections = []
        for layer_collection in parent_layer_collection.children:
            all_layer_collections.append(layer_collection)
            all_layer_collections.extend(self.get_all_layer_collections(layer_collection))
        return all_layer_collections


class RenderCollectionListItem(bpy.types.PropertyGroup):
    """Item for the collection render list"""
    name: bpy.props.StringProperty(name="Collection Name")

class RENDER_PT_collections_panel(bpy.types.Panel):
    """Panel to render collections separately"""
    bl_label = "Render Collections Separately"
    bl_idname = "RENDER_PT_collections_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Render Collections'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.operator(RENDER_OT_add_collections.bl_idname)
        
        layout.label(text="Collections to Render:")
        
        # Display the list with a remove button
        row = layout.row()
        row.template_list("UI_UL_list", "render_collections", scene, "render_collections_list", scene, "render_collections_list_index")
        
        col = row.column(align=True)
        col.operator("render.remove_collection_from_list", icon='X', text="")

        layout.operator(RENDER_OT_collections_with_lineart.bl_idname)
        layout.prop(scene, "render_collections_lineart")
        layout.prop(scene, "render_collections_output_path")

def register():
    bpy.utils.register_class(RENDER_OT_add_collections)
    bpy.utils.register_class(RENDER_OT_remove_collection)
    bpy.utils.register_class(RENDER_OT_collections_with_lineart)
    bpy.utils.register_class(RenderCollectionListItem)
    bpy.utils.register_class(RENDER_PT_collections_panel)
    bpy.types.Scene.render_collections_list = bpy.props.CollectionProperty(type=RenderCollectionListItem)
    bpy.types.Scene.render_collections_list_index = bpy.props.IntProperty()
    bpy.types.Scene.render_collections_output_path = bpy.props.StringProperty(
        name="Output Folder",
        description="Folder to save rendered images",
        subtype='DIR_PATH',
        default="//renders/"
    )
    bpy.types.Scene.render_collections_lineart = bpy.props.BoolProperty(
        name="Render Line Art",
        description="Also render line art for each collection",
        default=False
    )

def unregister():
    bpy.utils.unregister_class(RENDER_OT_add_collections)
    bpy.utils.unregister_class(RENDER_OT_remove_collection)
    bpy.utils.unregister_class(RENDER_OT_collections_with_lineart)
    bpy.utils.unregister_class(RenderCollectionListItem)
    bpy.utils.unregister_class(RENDER_PT_collections_panel)
    del bpy.types.Scene.render_collections_list
    del bpy.types.Scene.render_collections_list_index
    del bpy.types.Scene.render_collections_output_path

if __name__ == "__main__":
    register()
