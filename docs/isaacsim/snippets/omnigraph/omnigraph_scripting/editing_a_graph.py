import omni.graph.core as og

# get existing value from an attribute
existing_text = og.Controller.attribute("/action_graph/print.inputs:text").get()
print("Existing Text: ", existing_text)

# set new value
og.Controller.attribute("/action_graph/print.inputs:text").set("New Texts to print")
