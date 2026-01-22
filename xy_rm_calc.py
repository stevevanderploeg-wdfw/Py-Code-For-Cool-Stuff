# This code is working 6/16/25, had trouble overwriting an existing csv file so I just renamed it, the other one was locked by ESRI

import arcpy
import os
arcpy.env.overwriteOutput = True

# Input parameters
csv_file = "S:\\FP\\Reg5\\GIS\\iForm\\Empty_RMs - Copy.csv"
x_field = "lon"  # Replace with your actual X field name
y_field = "lat"   # Replace with your actual Y field name
output_gdb = "S:\\FP\\Reg5\\GIS\\iForm\\iForm_TWS_RMs.gdb"
output_feature_class = "XY_RM_Calc"
route_feature_class = "S:\\FP\\Reg5\\GIS\\Hydro\\R5_StreamLayer.gdb\\R5_StreamLayer"
route_id_field = "LLID"  # Replace with your route's ID field
search_radius = "1600 Meters"  # Adjust as needed
output_event_table = f"{output_gdb}\\XY_RM_Calc_loc"
filtered_table = f"{output_gdb}\\XY_RM_Calc_loc_select"
csv_output = "S:\\FP\\Reg5\\GIS\\iForm\\RM_Calc_Meas.csv"
far_out_layer = r"S:\FP\Reg5\GIS\iForm\iForm_TWS_RMs.gdb\XY_RM_Calc_Out250"

# try:
#arcpy.management.Delete(csv_output)
    
#     print("CSV file deleted successfully.")
# except Exception as e:
#     print(f"Error during cleanup: {e}")
    
try:
    # Step 1: Create XY Event Layer
    output_xy_layer = "XY_Event_Layer"
    arcpy.MakeXYEventLayer_management(
        table=csv_file,
        in_x_field=x_field,
        in_y_field=y_field,
        out_layer=output_xy_layer,
        spatial_reference=4326  # WGS 1984
    )
    print(f"Step 1: XY Event Layer '{output_xy_layer}' created successfully.")

    # Step 2: Convert to Feature Class in File Geodatabase
    arcpy.FeatureClassToFeatureClass_conversion(
        in_features=output_xy_layer,
        out_path=output_gdb,
        out_name=output_feature_class
    )
    print(f"Step 2: Feature Class '{output_feature_class}' created in Geodatabase '{output_gdb}'.")

    # Step 3: Locate Features Along Route
    arcpy.LocateFeaturesAlongRoutes_lr(
        in_features=f"{output_gdb}\\{output_feature_class}",
        in_routes=route_feature_class,
        route_id_field=route_id_field,
        radius_or_tolerance=search_radius,  # Specify search radius here
        route_locations = "ALL",
        out_table=output_event_table,
        out_event_properties="RouteID POINT MEAS"
    )
    print(f"Step 3: Features located along route and saved to table '{output_event_table}'.")

    # Step 4: Select Features Where 'x' = 'y'
    arcpy.MakeTableView_management(
        in_table=output_event_table,
        out_view="EventTable_View"
    )
    query = '"llid" = "RID"'  # Adjust field names as necessary
    arcpy.SelectLayerByAttribute_management(
        in_layer_or_view="EventTable_View",
        selection_type="NEW_SELECTION",
        where_clause=query
    )
    arcpy.TableToTable_conversion(
        in_rows="EventTable_View",
        out_path=output_gdb,
        out_name="XY_RM_Calc_loc_select"
    )
    print(f"Step 4: Filtered records saved to '{filtered_table}'.")

    # Step 5: Export Filtered Table to CSV
    # Use arcpy.TableToTable_conversion to export to a folder as CSV
    csv_folder = os.path.dirname(csv_output)
    csv_name = os.path.basename(csv_output)
    arcpy.TableToTable_conversion(filtered_table,"S:\\FP\\Reg5\\GIS\\iForm","RM_Calc_Meas.csv")
    print(f"Step 5: Filtered table exported to CSV at '{csv_output}'.")
    
except arcpy.ExecuteError as e:
    print(f"ArcPy Error: {e}")
except Exception as ex: 
    print(f"General Error: {ex}")

# Step 6: Join Field Meas and Distance fields to Feature Class
arcpy.management.JoinField(
in_data=output_feature_class,
in_field="pt_id",
join_table=filtered_table,
join_field="pt_id",
fields="MEAS;Distance",
fm_option="NOT_USE_FM",
field_mapping=None,
index_join_fields="NO_INDEXES"
)
print(f"Step 6: Join Field performed on '{output_feature_class}' on '{filtered_table}'.")
    # Step 7 Select and export features > 250ft distance

arcpy.conversion.ExportFeatures(
in_features = output_feature_class,
out_features = far_out_layer,
where_clause = "Distance > 250 Or Distance < -250",
sort_field = "Distance")
print("Step 7: Points > 250 ft exported to S:\FP\Reg5\GIS\iForm\iForm_TWS_RMs.gdb\XY_RM_Calc_Out250")


# Add the new field
arcpy.AddField_management(
in_table=far_out_layer,
field_name="Distance_Absolute",
field_type="Long"
)

# Calculate the field with correct comparison operator (==) and null handling
arcpy.CalculateField_management(
in_table=far_out_layer,
field="Distance_Absolute",
expression="0 if !Distance! in (None, 0) else abs(!Distance!)",  # Correct null check
expression_type="PYTHON3"
)

print("Field 'Distance_Absolute' added and calculated")

arcpy.env.overwriteOutput = False
