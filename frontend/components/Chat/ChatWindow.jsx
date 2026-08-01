import { useChat } from "../../src/context/ChatContext";
import "./Chat.css";

export default function ChatWindow() {

    const { messages } = useChat();

    return (

        <div className="chat-window">

            <div className="messages">

                {messages.length === 0 ? (

                    <div className="empty-chat">

                        <h2>🤖 RAG Assistant</h2>

                        <p>

                            Upload a PDF to begin chatting with your AI assistant.

                        </p>

                    </div>

                ) : (

                    messages.map((msg, index) => (

                        <div
                            key={index}
                            className={`message ${msg.role}`}
                        >

                            <div className="bubble">

                                {msg.content}

                            </div>

                        </div>

                    ))

                )}

            </div>

        </div>

    );

}