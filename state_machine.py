class State:
    protocol = None
    transition_function = None #They both could be just one function, maybe I will unify them later

    def __init__(self, protocol=None, transition_function=None):
        self.protocol = protocol
        self.transition_function = transition_function

states = {}

def add_state(name, protocol, transition_function):
    states[name] = State(protocol, transition_function)
    
def run_state(state_name, data):
    output = [] #Should be a list of pairs (type, content). For example ('text', 'Hello World') or ('image', image_data)
    state = states.get(state_name)

    if state.protocol:
        protocol_output = state.protocol(data) #Should I pass data here? We will see
        if protocol_output:
            output.extend(protocol_output)
    
    if state.transition_function:
        next_state_name, transition_output = state.transition_function(data)
        if transition_output:
            output.extend(transition_output)
    else:
        next_state_name = state_name
    
    return next_state_name, output

#Idea: in the state define the transition function on which the transition is made and return the target state
#then there is another thing that runs the transition protocol for that transition