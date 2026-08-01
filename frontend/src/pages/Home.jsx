import Sidebar from "../../components/Sidebar/Sidebar";
import Topbar from "../../components/Topbar/Topbar";
import ChatWindow from "../../components/Chat/ChatWindow";
import InputBox from "../../components/Input/InputBox";

import "../styles/Home.css";

export default function Home() {
    return (
        <div className="app-layout">

            <Sidebar />

            <div className="main-section">

                <Topbar />

                <ChatWindow />

                <InputBox />

            </div>

        </div>
    );
}