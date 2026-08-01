import { useRef } from "react";
import { Paperclip, SendHorizontal } from "lucide-react";
import API from "../../src/services/api";
import { useChat } from "../../src/context/ChatContext";
import "./Input.css";

export default function InputBox() {

    const fileRef = useRef();

    const {
        setUploadedFile
    } = useChat();

    async function uploadFile(file) {

        if (!file) return;

        const formData = new FormData();

        formData.append("file", file);

        try {

            await API.post("/upload", formData);

            setUploadedFile(file.name);

            alert("✅ Document Uploaded Successfully");

        }

        catch (err) {

            console.error(err);

            alert("Upload Failed");

        }

    }

    return (

        <div className="input-container">

            <input

                type="file"

                hidden

                ref={fileRef}

                accept=".pdf"

                onChange={(e) => uploadFile(e.target.files[0])}

            />

            <button

                className="icon-btn"

                onClick={() => fileRef.current.click()}

            >

                <Paperclip size={20} />

            </button>

            <textarea

                placeholder="Ask anything about your documents..."

            />

            <button className="send-btn">

                <SendHorizontal size={20} />

            </button>

        </div>

    )

}