import bpy

bl_info = {
    "name": "Batch Asset Manager",
    "description": "Simplify and speed up tagging and managing assets in the Blender Asset Library",
    "author": "Your Name",
    "version": (1, 3, 0),
    "blender": (3, 0, 0),
    "category": "Asset",
}

# Tag List Management
class ASSET_OT_AddTagToList(bpy.types.Operator):
    """Add a Tag to the List"""
    bl_idname = "asset.add_tag_to_list"
    bl_label = "Add Tag to List"

    def execute(self, context):
        new_tag = context.scene.tag_input.strip()
        
        if not new_tag:
            self.report({'WARNING'}, "Tag is empty.")
            return {'CANCELLED'}
        
        if context.scene.single_words:
            tags = new_tag.split(" ")
            for tag in tags:
                self.add_tag(context.scene.tag_list, tag)
        else:
            self.add_tag(context.scene.tag_list, new_tag)
        
        context.scene.tag_input = ""
        return {'FINISHED'}
    
    def add_tag(self, tag_list, new_tag):
        if new_tag and new_tag not in tag_list:
            item = tag_list.add()
            item.name = new_tag
            self.report({'INFO'}, f"Added tag '{new_tag}' to the list.")
        else:
            self.report({'WARNING'}, "Tag is empty or already in the list.")

class ASSET_OT_RemoveTagFromList(bpy.types.Operator):
    """Remove Selected Tag from the List"""
    bl_idname = "asset.remove_tag_from_list"
    bl_label = "Remove Tag from List"

    def execute(self, context):
        index = context.scene.tag_list_index

        if 0 <= index < len(context.scene.tag_list):
            context.scene.tag_list.remove(index)
            context.scene.tag_list_index = max(0, index-1)
            self.report({'INFO'}, "Removed tag from the list.")
        else:
            self.report({'WARNING'}, "No tag selected to remove.")
        return {'FINISHED'}
    
class ASSET_OT_AddDefaultTags(bpy.types.Operator):
    """Add set of defaults tags to the List"""
    bl_idname = "asset.add_default_tags"
    bl_label = "Add Default Tags"

    def execute(self, context):
        new_tags = {"Medieval", "fantasy", "Shakal"}
        
        for tag in new_tags:
            if tag and tag not in context.scene.tag_list:
                item = context.scene.tag_list.add()
                item.name = tag
                self.report({'INFO'}, f"Added tag '{tag}' to the list.")
            else:
                self.report({'WARNING'}, "Tag is empty or already in the list.")

        return {'FINISHED'}

# Operators for Applying Tags
class ASSET_OT_AddListedTags(bpy.types.Operator):
    """Add All Tags in the List to Selected Assets"""
    bl_idname = "asset.add_listed_tags"
    bl_label = "Add Listed Tags"

    def execute(self, context):
        tag_list = [item.name for item in context.scene.tag_list]
        assets = context.selected_assets
        if not assets:
            self.report({'WARNING'}, "No assets selected.")
            return {'CANCELLED'}

        for asset in assets:
            for tag in tag_list:
                asset.metadata.tags.new(tag, skip_if_exists=True)
        
        self.report({'INFO'}, f"Added {len(tag_list)} tag(s) to {len(assets)} asset(s).")
        return {'FINISHED'}

class ASSET_OT_RemoveListedTags(bpy.types.Operator):
    """Remove All Tags in the List from Selected Assets"""
    bl_idname = "asset.remove_listed_tags"
    bl_label = "Remove Listed Tags"

    def execute(self, context):
        tag_list = [item.name for item in context.scene.tag_list]
        assets = context.selected_assets
        if not assets:
            self.report({'WARNING'}, "No assets selected.")
            return {'CANCELLED'}

        for asset in assets:
            for tag in tag_list:
                tag_to_remove = asset.metadata.tags.get(tag)
                if tag_to_remove is not None:
                    asset.metadata.tags.remove(tag_to_remove)
        
        self.report({'INFO'}, f"Removed {len(tag_list)} tag(s) from {len(assets)} asset(s).")
        return {'FINISHED'}

# Single Tag Replacement
class ASSET_OT_ReplaceTag(bpy.types.Operator):
    """Replace Tag for Selected Assets"""
    bl_idname = "asset.replace_tag"
    bl_label = "Replace Tag"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        old_tag = context.scene.old_tag
        new_tag = context.scene.new_tag
        assets = context.selected_assets
        if not assets:
            self.report({'WARNING'}, "No assets selected.")
            return {'CANCELLED'}

        for asset in assets:
            tag_to_remove = asset.metadata.tags.get(old_tag)
            if tag_to_remove is not None:
                asset.metadata.tags.remove(tag_to_remove)
                asset.metadata.tags.new(new_tag, skip_if_exists=True)
        
        self.report({'INFO'}, f"Replaced tag '{old_tag}' with '{new_tag}' for {len(assets)} asset(s).")
        return {'FINISHED'}
    
# Operators for Asset Information
class ASSET_OT_EditMetadata(bpy.types.Operator):
    """Edit Metadata of Selected Assets"""
    bl_idname = "asset.edit_metadata"
    bl_label = "Edit Metadata"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        description_text = context.scene.asset_description
        license_text = context.scene.asset_license
        copyright_text = context.scene.asset_copyright
        author_text = context.scene.asset_author

        assets = context.selected_assets
        if not assets:
            self.report({'WARNING'}, "No assets selected.")
            return {'CANCELLED'}

        for asset in assets:
            if description_text:
                asset.metadata.description = description_text
            if license_text:
                asset.metadata.license = license_text
            if copyright_text:
                asset.metadata.copyright = copyright_text
            if author_text:
                asset.metadata.author = author_text
        
        self.report({'INFO'}, f"Updated metadata for {len(assets)} asset(s).")
        return {'FINISHED'}
    
