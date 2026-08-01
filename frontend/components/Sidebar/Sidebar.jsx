import { Plus, MessageSquare, Settings } from "lucide-react";
import "./Sidebar.css";

export default function Sidebar() {

    return (

        <div className="sidebar">

            <div>

                <h2 className="logo">
                    🤖 RAG Assistant
                </h2>

                <button className="new-chat-btn">

                    <Plus size={18} />

                    New Chat

                </button>

                <div className="chat-list">

                    <div className="chat-item active">

                        <MessageSquare size={16} />

                        AI Project

                    </div>

                    <div className="chat-item">

                        <MessageSquare size={16} />

                        Resume.pdf

                    </div>

                    <div className="chat-item">

                        <MessageSquare size={16} />

                        Research Paper

                    </div>

                </div>

            </div>

            <div className="sidebar-bottom">

                <div className="chat-item">

                    <Settings size={18} />

                    Settings

                </div>

            </div>

        </div>

    )

}