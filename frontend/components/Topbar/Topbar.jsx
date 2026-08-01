import {
    Globe,
    Upload,
    Moon,
    User,
} from "lucide-react";

import "./Topbar.css";

export default function Topbar() {

    return (

        <div className="topbar">

            <div className="topbar-title">

                AI Document Assistant

            </div>

            <div className="topbar-actions">

                <button>

                    <Globe size={18} />

                </button>

                <select>

                    <option>Llama 3.3 70B</option>

                    <option>Llama 3.1 8B</option>

                    <option>Gemma 2</option>

                </select>

                <button>

                    <Upload size={18} />

                </button>

                <button>

                    <Moon size={18} />

                </button>

                <button>

                    <User size={18} />

                </button>

            </div>

        </div>

    );

}