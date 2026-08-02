class ChatMemory:
    def __init__(self, max_messages=10):
        self.messages = []
        self.max_messages = max_messages
        
    def add_user_message(self, message):
        self.messages.append(f"User: {message}")
        self._trim()
        
    def add_ai_message(self, message):
        self.messages.append(f"Assisant: {message}")
        self._trim()
        
    def get_history(self):
        return "\n".join(self.messages)
    
    def clear(self):
        self.messages = []
        
    def _trim(self):
        if(len(self.messages) > self.max_messages):
            self.messages = self.messages[-self.max_messages:]