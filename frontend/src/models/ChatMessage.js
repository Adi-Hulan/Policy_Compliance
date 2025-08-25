class ChatMessage {
  constructor(id, content, user, createdAt) {
    this.id = id;
    this.content = content;
    this.user = user; // { name: string }
    this.createdAt = createdAt;
  }

  // Example helper method to format date
  getFormattedDate() {
    return new Date(this.createdAt).toLocaleString();
  }
}

export default ChatMessage;