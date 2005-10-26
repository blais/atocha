# Explicit inheritance search snippet.

            # Search the classes in order of inheritance.
            clsstack = [field.__class__]
            method = None
            while method is None:
                cls = clsstack.pop()
                mname = 'render%s' % cls.__name__
                method = getattr(renderer, mname, None)
                clsstack.extend(cls.__bases__)

            if method is None:
                raise AtochaInternalError(
                    "Error: renderer has no method for '%s'." %
                    field.__class__)
