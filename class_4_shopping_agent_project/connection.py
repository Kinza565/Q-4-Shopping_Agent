# connection.py

class RunConfig:
    def __init__(self, model, model_provider, tracing_disabled=True):
        self.model = model
        self.model_provider = model_provider
        self.tracing_disabled = tracing_disabled

# Create a dummy config if needed
config = RunConfig(model=None, model_provider=None, tracing_disabled=True)
