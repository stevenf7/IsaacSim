def _on_save_data_event(self, log_path):
    world = self.get_world()
    data_logger = world.get_data_logger()  # a DataLogger object is defined in the World by default
    data_logger.save(log_path=log_path)  # Saves the collected data to the json file specified.
    data_logger.reset()  # Resets the DataLogger internal state so that another set of data can be collected and saved separately.
    return
