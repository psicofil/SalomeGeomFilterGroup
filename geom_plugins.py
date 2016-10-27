import salome_pluginsmanager

def filter_group(context):
    import geom_filter_group
    dialog = geom_filter_group.getDialog(context)
    dialog.show()

salome_pluginsmanager.AddFunction('Filter Group',
                                  'Create a similar group according criteria',
                                  filter_group)
