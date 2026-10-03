import { BrowserRouter, Route, Routes } from "react-router-dom";

function HomePage() {
    return <div>Nexora</div>;
}

export function AppRouter() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<HomePage />} />
            </Routes>
        </BrowserRouter>
    );
}