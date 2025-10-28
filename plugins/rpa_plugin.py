def register(app, register_plugin):
    def rpa_job():
        return "rpa placeholder"

    register_plugin("rpa", jobs=[rpa_job])


