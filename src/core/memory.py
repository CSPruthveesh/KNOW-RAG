class ChatMemory:
    def __init__(self, max_messages=10):
        self.sessions = {}
        self.max_messages = max_messages
    
    def _get_session_messages(self, session_id: str)-> list:
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        return self.sessions[session_id]
        
    def add_user_message(self, message: str, session_id: str = "default_session"):
        messages = self._get_session_messages(session_id)
        messages.append(f"User: {message}")
        self._trim(session_id) 
        
    def add_ai_message(self, message: str, session_id: str = "default_session"):
        messages = self._get_session_messages(session_id)
        messages.append(f"Assistant: {message}")
        self._trim(session_id)
        
    def get_history(self, session_id: str = "default_session"):
        messages = self._get_session_messages(session_id)
        return "\n".join(messages)
    
    def clear(self, session_id: str = "default_session"):
        if session_id in self.sessions:
            self.sessions[session_id] = []
        
    def _trim(self, session_id: str):
        messages = self._get_session_messages(session_id)
        if(len(messages) > self.max_messages):
            self.sessions[session_id] = messages[-self.max_messages:]