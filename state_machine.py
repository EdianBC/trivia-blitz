class State:
    entry_protocol = None
    core_protocol = None
    transition_protocol = None #main and transition could be just one function, maybe I will unify them later or maybe not

    def __init__(self, entry_protocol=None, core_protocol=None, transition_protocol=None):
        self.entry_protocol = entry_protocol
        self.core_protocol = core_protocol
        self.transition_protocol = transition_protocol

states = {}

def add_state(name, entry_protocol=None, core_protocol=None, transition_protocol=None):
    states[name] = State(entry_protocol, core_protocol, transition_protocol)
    
def run_state(state_name, data):
    output = [] #Should be a list of pairs (type, content). For example ('text', 'Hello World') or ('image', image_data)
    state = states.get(state_name)

    if state.core_protocol:
        protocol_output = state.core_protocol(data)
        if protocol_output:
            output.extend(protocol_output)
    
    if state.transition_protocol:
        next_state_name, transition_output = state.transition_protocol(data)
        if transition_output:
            output.extend(transition_output)
    else:
        next_state_name = state_name

    state = states.get(next_state_name)
    if state.entry_protocol:
        entry_output = state.entry_protocol(data)
        if entry_output:
            output.extend(entry_output)
    
    return next_state_name, output
