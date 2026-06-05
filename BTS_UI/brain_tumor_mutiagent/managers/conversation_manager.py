class ConversationManager:
    """
    Manage multi-agent conversation history.
    """

    def __init__(self, max_messages=10):

        self.history = []
        self.max_messages = max_messages

        print("[ConversationManager] Initialized.")

    # ===============================
    # Add message
    # ===============================

    def add_message(self, speaker, content):

        message = {
            "speaker": speaker,
            "content": content
        }

        self.history.append(message)

        print(f"[Conversation] {speaker} added message.")

        # 自动裁剪历史
        if len(self.history) > self.max_messages:

            self.history = self.history[-self.max_messages:]

    # ===============================
    # Get full history
    # ===============================

    def get_history(self):

        return self.history

    # ===============================
    # Get context string for prompt
    # ===============================

    def get_context(self):

        context = ""

        for msg in self.history:

            context += f"{msg['speaker']}: {msg['content']}\n"

        return context

    # ===============================
    # Reset conversation
    # ===============================

    def reset(self):

        self.history = []

        print("[Conversation] Reset.")