class ASSET_OT_FillWithDefaultValues(bpy.types.Operator):
    """Fill All Metadata Fields with Default Values"""
    bl_idname = "asset.fill_default"
    bl_label = "Fill Default"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.asset_description = "A 3D model in a low-poly aesthetic, suitable for games, animations, and concept art."
        context.scene.asset_license = "Extended Commercial License (https://www.artstation.com/marketplace-product-eula)"
        context.scene.asset_copyright = "SHAKAL"
        context.scene.asset_author = "Hubert Ziarek"
        
        self.report({'INFO'}, "All fields are pre-filled with default values.")
        return {'FINISHED'}

# Panels
class ASSET_PT_TagManagerPanel(bpy.types.Panel):
    """UI Panel for Batch Tagging"""
    bl_idname = "ASSET_PT_TagManager"
    bl_label = "Batch Tag Manager"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_category = "Tagging"
    bl_context = "asset"

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        # Tag List
        col.label(text="Tag List:")
        row = col.row(align=True)
        row.prop(context.scene, "tag_input", text="")
        row.operator("asset.add_tag_to_list", text="", icon="ADD")
        row.operator("asset.remove_tag_from_list", text="", icon="REMOVE")
        row = col.row(align=True)
        row.prop(context.scene, "single_words")
        row.operator("asset.add_default_tags", text="Default Set")
        
        col.template_list("UI_UL_list", "tags_to_manage", context.scene, "tag_list", context.scene, "tag_list_index")

        # Apply Tag Buttons
        col.operator("asset.add_listed_tags", text="Add Listed Tags to Assets")
        col.operator("asset.remove_listed_tags", text="Remove Listed Tags from Assets")

        # Advanced
        col.separator()
        col.label(text="Advanced:")
        row = col.row(align=True)
        row.prop(context.scene, "old_tag", text="Old Tag")
        row.prop(context.scene, "new_tag", text="New Tag")
        col.operator("asset.replace_tag", text="Replace Tag")

class ASSET_PT_MetadataManagerPanel(bpy.types.Panel):
    """UI Panel for Editing Asset Metadata"""
    bl_idname = "ASSET_PT_MetadataManager"
    bl_label = "Batch Metadata Manager"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_category = "Tagging"
    bl_context = "asset"

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.label(text="Edit Asset Metadata:")
        col.prop(context.scene, "asset_description", text="Description")
        col.prop(context.scene, "asset_license", text="License")
        col.prop(context.scene, "asset_copyright", text="Copyright")
        col.prop(context.scene, "asset_author", text="Author")
        col.operator("asset.fill_default", text="Fill Default")
        col.operator("asset.edit_metadata", text="Apply Metadata")

# Registration
def register():
    bpy.types.Scene.tag_input = bpy.props.StringProperty(name="Tag Input")
    bpy.types.Scene.tag_list = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)
    bpy.types.Scene.tag_list_index = bpy.props.IntProperty(name="Tag List Index", default=0)
    bpy.types.Scene.old_tag = bpy.props.StringProperty(name="Old Tag")
    bpy.types.Scene.new_tag = bpy.props.StringProperty(name="New Tag")
    bpy.types.Scene.single_words = bpy.props.BoolProperty(
        name="Single Words",
        description="Divide given tag into single words",
        default=False
    )

    bpy.types.Scene.asset_description = bpy.props.StringProperty(name="Description")
    bpy.types.Scene.asset_license = bpy.props.StringProperty(name="License")
    bpy.types.Scene.asset_copyright = bpy.props.StringProperty(name="Copyright")
    bpy.types.Scene.asset_author = bpy.props.StringProperty(name="Author")

    bpy.utils.register_class(ASSET_OT_AddTagToList)
    bpy.utils.register_class(ASSET_OT_RemoveTagFromList)
    bpy.utils.register_class(ASSET_OT_AddDefaultTags)
    bpy.utils.register_class(ASSET_OT_AddListedTags)
    bpy.utils.register_class(ASSET_OT_RemoveListedTags)
    bpy.utils.register_class(ASSET_OT_ReplaceTag)
    bpy.utils.register_class(ASSET_PT_TagManagerPanel)

    bpy.utils.register_class(ASSET_OT_EditMetadata)
    bpy.utils.register_class(ASSET_OT_FillWithDefaultValues)
    bpy.utils.register_class(ASSET_PT_MetadataManagerPanel)

def unregister():
    del bpy.types.Scene.tag_input
    del bpy.types.Scene.tag_list
    del bpy.types.Scene.tag_list_index
    del bpy.types.Scene.old_tag
    del bpy.types.Scene.new_tag
    del bpy.types.Scene.single_words

    del bpy.types.Scene.asset_description
    del bpy.types.Scene.asset_license
    del bpy.types.Scene.asset_copyright
    del bpy.types.Scene.asset_author

    bpy.utils.unregister_class(ASSET_OT_AddTagToList)
    bpy.utils.unregister_class(ASSET_OT_RemoveTagFromList)
    bpy.utils.unregister_class(ASSET_OT_AddDefaultTags)
    bpy.utils.unregister_class(ASSET_OT_AddListedTags)
    bpy.utils.unregister_class(ASSET_OT_RemoveListedTags)
    bpy.utils.unregister_class(ASSET_OT_ReplaceTag)
    bpy.utils.unregister_class(ASSET_PT_TagManagerPanel)

    bpy.utils.unregister_class(ASSET_OT_EditMetadata)
    bpy.utils.unregister_class(ASSET_OT_FillWithDefaultValues)
    bpy.utils.unregister_class(ASSET_PT_MetadataManagerPanel)

if __name__ == "__main__":
    register()
