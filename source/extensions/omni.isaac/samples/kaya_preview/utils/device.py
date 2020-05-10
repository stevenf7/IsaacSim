import abc


class Device(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def _reset_state(self):
        """
        """
        raise NotImplementedError

    @abc.abstractmethod
    def start_control(self):
        """
        """
        raise NotImplementedError

    @abc.abstractmethod
    def bind_object(self):
        """
        """
        raise NotImplementedError

    # @abc.abstractmethod
    # def get_state(self):
    #     """
    #     """
    #     raise NotImplementedError

    @abc.abstractmethod
    def _on_event_fn(self):
        """
        """
        raise NotImplementedError
