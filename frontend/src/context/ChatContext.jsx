import { createContext, useContext, useState } from "react";

const ChatContext = createContext();

export function ChatProvider({ children }) {

    const [messages, setMessages] = useState([]);

    const [loading, setLoading] = useState(false);

    const [model, setModel] = useState("llama-3.3-70b-versatile");

    const [webSearch, setWebSearch] = useState(false);

    const [uploadedFile, setUploadedFile] = useState(null);

    return (

        <ChatContext.Provider
            value={{
                messages,
                setMessages,
                loading,
                setLoading,
                model,
                setModel,
                webSearch,
                setWebSearch,
                uploadedFile,
                setUploadedFile,
            }}
        >
            {children}
        </ChatContext.Provider>

    );

}

export const useChat = () => useContext(ChatContext);