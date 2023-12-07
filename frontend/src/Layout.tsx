import { Outlet } from "react-router-dom";
import Header from "./components/Header";
import LoadingProvider from "./providers/LoadingProvider";

export default function Layout() {
    return (
        <>
            <LoadingProvider>
                <Header />
                <Outlet />
            </LoadingProvider>
        </>
    )
}