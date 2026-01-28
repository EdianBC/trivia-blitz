class State:
    entry_protocol = None
    core_protocol = None
    transition_protocol = None #main and transition could be just one function, maybe I will unify them later or maybe not

    def __init__(self, entry_protocol=None, core_protocol=None, transition_protocol=None):
        self.entry_protocol = entry_protocol
        self.core_protocol = core_protocol
        self.transition_protocol = transition_protocol

states = {}

async def add_state(name, entry_protocol=None, core_protocol=None, transition_protocol=None):
    states[name] = State(entry_protocol, core_protocol, transition_protocol)
    
async def run_state(state_name, data):
    state = states.get(state_name)

    if state.core_protocol:
        await state.core_protocol(data)
        
    if state.transition_protocol:
        next_state_name = await state.transition_protocol(data)
    else:
        next_state_name = state_name

    state = states.get(next_state_name)
    if state.entry_protocol:
        await state.entry_protocol(data)
    
    return next_state_name

