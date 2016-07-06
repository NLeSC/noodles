# from .termapp import TermApp


class Display:
    def __init__(self):
        pass

    def report(self):
        pass

    def __call__(self, key, status, data, err_msg):
        getattr(self, status)(key, data, err_msg)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            if exc_type is KeyboardInterrupt:
                self.out << "\n" << ['fg', 255, 200, 50] \
                         << "User interrupt detected, abnormal exit.\n" \
                         << ['reset']
                return True

            if exc_type is SystemExit:
                return False

            print("Internal error encountered. Contact the developers: \n",
                  exc_type, exc_val)
            return False

        self.report()
