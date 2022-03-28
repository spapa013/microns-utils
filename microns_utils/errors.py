class MICrONSError(Exception):
    """
    Base class for errors specific to DataJoint internal operation.
    """
    def suggest(self, *args):
        """
        regenerate the exception with additional arguments
        :param args: addition arguments
        :return: a new exception of the same type with the additional arguments
        """
        return self.__class__(*(self.args + args))

class VersionError(MICrONSError):
    """
    Incorrect version.
    """